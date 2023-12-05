"""Light platform for MyGekko."""
import logging

from homeassistant.components.light import ATTR_BRIGHTNESS
from homeassistant.components.light import ATTR_RGB_COLOR
from homeassistant.components.light import ColorMode
from homeassistant.components.light import LightEntity
from homeassistant.core import callback
from PyMyGekko.resources.Lights import Light
from PyMyGekko.resources.Lights import LightFeature
from PyMyGekko.resources.Lights import LightState

from .const import DOMAIN
from .entity import MyGekkoEntity


_LOGGER: logging.Logger = logging.getLogger(__name__)


async def async_setup_entry(hass, entry, async_add_devices):
    """Setup light platform."""
    coordinator = hass.data[DOMAIN][entry.entry_id]
    lights: list[Light] = coordinator.api.get_lights()
    if lights is not None:
        async_add_devices(
            MyGekkoLight(coordinator, light)
            for light in filter(
                lambda light: light.entity_id.startswith("item"), lights
            )
        )


class MyGekkoLight(MyGekkoEntity, LightEntity):
    """mygekko Light class."""

    def __init__(self, coordinator, light: Light):
        super().__init__(coordinator, light, "lights")
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

    @property
    def is_on(self) -> bool | None:
        _LOGGER.debug(
            "The light state of %s is %d", self._light.name, self._light.state
        )
        return self._light.state == LightState.ON

    async def async_turn_off(self, **kwargs):
        _LOGGER.debug("Switch off light %s", self._light.name)
        await self._light.set_state(LightState.OFF)

    async def async_turn_on(self, **kwargs):
        _LOGGER.debug("Switch on light %s", self._light.name)
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
