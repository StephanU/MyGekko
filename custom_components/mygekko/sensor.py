"""Sensor platform for MyGekko."""
import logging

from homeassistant.components.sensor import SensorDeviceClass
from homeassistant.components.sensor import SensorEntity
from homeassistant.components.sensor import SensorEntityDescription
from homeassistant.components.sensor import SensorStateClass
from homeassistant.const import UnitOfEnergy
from homeassistant.const import UnitOfPower
from homeassistant.helpers.entity import DeviceInfo
from PyMyGekko.resources.AlarmsLogics import AlarmsLogic
from PyMyGekko.resources.EnergyCosts import EnergyCost

from .const import DOMAIN
from .const import NAME

_LOGGER: logging.Logger = logging.getLogger(__name__)

SENSOR_TYPES: tuple[SensorEntityDescription, ...] = (
    SensorEntityDescription(
        key="actPower",
        name="Actual Power",
        state_class=SensorStateClass.MEASUREMENT,
        device_class=SensorDeviceClass.POWER,
    ),
    SensorEntityDescription(
        key="powerMax",
        name="Power Max",
        state_class=SensorStateClass.MEASUREMENT,
        device_class=SensorDeviceClass.POWER,
    ),
    SensorEntityDescription(
        key="energySum",
        name="Energy Sum",
        state_class=SensorStateClass.TOTAL_INCREASING,
        device_class=SensorDeviceClass.ENERGY,
    ),
    SensorEntityDescription(
        key="energyToday",
        name="Energy Today",
        state_class=SensorStateClass.TOTAL,
        device_class=SensorDeviceClass.ENERGY,
    ),
    SensorEntityDescription(
        key="energyMonth",
        name="Energy Month",
        state_class=SensorStateClass.TOTAL,
        device_class=SensorDeviceClass.ENERGY,
    ),
    SensorEntityDescription(
        key="energyToday6",
        name="Energy Today 6",
        state_class=SensorStateClass.TOTAL,
        device_class=SensorDeviceClass.ENERGY,
    ),
    SensorEntityDescription(
        key="energyToday12",
        name="Energy Today 12",
        state_class=SensorStateClass.TOTAL,
        device_class=SensorDeviceClass.ENERGY,
    ),
    SensorEntityDescription(
        key="energyToday18",
        name="Energy Today 18",
        state_class=SensorStateClass.TOTAL,
        device_class=SensorDeviceClass.ENERGY,
    ),
    SensorEntityDescription(
        key="energyToday24",
        name="Energy Today 24",
        state_class=SensorStateClass.TOTAL,
        device_class=SensorDeviceClass.ENERGY,
    ),
    SensorEntityDescription(
        key="energyYesterd6",
        name="Energy Yesterday 6",
        state_class=SensorStateClass.TOTAL,
        device_class=SensorDeviceClass.ENERGY,
    ),
    SensorEntityDescription(
        key="energyYesterd12",
        name="Energy Yesterday 12",
        state_class=SensorStateClass.TOTAL,
        device_class=SensorDeviceClass.ENERGY,
    ),
    SensorEntityDescription(
        key="energyYesterd18",
        name="Energy Yesterday 18",
        state_class=SensorStateClass.TOTAL,
        device_class=SensorDeviceClass.ENERGY,
    ),
    SensorEntityDescription(
        key="energyYesterd24",
        name="Energy Yesterday 24",
        state_class=SensorStateClass.TOTAL,
        device_class=SensorDeviceClass.ENERGY,
    ),
    SensorEntityDescription(
        key="energyYear",
        name="Energy Year",
        state_class=SensorStateClass.TOTAL,
        device_class=SensorDeviceClass.ENERGY,
    ),
)

SENSORS = {desc.key: desc for desc in SENSOR_TYPES}

SENSOR_UNIT_MAPPING = {
    "Wh": UnitOfEnergy.WATT_HOUR,
    "kWh": UnitOfEnergy.KILO_WATT_HOUR,
    "kW": UnitOfPower.KILO_WATT,
    "W": UnitOfPower.WATT,
}


async def async_setup_entry(hass, entry, async_add_devices):
    """Setup sensor platform."""
    coordinator = hass.data[DOMAIN][entry.entry_id]
    energy_costs: list[EnergyCost] = coordinator.api.get_energy_costs()
    if energy_costs is not None:
        for energy_cost in energy_costs:
            if energy_cost.sensor_data and "values" in energy_cost.sensor_data:
                for sensor in energy_cost.sensor_data["values"]:
                    if sensor and "name" in sensor and sensor["name"] in SENSORS:
                        async_add_devices(
                            [
                                MyGekkoEnergySensor(
                                    energy_cost, sensor, SENSORS[sensor["name"]]
                                )
                            ]
                        )
    globals_network = coordinator.api.get_globals_network()
    alarms_logics: list[AlarmsLogic] = coordinator.api.get_alarms_logics()
    if alarms_logics is not None:
        for alarms_logic in alarms_logics:
            async_add_devices(
                [MyGekkoAlarmsLogicsSensor(alarms_logic, globals_network)]
            )


class MyGekkoAlarmsLogicsSensor(SensorEntity):
    """mygekko AlarmsLogics Sensor class."""

    _attr_has_entity_name = True

    def __init__(self, alarms_logic: AlarmsLogic, globals_network):
        self._attr_unique_id = "alarms_logic_" + alarms_logic.id
        self._attr_name = alarms_logic.name
        self._alarms_logic = alarms_logic
        self._attr_device_info = DeviceInfo(
            identifiers={
                (DOMAIN, "mygekko_controller_" + globals_network["gekkoname"])
            },
            name=globals_network["gekkoname"],
            manufacturer=NAME,
            sw_version=globals_network["version"],
            hw_version=globals_network["hardware"],
        )

        _LOGGER.debug("Added sensor %s %s", alarms_logic.name, self.unique_id)

    @property
    def state(self):
        """Return the state of the sensor."""
        return self._alarms_logic.value


class MyGekkoEnergySensor(SensorEntity):
    """mygekko EnergyCost Sensor class."""

    _attr_has_entity_name = True

    def __init__(
        self,
        energy_cost: EnergyCost,
        sensor_data,
        sensorEntityDescription: SensorEntityDescription,
    ):
        self.entity_description = sensorEntityDescription
        self._attr_unique_id = (
            "energy_cost_" + energy_cost.id + "_" + sensor_data["name"]
        )
        self._energy_cost = energy_cost
        self._sensor_data = sensor_data
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, "energy_cost_" + energy_cost.id)},
            name=energy_cost.name,
            manufacturer=NAME,
        )

        _LOGGER.debug(
            "Added sensor %s %s %s",
            sensor_data["name"],
            self.unique_id,
            sensor_data["unit"],
        )

    @property
    def state(self):
        """Return the state of the sensor."""
        return self._sensor_data["value"]

    @property
    def native_unit_of_measurement(self) -> str | None:
        """Return the unit of measurement."""
        if (unit := self._sensor_data["unit"]) is None or unit == 0:
            return None

        return SENSOR_UNIT_MAPPING[unit]
