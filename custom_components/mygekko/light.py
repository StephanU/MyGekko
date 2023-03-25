"""Light platform for MyGekko."""
from homeassistant.core import callback
from homeassistant.components.light import LightEntity, ColorMode
from PyMyGekko.resources.Lights import Light, LightState, LightFeature

from .const import DOMAIN, LIGHT
from .entity import MyGekkoEntity


async def async_setup_entry(hass, entry, async_add_devices):
    """Setup light platform."""
    coordinator = hass.data[DOMAIN][entry.entry_id]
    lights = coordinator.api.get_lights()
    print(lights)
    if lights is not None:
        async_add_devices(MyGekkoLight(coordinator, light) for light in lights)


class MyGekkoLight(MyGekkoEntity, LightEntity):
    """mygekko Light class."""


    def __init__(self, coordinator, light: Light):
        super().__init__(coordinator, light, LIGHT)
        self._light = light
        self._attr_color_mode = ColorMode.ONOFF

        supported_features = self._light.supported_features
        self._attr_supported_color_modes = set()

        if LightFeature.ON_OFF in supported_features:
            self._attr_supported_color_modes.add(ColorMode.ONOFF)

    @callback
    def _handle_coordinator_update(self) -> None:
        """Handle updated data from the coordinator."""
        self.async_write_ha_state()

    def is_on(self) -> bool | None:
        return self._light.state == LightState.ON

    async def async_turn_off(self, **kwargs):
        await self._light.set_state(LightState.OFF)

    async def async_turn_on(self, **kwargs):
        await self._light.set_state(LightState.ON)