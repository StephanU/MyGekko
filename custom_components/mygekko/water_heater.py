"""Light platform for MyGekko."""
import logging
from typing import Any

from homeassistant.components.water_heater import ATTR_TEMPERATURE
from homeassistant.components.water_heater import WaterHeaterEntity
from homeassistant.components.water_heater import WaterHeaterEntityFeature
from homeassistant.const import STATE_OFF
from homeassistant.const import STATE_ON
from homeassistant.const import UnitOfTemperature
from homeassistant.core import callback
from PyMyGekko.resources.HotWaterSystems import HotWaterSystem
from PyMyGekko.resources.HotWaterSystems import HotWaterSystemFeature
from PyMyGekko.resources.HotWaterSystems import HotWaterSystemState

from .const import DOMAIN
from .entity import MyGekkoEntity


_LOGGER: logging.Logger = logging.getLogger(__name__)


async def async_setup_entry(hass, entry, async_add_devices):
    """Set up light platform."""
    coordinator = hass.data[DOMAIN][entry.entry_id]
    hotwater_systems = coordinator.api.get_hot_water_systems()
    if hotwater_systems is not None:
        async_add_devices(
            MyGekkoWaterHeater(coordinator, hotwater_system)
            for hotwater_system in hotwater_systems
        )


class MyGekkoWaterHeater(MyGekkoEntity, WaterHeaterEntity):
    """mygekko water heater class."""

    _attr_name = None
    _attr_temperature_unit = UnitOfTemperature.CELSIUS

    def __init__(self, coordinator, hotwater_system: HotWaterSystem):
        """Initialize a MyGekko water heater."""
        super().__init__(coordinator, hotwater_system, "hotwater_systems")
        self._hotwater_system = hotwater_system

        supported_features = self._hotwater_system.supported_features
        self._attr_supported_features = 0

        if HotWaterSystemFeature.ON_OFF in supported_features:
            self._attr_supported_features |= WaterHeaterEntityFeature.ON_OFF

        if HotWaterSystemFeature.TARGET_TEMPERATURE in supported_features:
            self._attr_supported_features |= WaterHeaterEntityFeature.TARGET_TEMPERATURE

    @callback
    def _handle_coordinator_update(self) -> None:
        """Handle updated data from the coordinator."""
        self.async_write_ha_state()

    async def async_turn_off(self, **kwargs):
        """Turn off the water heater."""
        _LOGGER.debug("Switch off water heater %s", self._hotwater_system.name)
        await self._hotwater_system.set_state(HotWaterSystemState.OFF)

    async def async_turn_on(self, **kwargs):
        """Turn on the water heater."""
        _LOGGER.debug("Switch on water heater %s", self._hotwater_system.name)
        await self._hotwater_system.set_state(HotWaterSystemState.ON)

    @property
    def target_temperature(self) -> float | None:
        """Return the target temperature of the water heater."""
        _LOGGER.debug(
            "The water heaters %s current target temperature is %s",
            self._hotwater_system.name,
            self._hotwater_system.target_temperature,
        )

        return self._hotwater_system.target_temperature

    async def async_set_temperature(self, **kwargs: Any) -> None:
        """Set new target temperature."""
        await self._hotwater_system.set_target_temperature(
            float(kwargs[ATTR_TEMPERATURE])
        )

    @property
    def current_temperature(self) -> float | None:
        """Return the top temperature of the water heater."""
        _LOGGER.debug(
            "The water heaters %s current top temperature is %s",
            self._hotwater_system.name,
            self._hotwater_system.current_temperature_top,
        )

        return self._hotwater_system.current_temperature_top

    @property
    def current_operation(self) -> str | None:
        """Return current operation ie. eco, electric, performance, ..."""
        if self._hotwater_system.state == HotWaterSystemState.OFF:
            return STATE_OFF
        else:
            return STATE_ON
