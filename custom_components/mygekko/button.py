"""Button platform for MyGekko."""
from homeassistant.components.button import ButtonEntity
from PyMyGekko.resources.Lights import Light
from PyMyGekko.resources.Lights import LightState

from .const import DOMAIN
from .entity import MyGekkoEntity


async def async_setup_entry(hass, entry, async_add_devices):
    """Set up button platform."""
    coordinator = hass.data[DOMAIN][entry.entry_id]
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
        await self._light.set_state(LightState.ON)


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
        await self._light.set_state(LightState.OFF)
