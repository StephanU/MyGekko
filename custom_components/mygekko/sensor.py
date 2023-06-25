"""Sensor platform for MyGekko."""
from homeassistant.components.sensor import SensorDeviceClass
from homeassistant.components.sensor import SensorEntity
from homeassistant.components.sensor import SensorEntityDescription
from homeassistant.components.sensor import SensorStateClass
from PyMyGekko.resources.EnergyMeters import EnergyMeter

from .const import DEFAULT_NAME
from .const import DOMAIN
from .const import ICON
from .const import SENSOR
from .entity import MyGekkoEntity

SENSOR_TYPES: tuple[SensorEntityDescription, ...] = (
    SensorEntityDescription(
        key="actPower",
        name="Actual power",
        state_class=SensorStateClass.MEASUREMENT,
        device_class=SensorDeviceClass.POWER,
    ),
    SensorEntityDescription(
        key="energySum",
        name="Energy sum",
        state_class=SensorStateClass.TOTAL_INCREASING,
        device_class=SensorDeviceClass.ENERGY,
    ),
)


async def async_setup_entry(hass, entry, async_add_devices):
    """Setup sensor platform."""
    coordinator = hass.data[DOMAIN][entry.entry_id]
    energy_meters: list[EnergyMeter] = coordinator.api.get_energy_meters()
    if energy_meters is not None:
        for energy_meter in energy_meters:
            if energy_meter.sensor_data and "values" in energy_meter.sensor_data:
                for sensor in energy_meter.sensor_data["values"]:
                    async_add_devices(MyGekkoSensor(coordinator, sensor))


class MyGekkoSensor(MyGekkoEntity, SensorEntity):
    """mygekko Sensor class."""

    def __init__(self, coordinator, energy_meter: EnergyMeter):
        super().__init__(coordinator, energy_meter, SENSOR)
        self._energy_meter = energy_meter
        # supported_features = self._blind.supported_features
        self._attr_supported_features = 0

    @property
    def name(self):
        """Return the name of the sensor."""
        return f"{DEFAULT_NAME}_{SENSOR}"

    @property
    def state(self):
        """Return the state of the sensor."""
        return self.coordinator.data.get("body")

    @property
    def icon(self):
        """Return the icon of the sensor."""
        return ICON

    @property
    def device_class(self):
        """Return de device class of the sensor."""
        return "mygekko__custom_device_class"
