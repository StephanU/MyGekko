"""Button platform for MyGekko."""
from homeassistant.components.button import ButtonEntity
from .api import AccessDoor
from .api import AccessDoorCommand
from .api import AccessDoorFeature
from .api import Light
from .api import LightState

from .entity import MyGekkoEntity


PARALLEL_UPDATES = 1


async def async_setup_entry(hass, entry, async_add_devices):
    """Set up button platform."""
    coordinator = entry.runtime_data
    async_add_devices(
        MyGekkoAccessDoorOpenButton(coordinator, door)
        for door in coordinator.api.get_access_doors()
        if AccessDoorFeature.OPEN in door.supported_features
    )
    lights = coordinator.api.get_lights()
    if lights is not None:
        async_add_devices(
            MyGekkoLightGroupOnButton(coordinator, light)
            for light in filter(
                lambda light: light.entity_id.startswith("group"), lights
            )
        )
        async_add_devices(
            MyGekkoLightGroupOffButton(coordinator, light)
            for light in filter(
                lambda light: light.entity_id.startswith("group"), lights
            )
        )


class MyGekkoLightGroupOnButton(MyGekkoEntity, ButtonEntity):
    """mygekko Light class."""

    def __init__(self, coordinator, light: Light):
        """Initialize the Light Group On button."""
        super().__init__(coordinator, light, "lights", "On")
        self._light = light
        self._attr_icon = "mdi:lightbulb-on"
        self._attr_translation_key = "mygekko_light_group_on"

    async def async_press(self) -> None:
        """Press the button."""
        await self.coordinator.async_write(self._light.set_state, LightState.ON)


class MyGekkoLightGroupOffButton(MyGekkoEntity, ButtonEntity):
    """mygekko Light class."""

    def __init__(self, coordinator, light: Light):
        """Initialize the Light Group Off button."""
        super().__init__(coordinator, light, "lights", "Off")
        self._light = light
        self._attr_icon = "mdi:lightbulb-off"
        self._attr_translation_key = "mygekko_light_group_off"

    async def async_press(self) -> None:
        """Press the button."""
        await self.coordinator.async_write(self._light.set_state, LightState.OFF)


class MyGekkoAccessDoorOpenButton(MyGekkoEntity, ButtonEntity):
    """Opens a door, a gate or a barrier.

    Disabled by default as this opens the building: it has to be enabled on purpose and
    should not be exposed to voice assistants.
    """

    _attr_entity_registry_enabled_default = False
    _attr_translation_key = "mygekko_access_door_open"
    _attr_icon = "mdi:door-open"

    def __init__(self, coordinator, door: AccessDoor):
        """Initialize the open button."""
        super().__init__(coordinator, door, "access_door", "_open_command")
        self._door = door

    async def async_press(self) -> None:
        """Press the button."""
        await self.coordinator.async_write(self._door.set_state, AccessDoorCommand.OPEN)
