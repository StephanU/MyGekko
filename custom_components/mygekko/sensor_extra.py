"""Sensors for energy managers, e-mobility and heating circuits."""
from __future__ import annotations

from dataclasses import dataclass

from homeassistant.components.sensor import SensorDeviceClass
from homeassistant.components.sensor import SensorEntity
from homeassistant.components.sensor import SensorEntityDescription
from homeassistant.components.sensor import SensorStateClass
from homeassistant.const import PERCENTAGE
from homeassistant.const import UnitOfEnergy
from homeassistant.const import UnitOfPower
from homeassistant.const import UnitOfTemperature

from .entity import MyGekkoEntity


@dataclass(frozen=True, kw_only=True)
class MyGekkoPropertySensorDescription(SensorEntityDescription):
    """Sensor description reading a python property of the MyGekko device."""

    attr: str


def _power(key, attr, name, unit=UnitOfPower.WATT):
    return MyGekkoPropertySensorDescription(
        key=key,
        attr=attr,
        name=name,
        device_class=SensorDeviceClass.POWER,
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement=unit,
    )


def _energy(key, attr, name, unit=UnitOfEnergy.WATT_HOUR):
    return MyGekkoPropertySensorDescription(
        key=key,
        attr=attr,
        name=name,
        device_class=SensorDeviceClass.ENERGY,
        state_class=SensorStateClass.TOTAL_INCREASING,
        native_unit_of_measurement=unit,
    )


def _temperature(key, attr, name):
    return MyGekkoPropertySensorDescription(
        key=key,
        attr=attr,
        name=name,
        device_class=SensorDeviceClass.TEMPERATURE,
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement=UnitOfTemperature.CELSIUS,
    )


def _percent(key, attr, name, device_class=None):
    return MyGekkoPropertySensorDescription(
        key=key,
        attr=attr,
        name=name,
        device_class=device_class,
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement=PERCENTAGE,
    )


ENERGY_MANAGER_SENSORS = (
    _power("grid_meter_power", "grid_meter_power", "Grid Power"),
    _power("power_exported_to_grid", "power_exported_to_grid", "Power Exported To Grid"),
    _power("power_from_solar_panels", "power_from_solar_panels", "Solar Power"),
    _power("power_from_battery", "power_from_battery", "Battery Power"),
    _power("power_charging_battery", "power_charging_battery", "Battery Charging Power"),
    _power("home_power_consumption", "home_power_consumption", "Home Power Consumption"),
    _energy("daily_energy_imported_from_grid", "daily_energy_imported_from_grid", "Daily Energy Imported From Grid"),
    _energy("daily_energy_exported_to_grid", "daily_energy_exported_to_grid", "Daily Energy Exported To Grid"),
    _energy("daily_energy_from_solar_panels", "daily_energy_from_solar_panels", "Daily Solar Energy"),
    _energy("daily_energy_from_battery", "daily_energy_from_battery", "Daily Energy From Battery"),
    _energy("daily_energy_charging_battery", "daily_energy_charging_battery", "Daily Energy Charging Battery"),
    _energy("daily_home_energy_consumption", "daily_home_energy_consumption", "Daily Home Energy Consumption"),
    _percent("battery_soc", "battery_soc", "Battery Charge", SensorDeviceClass.BATTERY),
)

EMOBIL_SENSORS = (
    _power("current_charging_power", "current_charging_power", "Charging Power", UnitOfPower.KILO_WATT),
    _power("maximum_charging_power", "maximum_charging_power", "Maximum Charging Power", UnitOfPower.KILO_WATT),
    _power("charging_power_setpoint", "charging_power_setpoint", "Charging Power Setpoint", UnitOfPower.KILO_WATT),
    _energy("current_charging_energy", "current_charging_energy", "Charged Energy", UnitOfEnergy.KILO_WATT_HOUR),
)

HEATING_CIRCUIT_SENSORS = (
    _temperature("flow_temperature", "flow_temperature", "Flow Temperature"),
    _temperature("return_flow_temperature", "return_flow_temperature", "Return Flow Temperature"),
    _temperature("flow_temperature_setpoint", "flow_temperature_setpoint", "Flow Temperature Setpoint"),
    _temperature("dew_point", "dew_point", "Dew Point"),
    _percent("pump_working_level", "pump_working_level", "Pump Level"),
    _percent("valve_opening_level", "valve_opening_level", "Valve Opening"),
)


class MyGekkoPropertySensor(MyGekkoEntity, SensorEntity):
    """Generic sensor reading one property of a MyGekko device."""

    entity_description: MyGekkoPropertySensorDescription

    def __init__(self, coordinator, entity, prefix, description):
        """Initialize the sensor."""
        super().__init__(coordinator, entity, prefix, f"_{description.key}")
        self._entity = entity
        self.entity_description = description

    @property
    def native_value(self):
        """Return the value, None when not (yet) available."""
        return getattr(self._entity, self.entity_description.attr, None)


def build_extra_sensors(coordinator):
    """Create sensors for energy managers, e-mobility and heating circuits."""
    api = coordinator.api
    groups = (
        (api.get_energy_managers(), "energy_manager", ENERGY_MANAGER_SENSORS),
        (api.get_emobils(), "emobil", EMOBIL_SENSORS),
        (api.get_heating_circuits(), "heating_circuit", HEATING_CIRCUIT_SENSORS),
    )
    return [
        MyGekkoPropertySensor(coordinator, entity, prefix, description)
        for entities, prefix, descriptions in groups
        for entity in entities or []
        for description in descriptions
    ]
