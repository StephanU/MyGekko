"""Cover platform for MyGekko."""

from homeassistant.components.cover import CoverEntity, CoverDeviceClass

from .const import DOMAIN
from .entity import MyGekkoEntity


async def async_setup_entry(hass, entry, async_add_devices):
    """Setup cover platform."""
    coordinator = hass.data[DOMAIN][entry.entry_id]
    async_add_devices([MyGekkoCover(coordinator, entry)])


class MyGekkoCover(MyGekkoEntity, CoverEntity):
    """mygekko Cover class."""

    def __init__(self, coordinator, config_entry):
        super().__init__(coordinator, config_entry)
        self.device_class = CoverDeviceClass.BLIND
