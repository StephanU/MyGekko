"""Number platform for MyGekko."""
from homeassistant.components.number import NumberDeviceClass
from homeassistant.components.number import NumberEntity
from homeassistant.components.number import NumberMode
from homeassistant.const import UnitOfPower
from PyMyGekko.resources.EMobils import EMobil

from .const import DOMAIN
from .entity import MyGekkoEntity

# Fallback upper bound for the charge power setpoint when the charging station does
# not report its maximum charging power. The myGekko command range is 1..100 kW.
DEFAULT_MAX_CHARGING_POWER = 100.0


async def async_setup_entry(hass, entry, async_add_devices):
    """Set up number platform."""
    coordinator = hass.data[DOMAIN][entry.entry_id]

    async_add_devices(
        MyGekkoEMobilChargingPowerNumber(coordinator, emobil)
        for emobil in coordinator.api.get_emobils()
    )


class MyGekkoEMobilChargingPowerNumber(MyGekkoEntity, NumberEntity):
    """mygekko charging station charge power setpoint class."""

    _attr_translation_key = "mygekko_emobil_charging_power_setpoint"
    _attr_device_class = NumberDeviceClass.POWER
    _attr_native_unit_of_measurement = UnitOfPower.KILO_WATT
    _attr_mode = NumberMode.BOX
    _attr_native_min_value = 1.0
    _attr_native_step = 0.1
    _attr_icon = "mdi:ev-station"

    def __init__(self, coordinator, emobil: EMobil):
        """Initialize a MyGekko charging station charge power setpoint."""
        super().__init__(coordinator, emobil, "emobils", "charging_power_setpoint")
        self._emobil = emobil

    @property
    def native_max_value(self) -> float:
        """Return the maximum charge power the station accepts."""
        maximum = self._emobil.maximum_charging_power
        return maximum if maximum else DEFAULT_MAX_CHARGING_POWER

    @property
    def native_value(self) -> float | None:
        """Return the current charge power setpoint."""
        return self._get_optimistic("setpoint", self._emobil.charging_power_setpoint)

    async def async_set_native_value(self, value: float) -> None:
        """Set a new charge power setpoint."""
        await self._emobil.set_charging_power_setpoint(value)
        self._set_optimistic("setpoint", value, self._emobil.charging_power_setpoint)
        await self.coordinator.async_request_refresh()
