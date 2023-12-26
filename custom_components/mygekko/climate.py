"""Climate platform for MyGekko."""
import logging
from math import ceil

from homeassistant.components.climate import ATTR_TEMPERATURE
from homeassistant.components.climate import ClimateEntity
from homeassistant.components.climate import ClimateEntityFeature
from homeassistant.components.climate import HVACMode
from homeassistant.const import UnitOfTemperature
from homeassistant.core import callback
from PyMyGekko.resources.RoomTemps import RoomTemp
from PyMyGekko.resources.RoomTemps import RoomTempsFeature
from PyMyGekko.resources.RoomTemps import RoomTempsMode

from .const import DOMAIN
from .entity import MyGekkoEntity


_LOGGER: logging.Logger = logging.getLogger(__name__)


async def async_setup_entry(hass, entry, async_add_devices):
    """Set up cover platform."""
    coordinator = hass.data[DOMAIN][entry.entry_id]

    async_add_devices(
        MyGekkoRoomTempClimate(coordinator, room_temp)
        for room_temp in coordinator.api.get_room_temps()
    )


class MyGekkoRoomTempClimate(MyGekkoEntity, ClimateEntity):
    """mygekko Climate class."""

    _attr_temperature_unit = UnitOfTemperature.CELSIUS

    def __init__(self, coordinator, room_temp: RoomTemp):
        """Initialize the MyGekko climate entity."""
        super().__init__(coordinator, room_temp, "room_temps")
        self._room_temp = room_temp
        self._attr_translation_key = "mygekko_roomtemp"
        supported_features = self._room_temp.supported_features
        self._attr_supported_features = ClimateEntityFeature.PRESET_MODE
        self._attr_hvac_mode = HVACMode.AUTO
        self._attr_hvac_modes = [HVACMode.AUTO]
        self._attr_preset_modes = [
            str(RoomTempsMode.OFF),
            str(RoomTempsMode.COMFORT),
            str(RoomTempsMode.REDUCED),
            str(RoomTempsMode.MANUAL),
            str(RoomTempsMode.STANDBY),
        ]

        if RoomTempsFeature.TARGET_TEMPERATURE in supported_features:
            self._attr_supported_features |= ClimateEntityFeature.TARGET_TEMPERATURE

    @callback
    def _handle_coordinator_update(self) -> None:
        """Handle updated data from the coordinator."""
        self.async_write_ha_state()

    @property
    def current_temperature(self) -> float | None:
        """Return the current temperature."""
        return self._room_temp.current_temperature

    @property
    def target_temperature(self) -> float | None:
        """Return the temperature we try to reach."""
        return self._room_temp.target_temperature

    async def async_set_temperature(self, **kwargs) -> None:
        """Set new target temperature."""
        await self._room_temp.set_target_temperature(float(kwargs[ATTR_TEMPERATURE]))

    @property
    def preset_mode(self) -> str | None:
        """Return preset mode."""
        _LOGGER.debug(
            "The mode of %s is %s", self._room_temp.name, self._room_temp.working_mode
        )

        return (
            str(self._room_temp.working_mode)
            if self._room_temp.working_mode is not None
            else None
        )

    async def async_set_preset_mode(self, preset_mode) -> None:
        """Set new preset mode."""

        await self._room_temp.set_working_mode(preset_mode)

    @property
    def current_humidity(self) -> int | None:
        """Return the current humidity."""
        return (
            ceil(self._room_temp.humidity)
            if self._room_temp.humidity is not None
            else None
        )
