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
from PyMyGekko.resources.WaterHeaters import WaterHeater
from PyMyGekko.resources.WaterHeaters import WaterHeaterFeature
from PyMyGekko.resources.WaterHeaters import WaterHeaterState

from .const import DOMAIN
from .const import WATER_HEATER
from .entity import MyGekkoEntity


_LOGGER: logging.Logger = logging.getLogger(__name__)


async def async_setup_entry(hass, entry, async_add_devices):
    """Setup light platform."""
    coordinator = hass.data[DOMAIN][entry.entry_id]
    waterHeaters = coordinator.api.get_water_heaters()
    if waterHeaters is not None:
        async_add_devices(
            MyGekkoWaterHeater(coordinator, waterHeater) for waterHeater in waterHeaters
        )


class MyGekkoWaterHeater(MyGekkoEntity, WaterHeaterEntity):
    """mygekko water heater class."""

    _attr_temperature_unit = UnitOfTemperature.CELSIUS

    def __init__(self, coordinator, water_heater: WaterHeater):
        super().__init__(coordinator, water_heater, WATER_HEATER)
        self._water_heater = water_heater

        supported_features = self._water_heater.supported_features
        self._attr_supported_features = 0

        if WaterHeaterFeature.ON_OFF in supported_features:
            self._attr_supported_features |= WaterHeaterEntityFeature.ON_OFF

        if WaterHeaterFeature.TARGET_TEMPERATURE in supported_features:
            self._attr_supported_features |= WaterHeaterEntityFeature.TARGET_TEMPERATURE

    @callback
    def _handle_coordinator_update(self) -> None:
        """Handle updated data from the coordinator."""
        self.async_write_ha_state()

    async def async_turn_off(self, **kwargs):
        _LOGGER.debug("Switch off water heater %s", self._water_heater.name)
        await self._water_heater.set_state(WaterHeaterState.OFF)

    async def async_turn_on(self, **kwargs):
        _LOGGER.debug("Switch on water heater %s", self._water_heater.name)
        await self._water_heater.set_state(WaterHeaterState.ON)

    @property
    def target_temperature(self) -> float | None:
        """Return the target temperature of the water heater."""
        _LOGGER.debug(
            "The water heaters %s current target temperature is %s",
            self._water_heater.name,
            self._water_heater.target_temperature,
        )

        return self._water_heater.target_temperature

    async def async_set_temperature(self, **kwargs: Any) -> None:
        """Set new target temperature."""
        await self._water_heater.set_target_temperature(float(kwargs[ATTR_TEMPERATURE]))

    @property
    def current_temperature(self) -> float | None:
        """Return the top temperature of the water heater."""
        _LOGGER.debug(
            "The water heaters %s current top temperature is %s",
            self._water_heater.name,
            self._water_heater.current_temperature_top,
        )

        return self._water_heater.current_temperature_top

    @property
    def current_operation(self) -> str | None:
        """Return current operation ie. eco, electric, performance, ..."""
        if self._water_heater.state == WaterHeaterState.OFF:
            return STATE_OFF
        else:
            return STATE_ON
