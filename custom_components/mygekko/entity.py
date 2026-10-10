"""Base classes of the MyGekko entities."""
from __future__ import annotations

import logging
from typing import Any

from homeassistant.core import callback
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .api import ReadOnlyEntity
from .const import CONF_USE_PAGES_AS_AREAS
from .const import DOMAIN
from .const import MANUFACTURER
from .const import NAME

_LOGGER: logging.Logger = logging.getLogger(__name__)


def controller_device_id(globals_network: dict[str, str] | None) -> str | None:
    """Return the id of the controller device, None if its name is unknown."""
    name = (globals_network or {}).get("gekkoname")
    return f"mygekko_controller_{name}" if name else None


def controller_device_info(
    globals_network: dict[str, str], configuration_url: str | None = None
) -> DeviceInfo:
    """Return the device of the MyGekko controller itself."""
    hardware = globals_network.get("hardware")
    if hardware == "legacy":
        hardware = None
    info = DeviceInfo(
        identifiers={(DOMAIN, controller_device_id(globals_network))},
        name=globals_network["gekkoname"],
        manufacturer=MANUFACTURER,
        model=hardware or "myGEKKO",
    )
    # only known values: an unset value would erase what was registered before
    if globals_network.get("version"):
        info["sw_version"] = globals_network["version"]
    if hardware:
        info["hw_version"] = hardware
    if configuration_url:
        info["configuration_url"] = configuration_url
    return info


class _MyGekkoBaseEntity(CoordinatorEntity):
    """Common behavior of all MyGekko entities."""

    _attr_has_entity_name = True

    @callback
    def _handle_coordinator_update(self) -> None:
        """Handle updated data; one failing entity must not stop the others."""
        try:
            self.async_write_ha_state()
        except Exception:  # noqa: BLE001
            _LOGGER.exception("State update failed for %s", self.entity_id)


class MyGekkoEntity(_MyGekkoBaseEntity):
    """Base class for the entities of a MyGekko device."""

    def __init__(
        self,
        coordinator,
        entity: ReadOnlyEntity,
        entity_prefix: str,
        entity_suffix: str = "",
    ):
        """Initialize a MyGekko entity."""
        super().__init__(coordinator)
        self._device = entity

        device_id = f"{entity_prefix}{entity.entity_id}"
        self._attr_unique_id = f"{device_id}{entity_suffix}"

        info = DeviceInfo(
            identifiers={(DOMAIN, device_id)},
            manufacturer=NAME,
            name=entity.name,
            model=getattr(entity, "model", None),
        )
        if coordinator.controller_registry_id:
            info["via_device_id"] = coordinator.controller_registry_id
        page = getattr(entity, "page", None)
        if page and coordinator.config_entry.options.get(CONF_USE_PAGES_AS_AREAS):
            info["suggested_area"] = page
        self._attr_device_info = info

        _LOGGER.debug("Added MyGekko entity id='%s'", self.unique_id)

    @property
    def extra_state_attributes(self) -> dict[str, Any] | None:
        """Report when the element is locked, set to manual operation or in alarm."""
        status = getattr(self._device, "element_status", None)
        if status in (None, "ok"):
            return None
        return {"element_status": status}


class MyGekkoControllerEntity(_MyGekkoBaseEntity):
    """Base class for the entities of the MyGekko controller."""

    def __init__(
        self, coordinator, entity: ReadOnlyEntity, globals_network, entity_prefix: str
    ):
        """Initialize a MyGekko controller entity."""
        super().__init__(coordinator)

        device_id = controller_device_id(globals_network)
        self._attr_unique_id = f"{device_id}{entity_prefix}{entity.entity_id}"
        self._attr_name = f"{entity.name}"
        self._attr_device_info = controller_device_info(globals_network)

        _LOGGER.debug(
            "Added MyGekko controller entity: id='%s' name='%s'",
            self.unique_id,
            self.name,
        )
