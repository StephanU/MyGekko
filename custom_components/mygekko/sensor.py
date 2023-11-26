"""Sensor platform for MyGekko."""
from custom_components.mygekko.entity import MyGekkoControllerEntity
from custom_components.mygekko.entity import MyGekkoEntity
from homeassistant.components.sensor import SensorDeviceClass
from homeassistant.components.sensor import SensorEntity
from homeassistant.components.sensor import SensorEntityDescription
from homeassistant.components.sensor import SensorStateClass
from homeassistant.const import CONCENTRATION_PARTS_PER_MILLION
from homeassistant.const import PERCENTAGE
from homeassistant.const import UnitOfEnergy
from homeassistant.const import UnitOfPower
from homeassistant.const import UnitOfTemperature
from PyMyGekko.resources.AlarmsLogics import AlarmsLogic
from PyMyGekko.resources.EnergyCosts import EnergyCost
from PyMyGekko.resources.HotWaterSystems import HotWaterSystem
from PyMyGekko.resources.HotWaterSystems import HotWaterSystemFeature
from PyMyGekko.resources.RoomTemps import RoomTemp
from PyMyGekko.resources.RoomTemps import RoomTempsFeature

from .const import DOMAIN

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
    SensorEntityDescription(
        key="air_quality",
        name="Air Quality",
        state_class=SensorStateClass.MEASUREMENT,
        device_class=SensorDeviceClass.CO2,
    ),
    SensorEntityDescription(
        key="humidity",
        name="Humidity",
        state_class=SensorStateClass.MEASUREMENT,
        device_class=SensorDeviceClass.HUMIDITY,
    ),
    SensorEntityDescription(
        key="temperature",
        name="Temperature",
        state_class=SensorStateClass.MEASUREMENT,
        device_class=SensorDeviceClass.TEMPERATURE,
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
    for energy_cost in energy_costs:
        if energy_cost.sensor_data and "values" in energy_cost.sensor_data:
            for index, sensor in enumerate(energy_cost.sensor_data["values"]):
                if sensor and "name" in sensor and sensor["name"] in SENSORS:
                    async_add_devices(
                        [
                            MyGekkoEnergySensor(
                                coordinator,
                                energy_cost,
                                index,
                                SENSORS[sensor["name"]],
                            )
                        ]
                    )

    globals_network = coordinator.api.get_globals_network()
    alarms_logics: list[AlarmsLogic] = coordinator.api.get_alarms_logics()
    for alarms_logic in alarms_logics:
        async_add_devices(
            [MyGekkoAlarmsLogicsSensor(coordinator, alarms_logic, globals_network)]
        )

    room_temps: list[RoomTemp] = coordinator.api.get_room_temps()
    for room_temp in room_temps:
        if RoomTempsFeature.HUMIDITY in room_temp.supported_features:
            async_add_devices([MyGekkoRoomTempsHumiditySensor(coordinator, room_temp)])
        if RoomTempsFeature.AIR_QUALITY in room_temp.supported_features:
            async_add_devices(
                [MyGekkoRoomTempsAirQualitySensor(coordinator, room_temp)]
            )

    hotwater_systems: list[HotWaterSystem] = coordinator.api.get_hot_water_systems()
    for hotwater_system in hotwater_systems:
        if (
            HotWaterSystemFeature.BOTTOM_TEMPERATURE
            in hotwater_system.supported_features
        ):
            async_add_devices(
                [
                    MyGekkoHotwaterSystemsBottomTemperatureSensor(
                        coordinator, hotwater_system
                    )
                ]
            )
        if (
            HotWaterSystemFeature.BOTTOM_TEMPERATURE
            in hotwater_system.supported_features
        ):
            async_add_devices(
                [
                    MyGekkoHotwaterSystemsTopTemperatureSensor(
                        coordinator, hotwater_system
                    )
                ]
            )


class MyGekkoAlarmsLogicsSensor(MyGekkoControllerEntity, SensorEntity):
    """mygekko AlarmsLogics Sensor class."""

    _attr_has_entity_name = True

    def __init__(self, coordinator, alarms_logic: AlarmsLogic, globals_network):
        super().__init__(coordinator, alarms_logic, globals_network, "alarms_logic")
        self._alarms_logic = alarms_logic

    @property
    def state(self):
        """Return the state of the sensor."""
        return self._alarms_logic.value


class MyGekkoEnergySensor(MyGekkoEntity, SensorEntity):
    """mygekko EnergyCost Sensor class."""

    def __init__(
        self,
        coordinator,
        energy_cost: EnergyCost,
        index,
        sensorEntityDescription: SensorEntityDescription,
    ):
        super().__init__(
            coordinator,
            energy_cost,
            "energy_cost",
            energy_cost.sensor_data["values"][index]["name"],
        )
        self._energy_cost = energy_cost
        self.entity_description = sensorEntityDescription
        self._index = index

    @property
    def state(self):
        """Return the state of the sensor."""
        return self._energy_cost.sensor_data["values"][self._index]["value"]

    @property
    def native_unit_of_measurement(self) -> str | None:
        """Return the unit of measurement."""
        if (
            unit := self._energy_cost.sensor_data["values"][self._index]["unit"]
        ) is None or unit == 0:
            return None

        return SENSOR_UNIT_MAPPING[unit]


class MyGekkoRoomTempsHumiditySensor(MyGekkoEntity, SensorEntity):
    """mygekko Humidity Sensor class."""

    _attr_has_entity_name = True
    _attr_native_unit_of_measurement = PERCENTAGE

    def __init__(self, coordinator, room_temp: RoomTemp):
        super().__init__(coordinator, room_temp, "room_temps", "Humidity")
        self._room_temp = room_temp
        self.entity_description = SENSORS["humidity"]

    @property
    def state(self):
        """Return the state of the sensor."""
        return self._room_temp.humidity


class MyGekkoRoomTempsAirQualitySensor(MyGekkoEntity, SensorEntity):
    """mygekko AirQuality Sensor class."""

    _attr_has_entity_name = True
    _attr_native_unit_of_measurement = CONCENTRATION_PARTS_PER_MILLION

    def __init__(self, coordinator, room_temp: RoomTemp):
        super().__init__(coordinator, room_temp, "room_temps", "Air Quality")
        self._room_temp = room_temp
        self.entity_description = SENSORS["air_quality"]

    @property
    def state(self):
        """Return the state of the sensor."""
        return self._room_temp.air_quality


class MyGekkoHotwaterSystemsBottomTemperatureSensor(MyGekkoEntity, SensorEntity):
    """mygekko Bottom Temperature Sensor class."""

    _attr_has_entity_name = True
    _attr_native_unit_of_measurement = UnitOfTemperature.CELSIUS

    def __init__(self, coordinator, hotwater_system: HotWaterSystem):
        super().__init__(
            coordinator, hotwater_system, "hotwater_systems", "Bottom Temperature"
        )
        self._hotwater_system = hotwater_system
        self.entity_description = SENSORS["temperature"]

    @property
    def state(self):
        """Return the state of the sensor."""
        return self._hotwater_system.current_temperature_bottom


class MyGekkoHotwaterSystemsTopTemperatureSensor(MyGekkoEntity, SensorEntity):
    """mygekko Top Temperature Sensor class."""

    _attr_has_entity_name = True
    _attr_native_unit_of_measurement = UnitOfTemperature.CELSIUS

    def __init__(self, coordinator, hotwater_system: HotWaterSystem):
        super().__init__(
            coordinator, hotwater_system, "hotwater_systems", "Top Temperature"
        )
        self._hotwater_system = hotwater_system
        self.entity_description = SENSORS["temperature"]

    @property
    def state(self):
        """Return the state of the sensor."""
        return self._hotwater_system.current_temperature_top
