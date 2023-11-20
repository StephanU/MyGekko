"""Sensor platform for MyGekko."""
from homeassistant.components.sensor import SensorDeviceClass
from homeassistant.components.sensor import SensorEntity
from homeassistant.components.sensor import SensorEntityDescription
from homeassistant.components.sensor import SensorStateClass
from PyMyGekko.resources.EnergyCosts import EnergyCost

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
    energy_costs: list[EnergyCost] = coordinator.api.get_energy_costs()
    if energy_costs is not None:
        for energy_cost in energy_costs:
            if energy_cost.sensor_data and "values" in energy_cost.sensor_data:
                async_add_devices(
                    MyGekkoSensor(coordinator, energy_cost, sensor)
                    for sensor in energy_cost.sensor_data["values"]
                )


class MyGekkoSensor(MyGekkoEntity, SensorEntity):
    """mygekko Sensor class."""

    def __init__(self, coordinator, energy_cost: EnergyCost, sensor_data):
        super().__init__(coordinator, energy_cost, SENSOR)
        self._energy_cost = energy_cost
        self._sensor_data = sensor_data
        # supported_features = self._blind.supported_features
        self._attr_supported_features = 0

    @property
    def name(self):
        """Return the name of the sensor."""
        return self._sensor_data["name"]

    @property
    def state(self):
        """Return the state of the sensor."""
        return self._sensor_data["value"]

    @property
    def icon(self):
        """Return the icon of the sensor."""
        return ICON

    @property
    def device_class(self):
        """Return de device class of the sensor."""
        return "mygekko__custom_device_class"
