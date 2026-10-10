"""MyGekko EnergyCosts implementation"""
from __future__ import annotations

import logging
import re

from ..data_provider import DataProviderBase
from ..data_provider import EntityValueAccessor
from . import Entity

_LOGGER: logging.Logger = logging.getLogger(__name__)


class EnergyCost(Entity):
    """Class for MyGekko EnergyCost"""

    def __init__(
        self, entity_id: str, name: str, value_accessor: EnergyCostValueAccessor
    ) -> None:
        super().__init__(entity_id, name, "/energycosts/")
        self._value_accessor = value_accessor

    @property
    def sensor_data(self) -> dict[str, any] | None:
        """Returns the sensor data"""
        return self._value_accessor.get_data(self)


class EnergyCostValueAccessor(EntityValueAccessor):
    """EnergyCost value accessor"""

    def __init__(self, data_provider: DataProviderBase):
        super().__init__()
        self._data_provider = data_provider
        self._data_provider.subscribe(self)

    def _transform_value(self, description: str, value: str) -> any:
        m = re.match(r"([^\[]*)\[([^\]]*)\]", description)

        if m is None:
            return None

        typed_value = None

        unit = None if len(m.groups()) == 1 else m.group(2)

        if unit is not None and unit != "Unit" and unit != "DateTime":
            typed_value = float(value)
        else:
            typed_value = value

        return {"name": m.group(1), "unit": unit, "value": typed_value}

    def _decode_values(self, value: str, hardware: str) -> any:
        value_descriptions = []

        if hardware == "legacy":
            value_descriptions = [
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
                "other",
            ]
        else:
            value_descriptions = [
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
                "energyYear[kWh]",
                "energyPeriod[kWh]",
                "energyPeriodFrom[DateTime]",
                "counterDirection",
                "other",
            ]
        values = []
        for index, value_parts in enumerate(value.split(";")):
            if index < len(value_descriptions):
                values.append(
                    self._transform_value(value_descriptions[index], value_parts)
                )
            else:
                _LOGGER.info(
                    "OutOfBounds access for value %s. Not all energy_costs value are read currently.",
                    value,
                )

        return values

    def update_status(self, status, hardware):
        if status is not None and "energycosts" in status:
            energy_costs = status["energycosts"]

            _LOGGER.debug("EnergyCosts update_status %s", energy_costs)

            for key in energy_costs:
                if key.startswith("item"):
                    if key not in self._data:
                        self._data[key] = {}

                    if (
                        "sumstate" in energy_costs[key]
                        and "value" in energy_costs[key]["sumstate"]
                    ):
                        self._data[key]["values"] = self._decode_values(
                            energy_costs[key]["sumstate"]["value"], hardware
                        )

    def update_resources(self, resources):
        if resources is not None and "energycosts" in resources:
            energy_costs = resources["energycosts"]

            _LOGGER.debug("EnergyCosts update_resources %s", energy_costs)

            for key in energy_costs:
                if key.startswith("item"):
                    if key not in self._data:
                        self._data[key] = {}
                    self._data[key]["name"] = energy_costs[key]["name"]

    @property
    def energy_costs(self):
        """Returns the energyCosts read from MyGekko"""
        result: list[EnergyCost] = []
        for key, data in self._data.items():
            if "name" not in data:
                continue
            result.append(EnergyCost(key, data["name"], self))

        return result

    def get_data(self, energy_meter: EnergyCost) -> dict[str, any] | None:
        """Returns the data of the given energy meter"""
        if energy_meter and energy_meter.entity_id:
            if (
                energy_meter.entity_id in self._data
                and self._data[energy_meter.entity_id]
            ):
                return self._data[energy_meter.entity_id]
        return None
