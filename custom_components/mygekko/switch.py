"""Switch platform for MyGekko."""
from homeassistant.components.switch import SwitchEntity
from homeassistant.core import callback
from PyMyGekko.resources.Loads import Load
from PyMyGekko.resources.Loads import LoadState

from .const import DOMAIN
from .const import SWITCH
from .entity import MyGekkoEntity


async def async_setup_entry(hass, entry, async_add_devices):
    """Setup switch platform."""
    coordinator = hass.data[DOMAIN][entry.entry_id]
    loads = coordinator.api.get_loads()
    if loads is not None:
        async_add_devices(MyGekkoSwitch(coordinator, load) for load in loads)


class MyGekkoSwitch(MyGekkoEntity, SwitchEntity):
    """mygekko Switch class."""

    def __init__(self, coordinator, load: Load):
        super().__init__(coordinator, load, SWITCH)
        self._load = load

    @callback
    def _handle_coordinator_update(self) -> None:
        """Handle updated data from the coordinator."""
        self.async_write_ha_state()

    @property
    def is_on(self) -> bool | None:
        return (
            self._load.state == LoadState.ON_PERMANENT
            or self._load.state == LoadState.ON_IMPULSE
        )

    async def async_turn_off(self, **kwargs):
        await self._load.set_state(LoadState.OFF)

    async def async_turn_on(self, **kwargs):
        await self._load.set_state(LoadState.ON_PERMANENT)
