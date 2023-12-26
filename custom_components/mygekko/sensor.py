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
from PyMyGekko.resources.vents import Vent
from PyMyGekko.resources.vents import VentFeature

from .const import DOMAIN

SENSOR_TYPES: tuple[SensorEntityDescription, ...] = (
    SensorEntityDescription(
        key="actPower",
        translation_key="mygekko_energycost_act_power",
        state_class=SensorStateClass.MEASUREMENT,
        device_class=SensorDeviceClass.POWER,
    ),
    SensorEntityDescription(
        key="powerMax",
        name="Power Max",
        translation_key="mygekko_energycost_power_max",
        state_class=SensorStateClass.MEASUREMENT,
        device_class=SensorDeviceClass.POWER,
    ),
    SensorEntityDescription(
        key="energySum",
        name="Energy Sum",
        translation_key="mygekko_energycost_energy_sum",
        state_class=SensorStateClass.TOTAL_INCREASING,
        device_class=SensorDeviceClass.ENERGY,
    ),
    SensorEntityDescription(
        key="energyToday",
        name="Energy Today",
        translation_key="mygekko_energycost_energy_today",
        state_class=SensorStateClass.TOTAL,
        device_class=SensorDeviceClass.ENERGY,
    ),
    SensorEntityDescription(
        key="energyMonth",
        name="Energy Month",
        translation_key="mygekko_energycost_energy_month",
        state_class=SensorStateClass.TOTAL,
        device_class=SensorDeviceClass.ENERGY,
    ),
    SensorEntityDescription(
        key="energyToday6",
        name="Energy Today 6",
        translation_key="mygekko_energycost_energy_today6",
        state_class=SensorStateClass.TOTAL,
        device_class=SensorDeviceClass.ENERGY,
    ),
    SensorEntityDescription(
        key="energyToday12",
        name="Energy Today 12",
        translation_key="mygekko_energycost_energy_today12",
        state_class=SensorStateClass.TOTAL,
        device_class=SensorDeviceClass.ENERGY,
    ),
    SensorEntityDescription(
        key="energyToday18",
        name="Energy Today 18",
        translation_key="mygekko_energycost_energy_today18",
        state_class=SensorStateClass.TOTAL,
        device_class=SensorDeviceClass.ENERGY,
    ),
    SensorEntityDescription(
        key="energyToday24",
        name="Energy Today 24",
        translation_key="mygekko_energycost_energy_today24",
        state_class=SensorStateClass.TOTAL,
        device_class=SensorDeviceClass.ENERGY,
    ),
    SensorEntityDescription(
        key="energyYesterd6",
        name="Energy Yesterday 6",
        translation_key="mygekko_energycost_energy_yesterd6",
        state_class=SensorStateClass.TOTAL,
        device_class=SensorDeviceClass.ENERGY,
    ),
    SensorEntityDescription(
        key="energyYesterd12",
        name="Energy Yesterday 12",
        translation_key="mygekko_energycost_energy_yesterd12",
        state_class=SensorStateClass.TOTAL,
        device_class=SensorDeviceClass.ENERGY,
    ),
    SensorEntityDescription(
        key="energyYesterd18",
        name="Energy Yesterday 18",
        translation_key="mygekko_energycost_energy_yesterd18",
        state_class=SensorStateClass.TOTAL,
        device_class=SensorDeviceClass.ENERGY,
    ),
    SensorEntityDescription(
        key="energyYesterd24",
        name="Energy Yesterday 24",
        translation_key="mygekko_energycost_energy_yesterd24",
        state_class=SensorStateClass.TOTAL,
        device_class=SensorDeviceClass.ENERGY,
    ),
    SensorEntityDescription(
        key="energyYear",
        name="Energy Year",
        translation_key="mygekko_energycost_energy_year",
        state_class=SensorStateClass.TOTAL,
        device_class=SensorDeviceClass.ENERGY,
    ),
    SensorEntityDescription(
        key="voc",
        state_class=SensorStateClass.MEASUREMENT,
        device_class=SensorDeviceClass.VOLATILE_ORGANIC_COMPOUNDS_PARTS,
    ),
    SensorEntityDescription(
        key="air_quality",
        state_class=SensorStateClass.MEASUREMENT,
        device_class=SensorDeviceClass.AQI,
    ),
    SensorEntityDescription(
        key="co2",
        state_class=SensorStateClass.MEASUREMENT,
        device_class=SensorDeviceClass.CO2,
    ),
    SensorEntityDescription(
        key="humidity",
        state_class=SensorStateClass.MEASUREMENT,
        device_class=SensorDeviceClass.HUMIDITY,
    ),
    SensorEntityDescription(
        key="temperature",
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
    """Set up sensor platform."""
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
    vents: list[Vent] = coordinator.api.get_vents()
    for vent in vents:
        if VentFeature.HUMIDITY in vent.supported_features:
            async_add_devices([MyGekkoVentHumiditySensor(coordinator, vent)])
        if VentFeature.AIR_QUALITY in vent.supported_features:
            async_add_devices([MyGekkoVentAirQualitySensor(coordinator, vent)])
        if VentFeature.CO2 in vent.supported_features:
            async_add_devices([MyGekkoVentCo2Sensor(coordinator, vent)])

        async_add_devices(
            [
                MyGekkoVentExhaustAirTemperatureSensor(coordinator, vent),
                MyGekkoVentOutgoingAirTemperatureSensor(coordinator, vent),
                MyGekkoVentOutsideAirTemperatureSensor(coordinator, vent),
                MyGekkoVentSupplyAirTemperatureSensor(coordinator, vent),
                MyGekkoVentSupplyAirWorkingLevelSensor(coordinator, vent),
                MyGekkoVentExhaustAirWorkingLevelSensor(coordinator, vent),
            ]
        )


class MyGekkoAlarmsLogicsSensor(MyGekkoControllerEntity, SensorEntity):
    """mygekko AlarmsLogics Sensor class."""

    def __init__(self, coordinator, alarms_logic: AlarmsLogic, globals_network):
        """Initialize a MyGekko AlarmsLogics sensor."""
        super().__init__(coordinator, alarms_logic, globals_network, "alarms_logic")
        self._alarms_logic = alarms_logic

    @property
    def native_value(self):
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
        """Initialize a MyGekko EnergyCost sensor."""
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
    def native_value(self):
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

    _attr_native_unit_of_measurement = PERCENTAGE

    def __init__(self, coordinator, room_temp: RoomTemp):
        """Initialize a MyGekko RoomTemp humidity sensor."""
        super().__init__(coordinator, room_temp, "room_temps", "Humidity")
        self._room_temp = room_temp
        self.entity_description = SENSORS["humidity"]

    @property
    def native_value(self):
        """Return the state of the sensor."""
        return self._room_temp.humidity


class MyGekkoRoomTempsAirQualitySensor(MyGekkoEntity, SensorEntity):
    """mygekko AirQuality Sensor class."""

    _attr_native_unit_of_measurement = CONCENTRATION_PARTS_PER_MILLION

    def __init__(self, coordinator, room_temp: RoomTemp):
        """Initialize a MyGekko RoomTemp air quality sensor."""
        super().__init__(coordinator, room_temp, "room_temps", "Air Quality")
        self._room_temp = room_temp
        self.entity_description = SENSORS["voc"]

    @property
    def native_value(self):
        """Return the state of the sensor."""
        return self._room_temp.air_quality


class MyGekkoHotwaterSystemsBottomTemperatureSensor(MyGekkoEntity, SensorEntity):
    """mygekko Bottom Temperature Sensor class."""

    _attr_native_unit_of_measurement = UnitOfTemperature.CELSIUS

    def __init__(self, coordinator, hotwater_system: HotWaterSystem):
        """Initialize a MyGekko bottom Temperature sensor."""
        super().__init__(
            coordinator, hotwater_system, "hotwater_systems", "Bottom Temperature"
        )
        self._hotwater_system = hotwater_system
        self.entity_description = SENSORS["temperature"]
        self._attr_translation_key = "mygekko_hotwatersystem_bottom_temperature"

    @property
    def native_value(self):
        """Return the state of the sensor."""
        return self._hotwater_system.current_temperature_bottom


class MyGekkoHotwaterSystemsTopTemperatureSensor(MyGekkoEntity, SensorEntity):
    """mygekko Top Temperature Sensor class."""

    _attr_native_unit_of_measurement = UnitOfTemperature.CELSIUS

    def __init__(self, coordinator, hotwater_system: HotWaterSystem):
        """Initialize a MyGekko top Temperature sensor."""
        super().__init__(
            coordinator, hotwater_system, "hotwater_systems", "Top Temperature"
        )
        self._hotwater_system = hotwater_system
        self.entity_description = SENSORS["temperature"]
        self._attr_translation_key = "mygekko_hotwatersystem_top_temperature"

    @property
    def native_value(self):
        """Return the state of the sensor."""
        return self._hotwater_system.current_temperature_top


class MyGekkoVentHumiditySensor(MyGekkoEntity, SensorEntity):
    """mygekko Vent Humidity Sensor class."""

    _attr_native_unit_of_measurement = PERCENTAGE

    def __init__(self, coordinator, vent: Vent):
        """Initialize a MyGekko vent humidity sensor."""
        super().__init__(coordinator, vent, "vents", "Humidity")
        self._vent = vent
        self.entity_description = SENSORS["humidity"]

    @property
    def native_value(self):
        """Return the state of the sensor."""
        return self._vent.relative_humidity


class MyGekkoVentAirQualitySensor(MyGekkoEntity, SensorEntity):
    """mygekko Vent Air Quality Sensor class."""

    _attr_native_unit_of_measurement = PERCENTAGE

    def __init__(self, coordinator, vent: Vent):
        """Initialize a MyGekko vent air quality sensor."""
        super().__init__(coordinator, vent, "vents", "Air Quality")
        self._vent = vent
        self.entity_description = SENSORS["air_quality"]

    @property
    def native_value(self):
        """Return the state of the sensor."""
        return self._vent.air_quality


class MyGekkoVentCo2Sensor(MyGekkoEntity, SensorEntity):
    """mygekko Vent CO2 Sensor class."""

    _attr_native_unit_of_measurement = CONCENTRATION_PARTS_PER_MILLION

    def __init__(self, coordinator, vent: Vent):
        """Initialize a MyGekko vent co2 sensor."""
        super().__init__(coordinator, vent, "vents", "CO2")
        self._vent = vent
        self.entity_description = SENSORS["co2"]

    @property
    def native_value(self):
        """Return the state of the sensor."""
        return self._vent.co2


class MyGekkoVentExhaustAirTemperatureSensor(MyGekkoEntity, SensorEntity):
    """mygekko Top Temperature Sensor class."""

    _attr_native_unit_of_measurement = UnitOfTemperature.CELSIUS

    def __init__(self, coordinator, vent: Vent):
        """Initialize a MyGekko vent exhaust air temperature sensor."""
        super().__init__(coordinator, vent, "vents", "Exhaust Air Temperature")
        self._vent = vent
        self.entity_description = SENSORS["temperature"]
        self._attr_translation_key = "mygekko_vent_exhaust_air_temperature"

    @property
    def native_value(self):
        """Return the state of the sensor."""
        return self._vent.exhaust_air_temperature


class MyGekkoVentExhaustAirWorkingLevelSensor(MyGekkoEntity, SensorEntity):
    """mygekko Top Temperature Sensor class."""

    _attr_native_unit_of_measurement = PERCENTAGE
    _attr_icon = "mdi:gauge"

    def __init__(self, coordinator, vent: Vent):
        """Initialize a MyGekko vent exhaust air working level sensor."""
        super().__init__(coordinator, vent, "vents", "Exhaust Air Working Level")
        self._vent = vent
        self._attr_translation_key = "mygekko_vent_exhaust_air_working_level"

    @property
    def native_value(self):
        """Return the state of the sensor."""
        return self._vent.exhaust_air_working_level


class MyGekkoVentOutgoingAirTemperatureSensor(MyGekkoEntity, SensorEntity):
    """mygekko Top Temperature Sensor class."""

    _attr_native_unit_of_measurement = UnitOfTemperature.CELSIUS

    def __init__(self, coordinator, vent: Vent):
        """Initialize a MyGekko vent outgoing air temperature sensor."""
        super().__init__(coordinator, vent, "vents", "Outgoing Air Temperature")
        self._vent = vent
        self.entity_description = SENSORS["temperature"]
        self._attr_translation_key = "mygekko_vent_outgoing_air_temperature"

    @property
    def native_value(self):
        """Return the state of the sensor."""
        return self._vent.outgoing_air_temperature


class MyGekkoVentOutsideAirTemperatureSensor(MyGekkoEntity, SensorEntity):
    """mygekko Top Temperature Sensor class."""

    _attr_native_unit_of_measurement = UnitOfTemperature.CELSIUS

    def __init__(self, coordinator, vent: Vent):
        """Initialize a MyGekko vent outside air temperature sensor."""
        super().__init__(coordinator, vent, "vents", "Outside Air Temperature")
        self._vent = vent
        self.entity_description = SENSORS["temperature"]
        self._attr_translation_key = "mygekko_vent_outside_air_temperature"

    @property
    def native_value(self):
        """Return the state of the sensor."""
        return self._vent.outside_air_temperature


class MyGekkoVentSupplyAirTemperatureSensor(MyGekkoEntity, SensorEntity):
    """mygekko Top Temperature Sensor class."""

    _attr_native_unit_of_measurement = UnitOfTemperature.CELSIUS

    def __init__(self, coordinator, vent: Vent):
        """Initialize a MyGekko vent supply air temperature sensor."""
        super().__init__(coordinator, vent, "vents", "Supply Air Temperature")
        self._vent = vent
        self.entity_description = SENSORS["temperature"]
        self._attr_translation_key = "mygekko_vent_supply_air_temperature"

    @property
    def native_value(self):
        """Return the state of the sensor."""
        return self._vent.supply_air_temperature


class MyGekkoVentSupplyAirWorkingLevelSensor(MyGekkoEntity, SensorEntity):
    """mygekko Supply Air Working Level class."""

    _attr_native_unit_of_measurement = PERCENTAGE
    _attr_icon = "mdi:gauge"

    def __init__(self, coordinator, vent: Vent):
        """Initialize a MyGekko vent supply air working level sensor."""
        super().__init__(coordinator, vent, "vents", "Supply Air Working Level")
        self._vent = vent
        self._attr_translation_key = "mygekko_vent_supply_air_working_level"

    @property
    def native_value(self):
        """Return the state of the sensor."""
        return self._vent.supply_air_working_level
