"""Scene platform for MyGekko."""
from typing import Any

from custom_components.mygekko.entity import MyGekkoControllerEntity
from homeassistant.components.scene import Scene
from .pymygekko.resources.Actions import Action
from .pymygekko.resources.Actions import ActionState



async def async_setup_entry(hass, entry, async_add_devices):
    """Set up scene platform."""
    coordinator = entry.runtime_data
    actions = coordinator.api.get_actions()
    globals_network = coordinator.api.get_globals_network()
    if actions is not None and globals_network:
        async_add_devices(
            MyGekkoScene(coordinator, action, globals_network) for action in actions
        )


class MyGekkoScene(MyGekkoControllerEntity, Scene):
    """mygekko Scene class."""

    def __init__(self, coordinator, action: Action, globals_network):
        """Initialize a MyGekko scene."""
        super().__init__(coordinator, action, globals_network, "actions")
        self._action = action

    async def async_activate(self, **kwargs: Any) -> None:
        """Activate the scene."""
        await self.coordinator.async_write(self._action.set_state, ActionState.ON)
