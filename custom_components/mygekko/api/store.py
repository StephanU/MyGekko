"""Holds the device data read from MyGekko and parses the API documents."""
from __future__ import annotations

import logging
import re
from typing import Any

from .schema import ENERGY_COSTS
from .schema import SPECS
from .schema import ResourceSpec

_LOGGER: logging.Logger = logging.getLogger(__name__)

LEGACY_HARDWARE = "legacy"

# Layout of the energy cost sumstate: "name[unit]" per value.
_ENERGY_COST_COMMON = (
    "actPower[kW]",
    "energyToday[kWh]",
    "energyMonth[kWh]",
    "energySum[kWh]",
    "powerMax[kW]",
    "unitEnergy[Unit]",
    "unitPower[Unit]",
    "energyToday6[kWh]",
    "energyToday12[kWh]",
    "energyToday18[kWh]",
    "energyToday24[kWh]",
    "energyYesterd6[kWh]",
    "energyYesterd12[kWh]",
    "energyYesterd18[kWh]",
    "energyYesterd24[kWh]",
    "elementInfo",
)
_ENERGY_COST_LEGACY = _ENERGY_COST_COMMON + ("other",)
_ENERGY_COST_CURRENT = _ENERGY_COST_COMMON + (
    "energyYear[kWh]",
    "energyPeriod[kWh]",
    "energyPeriodFrom[DateTime]",
    "counterDirection",
    "other",
)
_ENERGY_COST_PATTERN = re.compile(r"([^\[]*)\[([^\]]*)\]")


def hardware_of(status: dict | None) -> str:
    """Return the hardware generation reported in the status document.

    Only newer hardware (Slide 2, Nova) reports its hardware version.
    """
    network = ((status or {}).get("globals") or {}).get("network") or {}
    hardware = network.get("hardware")
    if isinstance(hardware, dict) and hardware.get("value"):
        return hardware["value"]
    return LEGACY_HARDWARE


def _split(sumstate: Any) -> list[str] | None:
    """Return the values of a sumstate entry, None if it has none."""
    if isinstance(sumstate, dict) and isinstance(sumstate.get("value"), str):
        return sumstate["value"].split(";")
    return None


def _decode_energy_cost(
    value: list[str], hardware: str
) -> list[dict[str, Any] | None]:
    """Decode the sumstate of an energy meter into named, typed values."""
    layout = _ENERGY_COST_LEGACY if hardware == LEGACY_HARDWARE else _ENERGY_COST_CURRENT
    result = []
    for description, raw in zip(layout, value, strict=False):
        match = _ENERGY_COST_PATTERN.match(description)
        if match is None:
            # values without a unit are not exposed, but keep their position
            result.append(None)
            continue
        name, unit = match.group(1), match.group(2)
        try:
            typed = raw if unit in ("Unit", "DateTime") else float(raw)
        except ValueError:
            # keep the position, sensors address values by index
            _LOGGER.debug("Energy cost value %s of %s is not numeric", raw, name)
            typed = None
        result.append({"name": name, "unit": unit, "value": typed})
    return result


class ResourceStore:
    """Stores names, features and values of all MyGekko devices."""

    def __init__(self) -> None:
        """Initialize an empty store."""
        self._devices: dict[str, dict[str, dict[str, Any]]] = {
            spec.kind: {} for spec in SPECS
        }
        self._meteo: dict[str, Any] = {}
        self._globals_network: dict[str, str] = {}

    # --- reading -----------------------------------------------------------------

    def devices(self, spec: ResourceSpec) -> dict[str, dict[str, Any]]:
        """Return the devices of a resource type that have a name."""
        return {
            key: data
            for key, data in self._devices[spec.kind].items()
            if "name" in data
        }

    def value(self, spec: ResourceSpec, key: str, field: str) -> str | None:
        """Return a raw value; empty values count as missing."""
        return self._devices[spec.kind].get(key, {}).get(field) or None

    @property
    def meteo(self) -> dict[str, Any]:
        """Return the weather station values."""
        return self._meteo

    @property
    def globals_network(self) -> dict[str, str]:
        """Return the network information of the controller."""
        return self._globals_network

    def unnamed_keys(self, status: dict) -> set[tuple[str, str]]:
        """Return the devices of the status document that have no name yet."""
        missing = set()
        for spec in SPECS:
            section = status.get(spec.kind)
            if not isinstance(section, dict):
                continue
            for key in section:
                if spec.accepts(key) and "name" not in self._devices[spec.kind].get(
                    key, {}
                ):
                    missing.add((spec.kind, key))
        return missing

    # --- updating ----------------------------------------------------------------

    def update_resources(self, resources: dict | None) -> None:
        """Read names and static attributes from the resources document."""
        for spec in SPECS:
            section = (resources or {}).get(spec.kind)
            if not isinstance(section, dict):
                continue
            for key, item in section.items():
                if not spec.accepts(key) or not isinstance(item, dict):
                    continue
                if "name" not in item:
                    continue
                data = self._devices[spec.kind].setdefault(key, {})
                data["name"] = item["name"]
                for attr in spec.resource_attrs:
                    data[attr] = item.get(attr)

    def update_status(self, status: dict | None) -> None:
        """Read the current values from the status document."""
        if not status:
            return
        hardware = hardware_of(status)
        self._update_globals(status)
        for spec in SPECS:
            try:
                section = status.get(spec.kind)
                if isinstance(section, dict):
                    self._update_spec(spec, section, hardware)
            except Exception:  # noqa: BLE001
                # one broken resource type must not stop the others
                _LOGGER.exception("Reading the status of %s failed", spec.kind)

    def _update_spec(self, spec: ResourceSpec, section: dict, hardware: str) -> None:
        for key, item in section.items():
            if not spec.accepts(key):
                continue
            values = _split((item or {}).get("sumstate"))
            data = self._devices[spec.kind].setdefault(key, {})
            if values is None:
                continue
            if spec is ENERGY_COSTS:
                data["values"] = _decode_energy_cost(values, hardware)
                continue
            fields = (
                spec.group_fields if key.startswith("group") else spec.fields_for(hardware)
            )
            data.update(zip(fields, values, strict=False))

    def _update_globals(self, status: dict) -> None:
        globals_ = status.get("globals") or {}
        network = globals_.get("network") or {}
        self._globals_network = {
            key: item["value"]
            for key, item in network.items()
            if isinstance(item, dict) and "value" in item
        }
        meteo = globals_.get("meteo") or {}
        for key, item in meteo.items():
            if isinstance(item, dict):
                self._meteo[key] = item.get("value", self._meteo.get(key, {}))
