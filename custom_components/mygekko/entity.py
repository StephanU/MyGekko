"""MyGekkoEntity class"""
from homeassistant.helpers.update_coordinator import CoordinatorEntity
from PyMyGekko.resources import Entity

from .const import ATTRIBUTION
from .const import DOMAIN
from .const import NAME
from .const import VERSION


class MyGekkoEntity(CoordinatorEntity):
    _attr_name = None
    _attr_has_entity_name = True

    def __init__(self, coordinator, entity: Entity, platform: str):
        super().__init__(coordinator)
        self.entity = entity
        self._attr_unique_id = platform + "_" + self.entity.id
        print(self.unique_id)

    @property
    def device_info(self):
        return {
            "identifiers": {(DOMAIN, self.unique_id)},
            "name": self.entity.name,
            "model": VERSION,
            "manufacturer": NAME,
        }