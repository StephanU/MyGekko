"""Cover platform for MyGekko."""

from homeassistant.core import callback
from homeassistant.components.cover import CoverEntity, CoverDeviceClass
from PyMyGekko.resources.Blinds import Blind

from .const import DOMAIN
from .entity import MyGekkoEntity


async def async_setup_entry(hass, entry, async_add_devices):
    """Setup cover platform."""
    coordinator = hass.data[DOMAIN][entry.entry_id]
    blinds = coordinator.api.get_blinds()
    if blinds is not None:
        async_add_devices(MyGekkoCover(coordinator, blind) for blind in blinds)


class MyGekkoCover(MyGekkoEntity, CoverEntity):
    """mygekko Cover class."""

    def __init__(self, coordinator, blind: Blind):
        super().__init__(coordinator, blind)
        self._blind = blind
        self._attr_device_class = CoverDeviceClass.BLIND
        self._attr_is_closed = self._blind.position == 100.00
        self._attr_current_cover_position = self._blind.position

    @callback
    def _handle_coordinator_update(self) -> None:
        """Handle updated data from the coordinator."""
        self._attr_is_closed = self._blind.position == 100.00
        self._attr_current_cover_position = self._blind.position
        self.async_write_ha_state()
