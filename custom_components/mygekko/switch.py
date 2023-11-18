"""Switch platform for MyGekko."""
from homeassistant.components.switch import SwitchEntity
from homeassistant.core import callback
from PyMyGekko.resources.Switches import Switch
from PyMyGekko.resources.Switches import SwitchState

from .const import DOMAIN
from .const import SWITCH
from .entity import MyGekkoEntity


async def async_setup_entry(hass, entry, async_add_devices):
    """Setup switch platform."""
    coordinator = hass.data[DOMAIN][entry.entry_id]
    switches = coordinator.api.get_switches()
    if switches is not None:
        async_add_devices(MyGekkoSwitch(coordinator, switch) for switch in switches)


class MyGekkoSwitch(MyGekkoEntity, SwitchEntity):
    """mygekko Switch class."""

    def __init__(self, coordinator, switch: Switch):
        super().__init__(coordinator, switch, SWITCH)
        self._switch = switch

    @callback
    def _handle_coordinator_update(self) -> None:
        """Handle updated data from the coordinator."""
        self.async_write_ha_state()

    def is_on(self) -> bool | None:
        return self._switch.state == SwitchState.PERMANENT_ON

    async def async_turn_off(self, **kwargs):
        await self._switch.set_state(SwitchState.OFF)

    async def async_turn_on(self, **kwargs):
        await self._switch.set_state(SwitchState.PERMANENT_ON)
