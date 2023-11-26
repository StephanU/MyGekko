"""MyGekkoEntity class"""
import logging

from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.update_coordinator import CoordinatorEntity
from PyMyGekko.resources import Entity

from .const import DOMAIN
from .const import MANUFACTURER
from .const import NAME

_LOGGER: logging.Logger = logging.getLogger(__name__)


class MyGekkoEntity(CoordinatorEntity):
    _attr_name = None
    _attr_has_entity_name = True

    def __init__(
        self, coordinator, entity: Entity, entity_prefix: str, entity_suffix: str = ""
    ):
        super().__init__(coordinator)

        device_id = f"{entity_prefix}{entity.id}"
        device_name = entity.name

        self._attr_unique_id = f"{device_id}{entity_suffix}"
        self._attr_name = entity_suffix if entity_suffix != "" else None

        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, device_id)},
            manufacturer=NAME,
            name=device_name,
        )

        _LOGGER.debug(
            "Added MyGekko entity id='%s' name='%s'", self.unique_id, self.name
        )


class MyGekkoControllerEntity(CoordinatorEntity):
    _attr_name = None
    _attr_has_entity_name = True

    def __init__(
        self, coordinator, entity: Entity, globals_network, entity_prefix: str
    ):
        super().__init__(coordinator)

        device_id = f"mygekko_controller_{globals_network['gekkoname']}"
        device_name = globals_network["gekkoname"]

        self._attr_unique_id = f"{device_id}{entity_prefix}{entity.id}"
        self._attr_name = f"{entity.name}"

        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, device_id)},
            name=device_name,
            manufacturer=MANUFACTURER,
            sw_version=globals_network["version"],
            hw_version=globals_network["hardware"],
            model=globals_network["hardware"],
        )

        _LOGGER.debug(
            "Added MyGekko controller entity: id='%s' name='%s'",
            self.unique_id,
            self.name,
        )
