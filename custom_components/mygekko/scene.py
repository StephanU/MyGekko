"""Scene platform for MyGekko."""
from typing import Any

from homeassistant.components.scene import Scene
from homeassistant.core import callback
from PyMyGekko.resources.Actions import Action
from PyMyGekko.resources.Actions import ActionState

from .const import DOMAIN
from .const import SCENE
from .entity import MyGekkoEntity


async def async_setup_entry(hass, entry, async_add_devices):
    """Setup scene platform."""
    coordinator = hass.data[DOMAIN][entry.entry_id]
    actions = coordinator.api.get_actions()
    if actions is not None:
        async_add_devices(MyGekkoScene(coordinator, action) for action in actions)


class MyGekkoScene(MyGekkoEntity, Scene):
    """mygekko Scene class."""

    def __init__(self, coordinator, action: Action):
        super().__init__(coordinator, action, SCENE)
        self._action = action

    @callback
    def _handle_coordinator_update(self) -> None:
        """Handle updated data from the coordinator."""
        self.async_write_ha_state()

    async def activate(self, **kwargs: Any) -> None:
        await self._action.set_state(ActionState.ON)
