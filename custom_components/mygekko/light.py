"""Light platform for MyGekko."""
from homeassistant.core import callback
from homeassistant.components.light import LightEntity, ColorMode, ATTR_RGB_COLOR, ATTR_BRIGHTNESS
from PyMyGekko.resources.Lights import Light, LightState, LightFeature

from .const import DOMAIN, LIGHT
from .entity import MyGekkoEntity


async def async_setup_entry(hass, entry, async_add_devices):
    """Setup light platform."""
    coordinator = hass.data[DOMAIN][entry.entry_id]
    lights = coordinator.api.get_lights()
    if lights is not None:
        async_add_devices(MyGekkoLight(coordinator, light) for light in lights)


class MyGekkoLight(MyGekkoEntity, LightEntity):
    """mygekko Light class."""


    def __init__(self, coordinator, light: Light):
        super().__init__(coordinator, light, LIGHT)
        self._light = light

        supported_features = self._light.supported_features
        self._attr_supported_color_modes = set()

        if LightFeature.RGB_COLOR in supported_features:
            self._attr_supported_color_modes.add(ColorMode.RGB)
            self._attr_color_mode = ColorMode.RGB
        elif LightFeature.DIMMABLE in supported_features:
            self._attr_supported_color_modes.add(ColorMode.BRIGHTNESS)
            self._attr_color_mode = ColorMode.BRIGHTNESS
        elif LightFeature.ON_OFF in supported_features:
            self._attr_supported_color_modes.add(ColorMode.ONOFF)
            self._attr_color_mode = ColorMode.ONOFF

    @callback
    def _handle_coordinator_update(self) -> None:
        """Handle updated data from the coordinator."""
        self.async_write_ha_state()

    def is_on(self) -> bool | None:
        return self._light.state == LightState.ON

    async def async_turn_off(self, **kwargs):
        await self._light.set_state(LightState.OFF)

    async def async_turn_on(self, **kwargs):
        if ATTR_RGB_COLOR in kwargs and kwargs[ATTR_RGB_COLOR]:
            await self._light.set_rgb_color(kwargs[ATTR_RGB_COLOR])
        elif ATTR_BRIGHTNESS in kwargs and kwargs[ATTR_BRIGHTNESS]:
            await self._light.set_brightness(round(kwargs[ATTR_BRIGHTNESS] / 255 * 100))
        else:
            await self._light.set_state(LightState.ON)

    @property
    def brightness(self) -> int | None:
        """Return the brightness of this light between 0..255."""
        if self._light.brightness is None:
            return None

        return round(255 * self._light.brightness / 100)

    @property
    def rgb_color(self) -> tuple[int, int, int] | None:
        """Return the rgb color value [int, int, int]."""
        return self._light.rgb_color