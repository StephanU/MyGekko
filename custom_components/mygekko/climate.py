"""Climate platform for MyGekko."""
import logging
from math import ceil

from homeassistant.components.climate import ATTR_TEMPERATURE
from homeassistant.components.climate import ClimateEntity
from homeassistant.components.climate import ClimateEntityFeature
from homeassistant.components.climate import HVACAction
from homeassistant.components.climate import HVACMode
from homeassistant.const import UnitOfTemperature
from .api import RoomTemp
from .api import RoomTempsFeature
from .api import OnOffState
from .api import RoomTempsMode

from .entity import MyGekkoEntity


_LOGGER: logging.Logger = logging.getLogger(__name__)

PARALLEL_UPDATES = 1


async def async_setup_entry(hass, entry, async_add_devices):
    """Set up cover platform."""
    coordinator = entry.runtime_data

    async_add_devices(
        MyGekkoRoomTempClimate(coordinator, room_temp)
        for room_temp in coordinator.api.get_room_temps()
    )


# Home Assistant 2026.11 renames the temperature API to native_*, the old names then log
# warnings. Both variants are offered, the one matching the installed version is used.
_NATIVE_TEMPERATURE = hasattr(ClimateEntity, "native_temperature_unit")

# readable preset ids of the working modes of MyGekko
PRESET_BY_MODE = {
    RoomTempsMode.OFF: "off",
    RoomTempsMode.COMFORT: "comfort",
    RoomTempsMode.REDUCED: "reduced",
    RoomTempsMode.MANUAL: "manual",
    RoomTempsMode.STANDBY: "standby",
}
MODE_BY_PRESET = {preset: mode for mode, preset in PRESET_BY_MODE.items()}


class MyGekkoRoomTempClimate(MyGekkoEntity, ClimateEntity):
    """mygekko Climate class."""

    if _NATIVE_TEMPERATURE:
        _attr_native_temperature_unit = UnitOfTemperature.CELSIUS
    else:
        _attr_temperature_unit = UnitOfTemperature.CELSIUS

    def __init__(self, coordinator, room_temp: RoomTemp):
        """Initialize the MyGekko climate entity."""
        super().__init__(coordinator, room_temp, "room_temps")
        self._room_temp = room_temp
        self._attr_translation_key = "mygekko_roomtemp"
        supported_features = self._room_temp.supported_features
        self._attr_supported_features = (
            ClimateEntityFeature.PRESET_MODE
            | ClimateEntityFeature.TURN_ON
            | ClimateEntityFeature.TURN_OFF
        )
        self._attr_hvac_modes = [HVACMode.OFF, HVACMode.AUTO]
        self._attr_preset_modes = list(MODE_BY_PRESET)

        if RoomTempsFeature.TARGET_TEMPERATURE in supported_features:
            self._attr_supported_features |= ClimateEntityFeature.TARGET_TEMPERATURE

    if _NATIVE_TEMPERATURE:

        @property
        def native_current_temperature(self) -> float | None:
            """Return the current temperature."""
            return self._room_temp.current_temperature

        @property
        def native_target_temperature(self) -> float | None:
            """Return the temperature we try to reach."""
            return self._room_temp.target_temperature

    else:

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
        await self.coordinator.async_write(self._room_temp.set_target_temperature, float(kwargs[ATTR_TEMPERATURE]))

    @property
    def preset_mode(self) -> str | None:
        """Return preset mode."""
        _LOGGER.debug(
            "The mode of %s is %s", self._room_temp.name, self._room_temp.working_mode
        )

        return PRESET_BY_MODE.get(self._room_temp.working_mode)

    async def async_set_preset_mode(self, preset_mode) -> None:
        """Set new preset mode."""
        await self.coordinator.async_write(
            self._room_temp.set_working_mode, MODE_BY_PRESET[preset_mode]
        )

    @property
    def hvac_mode(self) -> HVACMode | None:
        """Return off when the room controller is off, else it follows its own program."""
        mode = self._room_temp.working_mode
        if mode is None:
            return None
        return HVACMode.OFF if mode == RoomTempsMode.OFF else HVACMode.AUTO

    async def async_set_hvac_mode(self, hvac_mode: HVACMode) -> None:
        """Switch the room controller off, or back on (comfort) if it is off."""
        if hvac_mode == HVACMode.OFF:
            await self.coordinator.async_write(
                self._room_temp.set_working_mode, RoomTempsMode.OFF
            )
        elif self._room_temp.working_mode == RoomTempsMode.OFF:
            await self.coordinator.async_write(
                self._room_temp.set_working_mode, RoomTempsMode.COMFORT
            )

    @property
    def hvac_action(self) -> HVACAction | None:
        """Return what the room controller does: heating, cooling or idle."""
        if self._room_temp.working_mode == RoomTempsMode.OFF:
            return HVACAction.OFF
        valve = self._room_temp.valve_opening
        if valve is None:
            return None
        if valve <= 0:
            return HVACAction.IDLE
        if self._room_temp.cooling_mode_state == OnOffState.ON:
            return HVACAction.COOLING
        return HVACAction.HEATING

    @property
    def current_humidity(self) -> int | None:
        """Return the current humidity."""
        return (
            ceil(self._room_temp.humidity)
            if self._room_temp.humidity is not None
            else None
        )
