"""MyGekkoEntity class."""
import logging

from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.update_coordinator import CoordinatorEntity
from PyMyGekko.resources import ReadOnlyEntity

from .const import DOMAIN
from .const import MANUFACTURER
from .const import NAME

_LOGGER: logging.Logger = logging.getLogger(__name__)


class MyGekkoEntity(CoordinatorEntity):
    """Base Class for MyGekko entities."""

    _attr_has_entity_name = True

    def __init__(
        self, coordinator, entity: ReadOnlyEntity, entity_prefix: str, entity_suffix: str = ""
    ):
        """Initialize a MyGekko entity."""
        super().__init__(coordinator)

        device_id = f"{entity_prefix}{entity.entity_id}"
        device_name = entity.name

        self._attr_unique_id = f"{device_id}{entity_suffix}"

        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, device_id)},
            manufacturer=NAME,
            name=device_name,
        )

        _LOGGER.debug("Added MyGekko entity id='%s'", self.unique_id)


class MyGekkoControllerEntity(CoordinatorEntity):
    """Base Class for MyGekko controller entities."""

    _attr_has_entity_name = True

    def __init__(
        self, coordinator, entity: ReadOnlyEntity, globals_network, entity_prefix: str
    ):
        """Initialize a MyGekko controller entity."""
        super().__init__(coordinator)

        device_id = f"mygekko_controller_{globals_network['gekkoname']}"
        device_name = globals_network["gekkoname"]

        self._attr_unique_id = f"{device_id}{entity_prefix}{entity.entity_id}"
        self._attr_name = f"{entity.name}"

        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, device_id)},
            name=device_name,
            manufacturer=MANUFACTURER,
            sw_version=globals_network.get("version", "unknown"),
            hw_version=globals_network.get("hardware", "unknown"),
            model=globals_network.get("hardware", "unknown"),
        )

        _LOGGER.debug(
            "Added MyGekko controller entity: id='%s' name='%s'",
            self.unique_id,
            self.name,
        )
