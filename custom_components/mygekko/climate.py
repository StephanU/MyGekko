"""Climate platform for MyGekko."""
from homeassistant.components.climate import ATTR_TEMPERATURE
from homeassistant.components.climate import ClimateEntity
from homeassistant.components.climate import ClimateEntityFeature
from homeassistant.components.climate import HVACMode
from homeassistant.const import UnitOfTemperature
from homeassistant.core import callback
from PyMyGekko.resources.Thermostats import Thermostat
from PyMyGekko.resources.Thermostats import ThermostatFeature
from PyMyGekko.resources.Thermostats import ThermostatMode

from .const import CLIMATE
from .const import DOMAIN
from .entity import MyGekkoEntity


async def async_setup_entry(hass, entry, async_add_devices):
    """Setup cover platform."""
    coordinator = hass.data[DOMAIN][entry.entry_id]
    thermostats = coordinator.api.get_thermostats()
    if thermostats is not None:
        async_add_devices(
            MyGekkoClimate(coordinator, thermostat) for thermostat in thermostats
        )


class MyGekkoClimate(MyGekkoEntity, ClimateEntity):
    """mygekko Climate class."""

    _attr_temperature_unit = UnitOfTemperature.CELSIUS
    _attr_preset_modes = ["Comfort", "Reduced", "Manual", "Standby"]

    def __init__(self, coordinator, thermostat: Thermostat):
        super().__init__(coordinator, thermostat, CLIMATE)
        print("Thermo", thermostat.id, thermostat.name)
        self._thermostat = thermostat
        supported_features = self._thermostat.supported_features
        self._attr_supported_features = 0
        self._attr_hvac_modes = [HVACMode.OFF, HVACMode.AUTO]

        if ThermostatFeature.TARGET_TEMPERATURE in supported_features:
            self._attr_supported_features |= ClimateEntityFeature.TARGET_TEMPERATURE

    @callback
    def _handle_coordinator_update(self) -> None:
        """Handle updated data from the coordinator."""
        self.async_write_ha_state()

    @property
    def current_temperature(self) -> float | None:
        """Return the current temperature."""
        return self._thermostat.current_temperature

    @property
    def target_temperature(self) -> float | None:
        """Return the temperature we try to reach."""
        return self._thermostat.target_temperature

    async def async_set_temperature(self, **kwargs) -> None:
        """Set new target temperature."""
        print(self._thermostat.id, kwargs[ATTR_TEMPERATURE])
        await self._thermostat.set_target_temperature(float(kwargs[ATTR_TEMPERATURE]))

    @property
    def hvac_mode(self) -> HVACMode | str | None:
        """Return hvac operation ie. heat, cool mode."""
        if self._thermostat.mode == ThermostatMode.Off:
            return HVACMode.OFF
        else:
            return HVACMode.AUTO

    async def async_set_hvac_mode(self, hvac_mode: HVACMode) -> None:
        """Set new target hvac mode."""
        if hvac_mode == HVACMode.OFF:
            await self._thermostat.set_mode(ThermostatMode.Off)
        else:
            await self._thermostat.set_mode(ThermostatMode.Comfort)
