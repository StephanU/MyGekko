"""Scene platform for MyGekko."""
from typing import Any

from homeassistant.components.scene import Scene
from homeassistant.core import callback
from homeassistant.helpers.entity import DeviceInfo
from PyMyGekko.resources.Actions import Action
from PyMyGekko.resources.Actions import ActionState

from .const import DOMAIN
from .const import MANUFACTURER


async def async_setup_entry(hass, entry, async_add_devices):
    """Setup scene platform."""
    coordinator = hass.data[DOMAIN][entry.entry_id]
    actions = coordinator.api.get_actions()
    globals_network = coordinator.api.get_globals_network()
    if actions is not None:
        async_add_devices(MyGekkoScene(action, globals_network) for action in actions)


class MyGekkoScene(Scene):
    """mygekko Scene class."""

    def __init__(self, action: Action, globals_network):
        self._attr_unique_id = "actions_" + action.id
        self._attr_name = action.name
        self._action = action
        self._attr_device_info = DeviceInfo(
            identifiers={
                (DOMAIN, "mygekko_controller_" + globals_network["gekkoname"])
            },
            name=globals_network["gekkoname"],
            manufacturer=MANUFACTURER,
            sw_version=globals_network["version"],
            hw_version=globals_network["hardware"],
            model=globals_network["hardware"],
        )

    @callback
    def _handle_coordinator_update(self) -> None:
        """Handle updated data from the coordinator."""
        self.async_write_ha_state()

    async def activate(self, **kwargs: Any) -> None:
        await self._action.set_state(ActionState.ON)
