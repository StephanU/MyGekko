"""Scene platform for MyGekko."""
from typing import Any

from custom_components.mygekko.entity import MyGekkoControllerEntity
from homeassistant.components.scene import Scene
from homeassistant.core import callback
from PyMyGekko.resources.Actions import Action
from PyMyGekko.resources.Actions import ActionState

from .const import DOMAIN


async def async_setup_entry(hass, entry, async_add_devices):
    """Setup scene platform."""
    coordinator = hass.data[DOMAIN][entry.entry_id]
    actions = coordinator.api.get_actions()
    globals_network = coordinator.api.get_globals_network()
    if actions is not None:
        async_add_devices(
            MyGekkoScene(coordinator, action, globals_network) for action in actions
        )


class MyGekkoScene(MyGekkoControllerEntity, Scene):
    """mygekko Scene class."""

    def __init__(self, coordinator, action: Action, globals_network):
        super().__init__(coordinator, action, globals_network, "actions")
        self._action = action

    @callback
    def _handle_coordinator_update(self) -> None:
        """Handle updated data from the coordinator."""
        self.async_write_ha_state()

    async def async_activate(self, **kwargs: Any) -> None:
        await self._action.set_state(ActionState.ON)
