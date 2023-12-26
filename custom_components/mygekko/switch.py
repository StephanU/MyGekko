"""Switch platform for MyGekko."""
from homeassistant.components.switch import SwitchEntity
from homeassistant.core import callback
from PyMyGekko.resources.Loads import Load
from PyMyGekko.resources.Loads import LoadState

from .const import DOMAIN
from .entity import MyGekkoEntity


async def async_setup_entry(hass, entry, async_add_devices):
    """Set up switch platform."""
    coordinator = hass.data[DOMAIN][entry.entry_id]
    loads = coordinator.api.get_loads()
    if loads is not None:
        async_add_devices(MyGekkoSwitch(coordinator, load) for load in loads)


class MyGekkoSwitch(MyGekkoEntity, SwitchEntity):
    """mygekko Switch class."""

    _attr_name = None

    def __init__(self, coordinator, load: Load):
        """Initialize a MyGekko switch."""
        super().__init__(coordinator, load, "loads")
        self._load = load

    @callback
    def _handle_coordinator_update(self) -> None:
        """Handle updated data from the coordinator."""
        self.async_write_ha_state()

    @property
    def is_on(self) -> bool | None:
        """Check wether the swich is on."""
        return (
            self._load.state == LoadState.ON_PERMANENT
            or self._load.state == LoadState.ON_IMPULSE
        )

    async def async_turn_off(self, **kwargs):
        """Turn off the switch."""
        await self._load.set_state(LoadState.OFF)

    async def async_turn_on(self, **kwargs):
        """Turn on the switch."""
        await self._load.set_state(LoadState.ON_PERMANENT)
