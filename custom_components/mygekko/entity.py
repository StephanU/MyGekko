"""MyGekkoEntity class"""
from homeassistant.helpers.update_coordinator import CoordinatorEntity
from PyMyGekko.resources import Entity

from .const import ATTRIBUTION
from .const import DOMAIN
from .const import NAME
from .const import VERSION


class MyGekkoEntity(CoordinatorEntity):
    _attr_has_entity_name = True
    def __init__(self, coordinator, entity: Entity):
        super().__init__(coordinator)
        self.entity = entity

    @property
    def unique_id(self):
        """Return a unique ID to use for this entity."""
        return self.entity.id

    @property
    def device_info(self):
        return {
            "identifiers": {(DOMAIN, self.unique_id)},
            "name": self.entity.name,
            "model": VERSION,
            "manufacturer": NAME,
        }

    @property
    def device_state_attributes(self):
        """Return the state attributes."""
        return {
            "attribution": ATTRIBUTION,
            "id": "cover_" + str(self.entity.id),
            "integration": DOMAIN,
        }
