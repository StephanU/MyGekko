"""Sensor platform for MyGekko."""
from collections.abc import Callable
from dataclasses import dataclass
from datetime import datetime
from datetime import timedelta
import re
from typing import Any

from custom_components.mygekko.entity import MyGekkoControllerEntity
from custom_components.mygekko.entity import MyGekkoEntity
from homeassistant.components.sensor import SensorDeviceClass
from homeassistant.components.sensor import SensorEntity
from homeassistant.components.sensor import SensorEntityDescription
from homeassistant.components.sensor import SensorStateClass
from homeassistant.const import CONCENTRATION_PARTS_PER_MILLION
from homeassistant.const import EntityCategory
from homeassistant.const import LIGHT_LUX
from homeassistant.const import PERCENTAGE
from homeassistant.const import UnitOfElectricCurrent
from homeassistant.const import UnitOfEnergy
from homeassistant.const import UnitOfPower
from homeassistant.const import UnitOfSpeed
from homeassistant.const import UnitOfTemperature
from homeassistant.const import UnitOfVolumeFlowRate
from homeassistant.util import dt as dt_util
from PyMyGekko.resources.AlarmsLogics import AlarmsLogic
from PyMyGekko.resources.DoorInterComs import DoorInterCom
from PyMyGekko.resources.EMobils import EMobil
from PyMyGekko.resources.EMobils import EMobilChargeRequestState
from PyMyGekko.resources.EMobils import EMobilChargeState
from PyMyGekko.resources.EMobils import EMobilPluggedState
from PyMyGekko.resources.EnergyCosts import EnergyCost
from PyMyGekko.resources.EnergyManagers import EnergyManager
from PyMyGekko.resources.EnergyManagers import EnergyManagerBatteryModel
from PyMyGekko.resources.EnergyManagers import EnergyManagerComponentState
from PyMyGekko.resources.EnergyManagers import EnergyManagerEmsEnabled
from PyMyGekko.resources.EnergyManagers import EnergyManagerState
from PyMyGekko.resources.HeatingCircuits import HeatingCircuit
from PyMyGekko.resources.HeatingCircuits import HeatingCircuitCoolingModeState
from PyMyGekko.resources.HeatingCircuits import HeatingCircuitDeviceModel
from PyMyGekko.resources.HeatingCircuits import HeatingCircuitState
from PyMyGekko.resources.HotWaterSystems import HotWaterSystem
from PyMyGekko.resources.HotWaterSystems import HotWaterSystemFeature
from PyMyGekko.resources.RoomTemps import RoomTemp
from PyMyGekko.resources.RoomTemps import RoomTempsFeature
from PyMyGekko.resources.Vents import Vent
from PyMyGekko.resources.Vents import VentFeature
from PyMyGekko.resources.Meteo import Meteo

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
    SensorEntityDescription(
        key="rain",
        state_class=SensorStateClass.MEASUREMENT,
        device_class=SensorDeviceClass.VOLUME_FLOW_RATE,
    ),
    SensorEntityDescription(
        key="light",
        state_class=SensorStateClass.MEASUREMENT,
        device_class=SensorDeviceClass.ILLUMINANCE,
    ),
    SensorEntityDescription(
        key="wind",
        state_class=SensorStateClass.MEASUREMENT,
        device_class=SensorDeviceClass.WIND_SPEED,
    ),
)

SENSORS = {desc.key: desc for desc in SENSOR_TYPES}

SENSOR_UNIT_MAPPING = {
    "Wh": UnitOfEnergy.WATT_HOUR,
    "kWh": UnitOfEnergy.KILO_WATT_HOUR,
    "kW": UnitOfPower.KILO_WATT,
    "W": UnitOfPower.WATT,
}


def _enum_option(value):
    """Return the lowercase enum member name as option string, or None."""
    return value.name.lower() if value is not None else None


def _enum_options(enum_cls) -> list[str]:
    """Return the lowercase enum member names to use as sensor options."""
    return [member.name.lower() for member in enum_cls]


@dataclass(frozen=True, kw_only=True)
class MyGekkoValueSensorDescription(SensorEntityDescription):
    """Describes a MyGekko value sensor backed by a resource property."""

    value_fn: Callable[[Any], Any]


ENERGY_MANAGER_SENSORS: tuple[MyGekkoValueSensorDescription, ...] = (
    MyGekkoValueSensorDescription(
        key="grid_power",
        translation_key="mygekko_energymanager_grid_power",
        device_class=SensorDeviceClass.POWER,
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement=UnitOfPower.WATT,
        value_fn=lambda em: em.grid_meter_power,
    ),
    MyGekkoValueSensorDescription(
        key="power_exported_to_grid",
        translation_key="mygekko_energymanager_power_exported_to_grid",
        device_class=SensorDeviceClass.POWER,
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement=UnitOfPower.WATT,
        value_fn=lambda em: em.power_exported_to_grid,
    ),
    MyGekkoValueSensorDescription(
        key="solar_power",
        translation_key="mygekko_energymanager_solar_power",
        device_class=SensorDeviceClass.POWER,
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement=UnitOfPower.WATT,
        value_fn=lambda em: em.power_from_solar_panels,
    ),
    MyGekkoValueSensorDescription(
        key="battery_power",
        translation_key="mygekko_energymanager_battery_power",
        device_class=SensorDeviceClass.POWER,
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement=UnitOfPower.WATT,
        value_fn=lambda em: em.power_from_battery,
    ),
    MyGekkoValueSensorDescription(
        key="battery_charging_power",
        translation_key="mygekko_energymanager_battery_charging_power",
        device_class=SensorDeviceClass.POWER,
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement=UnitOfPower.WATT,
        value_fn=lambda em: em.power_charging_battery,
    ),
    MyGekkoValueSensorDescription(
        key="home_power_consumption",
        translation_key="mygekko_energymanager_home_power_consumption",
        device_class=SensorDeviceClass.POWER,
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement=UnitOfPower.WATT,
        value_fn=lambda em: em.home_power_consumption,
    ),
    MyGekkoValueSensorDescription(
        key="alternative_power_consumption",
        translation_key="mygekko_energymanager_alternative_power_consumption",
        device_class=SensorDeviceClass.POWER,
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement=UnitOfPower.WATT,
        value_fn=lambda em: em.alternative_power_consumption,
    ),
    MyGekkoValueSensorDescription(
        key="daily_energy_imported_from_grid",
        translation_key="mygekko_energymanager_daily_energy_imported_from_grid",
        device_class=SensorDeviceClass.ENERGY,
        state_class=SensorStateClass.TOTAL_INCREASING,
        native_unit_of_measurement=UnitOfEnergy.WATT_HOUR,
        value_fn=lambda em: em.daily_energy_imported_from_grid,
    ),
    MyGekkoValueSensorDescription(
        key="daily_energy_exported_to_grid",
        translation_key="mygekko_energymanager_daily_energy_exported_to_grid",
        device_class=SensorDeviceClass.ENERGY,
        state_class=SensorStateClass.TOTAL_INCREASING,
        native_unit_of_measurement=UnitOfEnergy.WATT_HOUR,
        value_fn=lambda em: em.daily_energy_exported_to_grid,
    ),
    MyGekkoValueSensorDescription(
        key="daily_energy_from_solar_panels",
        translation_key="mygekko_energymanager_daily_energy_from_solar_panels",
        device_class=SensorDeviceClass.ENERGY,
        state_class=SensorStateClass.TOTAL_INCREASING,
        native_unit_of_measurement=UnitOfEnergy.WATT_HOUR,
        value_fn=lambda em: em.daily_energy_from_solar_panels,
    ),
    MyGekkoValueSensorDescription(
        key="daily_energy_from_battery",
        translation_key="mygekko_energymanager_daily_energy_from_battery",
        device_class=SensorDeviceClass.ENERGY,
        state_class=SensorStateClass.TOTAL_INCREASING,
        native_unit_of_measurement=UnitOfEnergy.WATT_HOUR,
        value_fn=lambda em: em.daily_energy_from_battery,
    ),
    MyGekkoValueSensorDescription(
        key="daily_energy_charging_battery",
        translation_key="mygekko_energymanager_daily_energy_charging_battery",
        device_class=SensorDeviceClass.ENERGY,
        state_class=SensorStateClass.TOTAL_INCREASING,
        native_unit_of_measurement=UnitOfEnergy.WATT_HOUR,
        value_fn=lambda em: em.daily_energy_charging_battery,
    ),
    MyGekkoValueSensorDescription(
        key="daily_home_energy_consumption",
        translation_key="mygekko_energymanager_daily_home_energy_consumption",
        device_class=SensorDeviceClass.ENERGY,
        state_class=SensorStateClass.TOTAL_INCREASING,
        native_unit_of_measurement=UnitOfEnergy.WATT_HOUR,
        value_fn=lambda em: em.daily_home_energy_consumption,
    ),
    MyGekkoValueSensorDescription(
        key="battery_soc",
        translation_key="mygekko_energymanager_battery_soc",
        device_class=SensorDeviceClass.BATTERY,
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement=PERCENTAGE,
        value_fn=lambda em: em.battery_soc,
    ),
    MyGekkoValueSensorDescription(
        key="max_power_consumption_from_grid",
        translation_key="mygekko_energymanager_max_power_consumption_from_grid",
        device_class=SensorDeviceClass.POWER,
        native_unit_of_measurement=UnitOfPower.KILO_WATT,
        entity_category=EntityCategory.DIAGNOSTIC,
        value_fn=lambda em: em.max_power_consumption_from_grid,
    ),
    MyGekkoValueSensorDescription(
        key="max_power_export_to_grid",
        translation_key="mygekko_energymanager_max_power_export_to_grid",
        device_class=SensorDeviceClass.POWER,
        native_unit_of_measurement=UnitOfPower.KILO_WATT,
        entity_category=EntityCategory.DIAGNOSTIC,
        value_fn=lambda em: em.max_power_export_to_grid,
    ),
    MyGekkoValueSensorDescription(
        key="max_power_solar_panels",
        translation_key="mygekko_energymanager_max_power_solar_panels",
        device_class=SensorDeviceClass.POWER,
        native_unit_of_measurement=UnitOfPower.KILO_WATT,
        entity_category=EntityCategory.DIAGNOSTIC,
        value_fn=lambda em: em.max_power_solar_panels,
    ),
    MyGekkoValueSensorDescription(
        key="max_power_battery",
        translation_key="mygekko_energymanager_max_power_battery",
        device_class=SensorDeviceClass.POWER,
        native_unit_of_measurement=UnitOfPower.KILO_WATT,
        entity_category=EntityCategory.DIAGNOSTIC,
        value_fn=lambda em: em.max_power_battery,
    ),
    MyGekkoValueSensorDescription(
        key="grid_meter_state",
        translation_key="mygekko_energymanager_grid_meter_state",
        device_class=SensorDeviceClass.ENUM,
        options=_enum_options(EnergyManagerComponentState),
        entity_category=EntityCategory.DIAGNOSTIC,
        value_fn=lambda em: _enum_option(em.grid_meter_state),
    ),
    MyGekkoValueSensorDescription(
        key="solar_panel_state",
        translation_key="mygekko_energymanager_solar_panel_state",
        device_class=SensorDeviceClass.ENUM,
        options=_enum_options(EnergyManagerComponentState),
        entity_category=EntityCategory.DIAGNOSTIC,
        value_fn=lambda em: _enum_option(em.solar_panel_state),
    ),
    MyGekkoValueSensorDescription(
        key="battery_state",
        translation_key="mygekko_energymanager_battery_state",
        device_class=SensorDeviceClass.ENUM,
        options=_enum_options(EnergyManagerComponentState),
        entity_category=EntityCategory.DIAGNOSTIC,
        value_fn=lambda em: _enum_option(em.battery_state),
    ),
    MyGekkoValueSensorDescription(
        key="load_shedding_state",
        translation_key="mygekko_energymanager_load_shedding_state",
        device_class=SensorDeviceClass.ENUM,
        options=_enum_options(EnergyManagerState),
        entity_category=EntityCategory.DIAGNOSTIC,
        value_fn=lambda em: _enum_option(em.load_shedding_state),
    ),
    MyGekkoValueSensorDescription(
        key="ems_state",
        translation_key="mygekko_energymanager_ems_state",
        device_class=SensorDeviceClass.ENUM,
        options=_enum_options(EnergyManagerState),
        entity_category=EntityCategory.DIAGNOSTIC,
        value_fn=lambda em: _enum_option(em.ems_state),
    ),
    MyGekkoValueSensorDescription(
        key="ems_enabled",
        translation_key="mygekko_energymanager_ems_enabled",
        device_class=SensorDeviceClass.ENUM,
        options=_enum_options(EnergyManagerEmsEnabled),
        entity_category=EntityCategory.DIAGNOSTIC,
        value_fn=lambda em: _enum_option(em.ems_enabled),
    ),
    MyGekkoValueSensorDescription(
        key="battery_model",
        translation_key="mygekko_energymanager_battery_model",
        device_class=SensorDeviceClass.ENUM,
        options=_enum_options(EnergyManagerBatteryModel),
        entity_category=EntityCategory.DIAGNOSTIC,
        value_fn=lambda em: _enum_option(em.battery_model),
    ),
)


HEATING_CIRCUIT_SENSORS: tuple[MyGekkoValueSensorDescription, ...] = (
    MyGekkoValueSensorDescription(
        key="flow_temperature",
        translation_key="mygekko_heatingcircuit_flow_temperature",
        device_class=SensorDeviceClass.TEMPERATURE,
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement=UnitOfTemperature.CELSIUS,
        value_fn=lambda hc: hc.flow_temperature,
    ),
    MyGekkoValueSensorDescription(
        key="return_flow_temperature",
        translation_key="mygekko_heatingcircuit_return_flow_temperature",
        device_class=SensorDeviceClass.TEMPERATURE,
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement=UnitOfTemperature.CELSIUS,
        value_fn=lambda hc: hc.return_flow_temperature,
    ),
    MyGekkoValueSensorDescription(
        key="dew_point",
        translation_key="mygekko_heatingcircuit_dew_point",
        device_class=SensorDeviceClass.TEMPERATURE,
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement=UnitOfTemperature.CELSIUS,
        value_fn=lambda hc: hc.dew_point,
    ),
    MyGekkoValueSensorDescription(
        key="flow_temperature_setpoint",
        translation_key="mygekko_heatingcircuit_flow_temperature_setpoint",
        device_class=SensorDeviceClass.TEMPERATURE,
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement=UnitOfTemperature.CELSIUS,
        value_fn=lambda hc: hc.flow_temperature_setpoint,
    ),
    MyGekkoValueSensorDescription(
        key="pump_working_level",
        translation_key="mygekko_heatingcircuit_pump_working_level",
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement=PERCENTAGE,
        icon="mdi:gauge",
        value_fn=lambda hc: hc.pump_working_level,
    ),
    MyGekkoValueSensorDescription(
        key="valve_opening_level",
        translation_key="mygekko_heatingcircuit_valve_opening_level",
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement=PERCENTAGE,
        icon="mdi:valve",
        value_fn=lambda hc: hc.valve_opening_level,
    ),
    MyGekkoValueSensorDescription(
        key="cooling_mode_state",
        translation_key="mygekko_heatingcircuit_cooling_mode_state",
        device_class=SensorDeviceClass.ENUM,
        options=_enum_options(HeatingCircuitCoolingModeState),
        value_fn=lambda hc: _enum_option(hc.cooling_mode_state),
    ),
    MyGekkoValueSensorDescription(
        key="state",
        translation_key="mygekko_heatingcircuit_state",
        device_class=SensorDeviceClass.ENUM,
        options=_enum_options(HeatingCircuitState),
        value_fn=lambda hc: _enum_option(hc.state),
    ),
    MyGekkoValueSensorDescription(
        key="device_model",
        translation_key="mygekko_heatingcircuit_device_model",
        device_class=SensorDeviceClass.ENUM,
        options=_enum_options(HeatingCircuitDeviceModel),
        entity_category=EntityCategory.DIAGNOSTIC,
        value_fn=lambda hc: _enum_option(hc.device_model),
    ),
)


# myGekko pre-formats the charge start into a localized, human-readable
# timestamp whose date order and separators depend on the controller's
# configured language (e.g. German "23.07.2026 14:47:23", US English
# "07/23/2026 14:47:23", ISO-like "2026-07-23 14:47:23"). We try the known
# variants; genuinely ambiguous ones (dd/mm vs mm/dd) are resolved below.
_CHARGE_START_FORMATS = (
    "%d.%m.%Y %H:%M:%S",  # de and most of continental Europe
    "%d/%m/%Y %H:%M:%S",  # it / fr / es / en-GB
    "%m/%d/%Y %H:%M:%S",  # en-US
    "%Y-%m-%d %H:%M:%S",  # ISO-like
    "%d-%m-%Y %H:%M:%S",  # nl
)


def _emobil_charge_duration_seconds(value: str | None) -> int | None:
    """Read the elapsed charge seconds from a myGekko duration string.

    Handles both "20h 50m 51s" and "20:50:51" style values by taking the
    numeric groups (locale independent) and reading the last four as days,
    hours, minutes and seconds. Returns None for missing or zero durations.
    """
    if not value:
        return None
    groups = [int(part) for part in re.findall(r"\d+", value)]
    if not groups:
        return None
    days, hours, minutes, seconds = ([0, 0, 0, 0] + groups)[-4:]
    total = ((days * 24 + hours) * 60 + minutes) * 60 + seconds
    return total or None


def _emobil_charge_start(emobil: EMobil) -> datetime | None:
    """Parse the myGekko charge start time into a timezone-aware datetime.

    myGekko reports ``chargeStartTime`` as an already-localized timestamp whose
    layout depends on the controller language. We try the known formats and,
    when more than one matches (e.g. dd/mm vs mm/dd), disambiguate using the
    elapsed ``chargeDurationTime`` as a rough anchor. Exposing the result via a
    SensorDeviceClass.TIMESTAMP sensor lets Home Assistant render the elapsed
    time natively while the stable value stays out of the logbook. Returns None
    when nothing parses, so the sensor reads "unknown" instead of raising.
    """
    value = emobil.charge_start_time
    if not value:
        return None
    value = value.strip()

    candidates: list[datetime] = []
    for fmt in _CHARGE_START_FORMATS:
        try:
            parsed = datetime.strptime(value, fmt)
        except (ValueError, TypeError):
            continue
        if parsed not in candidates:
            candidates.append(parsed)
    if not candidates:
        return None

    if len(candidates) > 1:
        duration_seconds = _emobil_charge_duration_seconds(
            emobil.charge_duration_time
        )
        if duration_seconds is not None:
            anchor = (
                dt_util.now() - timedelta(seconds=duration_seconds)
            ).replace(tzinfo=None)
            candidates.sort(key=lambda candidate: abs(candidate - anchor))

    return candidates[0].replace(tzinfo=dt_util.DEFAULT_TIME_ZONE)


EMOBIL_SENSORS: tuple[MyGekkoValueSensorDescription, ...] = (
    MyGekkoValueSensorDescription(
        key="charging_power",
        translation_key="mygekko_emobil_charging_power",
        device_class=SensorDeviceClass.POWER,
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement=UnitOfPower.KILO_WATT,
        value_fn=lambda ev: ev.current_charging_power,
    ),
    MyGekkoValueSensorDescription(
        key="charging_energy",
        translation_key="mygekko_emobil_charging_energy",
        device_class=SensorDeviceClass.ENERGY,
        state_class=SensorStateClass.TOTAL_INCREASING,
        native_unit_of_measurement=UnitOfEnergy.KILO_WATT_HOUR,
        value_fn=lambda ev: ev.current_charging_energy,
    ),
    MyGekkoValueSensorDescription(
        key="charging_current_setpoint",
        translation_key="mygekko_emobil_charging_current_setpoint",
        device_class=SensorDeviceClass.CURRENT,
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement=UnitOfElectricCurrent.AMPERE,
        value_fn=lambda ev: ev.electric_current_setpoint,
    ),
    MyGekkoValueSensorDescription(
        key="maximum_charging_power",
        translation_key="mygekko_emobil_maximum_charging_power",
        device_class=SensorDeviceClass.POWER,
        native_unit_of_measurement=UnitOfPower.KILO_WATT,
        entity_category=EntityCategory.DIAGNOSTIC,
        value_fn=lambda ev: ev.maximum_charging_power,
    ),
    MyGekkoValueSensorDescription(
        key="plugged_state",
        translation_key="mygekko_emobil_plugged_state",
        device_class=SensorDeviceClass.ENUM,
        options=_enum_options(EMobilPluggedState),
        value_fn=lambda ev: _enum_option(ev.plugged_state),
    ),
    MyGekkoValueSensorDescription(
        key="charge_state",
        translation_key="mygekko_emobil_charge_state",
        device_class=SensorDeviceClass.ENUM,
        options=_enum_options(EMobilChargeState),
        value_fn=lambda ev: _enum_option(ev.charge_state),
    ),
    MyGekkoValueSensorDescription(
        key="charge_request_state",
        translation_key="mygekko_emobil_charge_request_state",
        device_class=SensorDeviceClass.ENUM,
        options=_enum_options(EMobilChargeRequestState),
        entity_category=EntityCategory.DIAGNOSTIC,
        value_fn=lambda ev: _enum_option(ev.charge_request_state),
    ),
    MyGekkoValueSensorDescription(
        key="charge_start_time",
        translation_key="mygekko_emobil_charge_start_time",
        device_class=SensorDeviceClass.TIMESTAMP,
        icon="mdi:clock-start",
        value_fn=_emobil_charge_start,
    ),
    MyGekkoValueSensorDescription(
        key="charge_user",
        translation_key="mygekko_emobil_charge_user",
        icon="mdi:account",
        value_fn=lambda ev: ev.charge_user_name,
    ),
    MyGekkoValueSensorDescription(
        key="charge_user_index",
        translation_key="mygekko_emobil_charge_user_index",
        entity_category=EntityCategory.DIAGNOSTIC,
        value_fn=lambda ev: ev.charge_user_index,
    ),
)


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

    meteo: Meteo = coordinator.api.get_meteo()
    async_add_devices(
        [
            MyGekkoMeteoRainSensor(coordinator, meteo),
            MyGekkoMeteoTwilightSensor(coordinator, meteo),
            MyGekkoMeteoBrightnessSensor(coordinator, meteo),
            MyGekkoMeteoBrightnessWestSensor(coordinator, meteo),
            MyGekkoMeteoBrightnessEastSensor(coordinator, meteo),
            MyGekkoMeteoHumiditySensor(coordinator, meteo),
            MyGekkoMeteoWindSensor(coordinator, meteo),
            MyGekkoMeteoTemperatureSensor(coordinator, meteo),
        ]
    )

    door_inter_coms: DoorInterCom = coordinator.api.get_door_inter_coms()
    for door_inter_com in door_inter_coms:
        async_add_devices(
            [
                MyGekkoDoorInterComConnectionState(coordinator, door_inter_com),
                MyGekkoDoorInterComSoundMode(coordinator, door_inter_com),
                MyGekkoDoorInterComMissedCalls(coordinator, door_inter_com),

            ]
        )

    energy_managers: list[EnergyManager] = coordinator.api.get_energy_managers()
    for energy_manager in energy_managers:
        async_add_devices(
            MyGekkoValueSensor(
                coordinator, energy_manager, "energy_manager", description
            )
            for description in ENERGY_MANAGER_SENSORS
        )

    heating_circuits: list[HeatingCircuit] = coordinator.api.get_heating_circuits()
    for heating_circuit in heating_circuits:
        async_add_devices(
            MyGekkoValueSensor(
                coordinator, heating_circuit, "heating_circuits", description
            )
            for description in HEATING_CIRCUIT_SENSORS
        )

    emobils: list[EMobil] = coordinator.api.get_emobils()
    for emobil in emobils:
        async_add_devices(
            MyGekkoValueSensor(coordinator, emobil, "emobils", description)
            for description in EMOBIL_SENSORS
        )


class MyGekkoAlarmsLogicsSensor(MyGekkoControllerEntity, SensorEntity):
    """mygekko AlarmsLogics Sensor class."""

    # AlarmsLogic values are always numeric (see PyMyGekko AlarmsLogic.value).
    # Marking them as a measurement makes them proper numeric sensors and keeps
    # their frequent value changes out of the logbook.
    _attr_state_class = SensorStateClass.MEASUREMENT

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


class MyGekkoMeteoRainSensor(MyGekkoEntity, SensorEntity):
    """mygekko Meteo Rain class."""

    _attr_native_unit_of_measurement = UnitOfVolumeFlowRate.LITERS_PER_MINUTE
    _attr_icon = "mdi:weather-rainy"

    def __init__(self, coordinator, meteo: Meteo):
        """Initialize a MyGekko meteo rain sensor."""
        super().__init__(coordinator, meteo, "meteo", "Rain")
        self._meteo = meteo
        self.entity_description = SENSORS["rain"]
        self._attr_translation_key = "mygekko_meteo_rain"

    @property
    def native_value(self):
        """Return the state of the sensor."""
        data = self._meteo.sensor_data.get("rain", None)
        return float(data) / 60 if data else None  # rain im MyGekko is in l/h


class MyGekkoMeteoTwilightSensor(MyGekkoEntity, SensorEntity):
    """mygekko Meteo Twilight class."""

    _attr_native_unit_of_measurement = LIGHT_LUX
    _attr_icon = "mdi:weather-sunset"

    def __init__(self, coordinator, meteo: Meteo):
        """Initialize a MyGekko meteo rain sensor."""
        super().__init__(coordinator, meteo, "meteo", "Twilight")
        self._meteo = meteo
        self.entity_description = SENSORS["light"]
        self._attr_translation_key = "mygekko_meteo_twilight"

    @property
    def native_value(self):
        """Return the state of the sensor."""
        data = self._meteo.sensor_data.get("twilight", None)
        return float(data) if data else None


class MyGekkoMeteoBrightnessSensor(MyGekkoEntity, SensorEntity):
    """mygekko Meteo Brightness class."""

    _attr_native_unit_of_measurement = LIGHT_LUX
    _attr_icon = "mdi:brightness-5"

    def __init__(self, coordinator, meteo: Meteo):
        """Initialize a MyGekko meteo rain sensor."""
        super().__init__(coordinator, meteo, "meteo", "Brightness")
        self._meteo = meteo
        self.entity_description = SENSORS["light"]
        self._attr_translation_key = "mygekko_meteo_brightness"

    @property
    def native_value(self):
        """Return the state of the sensor."""
        data = self._meteo.sensor_data.get("brightness", None)
        return float(data) * 1000 if data else None  # brightness im MyGekko is in klx


class MyGekkoMeteoBrightnessWestSensor(MyGekkoEntity, SensorEntity):
    """mygekko Meteo Brightness class."""

    _attr_native_unit_of_measurement = LIGHT_LUX
    _attr_icon = "mdi:brightness-5"

    def __init__(self, coordinator, meteo: Meteo):
        """Initialize a MyGekko meteo brightness sensor."""
        super().__init__(coordinator, meteo, "meteo", "Brightness West")
        self._meteo = meteo
        self.entity_description = SENSORS["light"]
        self._attr_translation_key = "mygekko_meteo_brightness_west"

    @property
    def native_value(self):
        """Return the state of the sensor."""
        data = self._meteo.sensor_data.get("brightnessw", None)
        return float(data) * 1000 if data else None  # brightness im MyGekko is in klx


class MyGekkoMeteoBrightnessEastSensor(MyGekkoEntity, SensorEntity):
    """mygekko Meteo Brightness east class."""

    _attr_native_unit_of_measurement = LIGHT_LUX
    _attr_icon = "mdi:brightness-5"

    def __init__(self, coordinator, meteo: Meteo):
        """Initialize a MyGekko meteo brightness sensor."""
        super().__init__(coordinator, meteo, "meteo", "Brightness East")
        self._meteo = meteo
        self.entity_description = SENSORS["light"]
        self._attr_translation_key = "mygekko_meteo_brightness_east"

    @property
    def native_value(self):
        """Return the state of the sensor."""
        data = self._meteo.sensor_data.get("brightnesso", None)
        return float(data) * 1000 if data else None  # brightness im MyGekko is in klx


class MyGekkoMeteoHumiditySensor(MyGekkoEntity, SensorEntity):
    """mygekko Meteo humidity class."""

    _attr_native_unit_of_measurement = PERCENTAGE
    _attr_icon = "mdi:cloud-percent"

    def __init__(self, coordinator, meteo: Meteo):
        """Initialize a MyGekko meteo humidity sensor."""
        super().__init__(coordinator, meteo, "meteo", "Humidity")
        self._meteo = meteo
        self.entity_description = SENSORS["humidity"]
        self._attr_translation_key = "mygekko_meteo_humidity"

    @property
    def native_value(self):
        """Return the state of the sensor."""
        data = self._meteo.sensor_data.get("humidity", None)
        return float(data) if data else None


class MyGekkoMeteoWindSensor(MyGekkoEntity, SensorEntity):
    """mygekko Meteo wind class."""

    _attr_native_unit_of_measurement = UnitOfSpeed.METERS_PER_SECOND
    _attr_icon = "mdi:weather-windy"

    def __init__(self, coordinator, meteo: Meteo):
        """Initialize a MyGekko meteo wind sensor."""
        super().__init__(coordinator, meteo, "meteo", "Wind")
        self._meteo = meteo
        self.entity_description = SENSORS["wind"]
        self._attr_translation_key = "mygekko_meteo_wind"

    @property
    def native_value(self):
        """Return the state of the sensor."""
        data = self._meteo.sensor_data.get("wind", None)
        return float(data) if data else None


class MyGekkoMeteoTemperatureSensor(MyGekkoEntity, SensorEntity):
    """mygekko Meteo Temperature class."""

    _attr_native_unit_of_measurement = UnitOfTemperature.CELSIUS
    _attr_icon = "mdi:thermometer"

    def __init__(self, coordinator, meteo: Meteo):
        """Initialize a MyGekko meteo Temperature sensor."""
        super().__init__(coordinator, meteo, "meteo", "Temperature")
        self._meteo = meteo
        self.entity_description = SENSORS["temperature"]
        self._attr_translation_key = "mygekko_meteo_temperature"

    @property
    def native_value(self):
        """Return the state of the sensor."""
        data = self._meteo.sensor_data.get("temperature", None)
        return float(data) if data else None


class MyGekkoDoorInterComConnectionState(MyGekkoEntity, SensorEntity):
    """mygekko DoorInterCom Connection State class."""

    STATE_MAP = {
        -6: "error_processing",
        -5: "error_authorization",
        -4 : "voip_not_active",
        -3: "error_fav_check",
        -2: "error_provisioning",
        -1: "error_connection",
        0: "not_set_up",
        1: "ok"
    }

    _attr_device_class = SensorDeviceClass.ENUM
    _attr_icon = "mdi:connection"
    _attr_options = list(STATE_MAP.values())

    def __init__(self, coordinator, door_inter_com: DoorInterCom):
        """Initialize a  DoorInterCom Connection State sensor."""
        super().__init__(coordinator, door_inter_com, "door_inter_com", "Connection")
        self._door_inter_com = door_inter_com
        self._attr_name = "Connection"

    @property
    def native_value(self):
        """Return the state of the sensor."""
        return self.STATE_MAP.get(self._door_inter_com.connection_state, None)

    @property
    def extra_state_attributes(self):
        """Return the extra state of the sensor."""
        return {"raw_state": self._door_inter_com.connection_state}


class MyGekkoDoorInterComSoundMode(MyGekkoEntity, SensorEntity):
    """mygekko DoorInterCom Sound Mode class."""

    STATE_MAP = {
        0: "mute",
        1: "ringing"
    }

    _attr_device_class = SensorDeviceClass.ENUM
    _attr_icon = "mdi:volume-low"
    _attr_options = list(STATE_MAP.values())

    def __init__(self, coordinator, door_inter_com: DoorInterCom):
        """Initialize a  DoorInterCom Sound Mode sensor."""
        super().__init__(coordinator, door_inter_com, "door_inter_com", "Sound Mode")
        self._door_inter_com = door_inter_com
        self._attr_name = "Sound Mode"

    @property
    def native_value(self):
        """Return the state of the sensor."""
        return self.STATE_MAP.get(self._door_inter_com.connection_state, None)

    @property
    def extra_state_attributes(self):
        """Return the extra state of the sensor."""
        return {"raw_state": self._door_inter_com.connection_state}


class MyGekkoDoorInterComMissedCalls(MyGekkoEntity, SensorEntity):
    """mygekko DoorInterCom Missed Calls class."""

    _attr_icon = "mdi:call-missed"

    def __init__(self, coordinator, door_inter_com: DoorInterCom):
        """Initialize a  DoorInterCom Missed Calls sensor."""
        super().__init__(coordinator, door_inter_com, "door_inter_com", "Missed Calls")
        self._door_inter_com = door_inter_com
        self._attr_name = "Missed Calls"

    @property
    def native_value(self):
        """Return the state of the sensor."""
        return self._door_inter_com.missed_calls


class MyGekkoValueSensor(MyGekkoEntity, SensorEntity):
    """mygekko sensor backed by a resource property via the description value_fn."""

    entity_description: MyGekkoValueSensorDescription

    def __init__(
        self,
        coordinator,
        resource,
        entity_prefix: str,
        description: MyGekkoValueSensorDescription,
    ):
        """Initialize a MyGekko value sensor."""
        super().__init__(coordinator, resource, entity_prefix, description.key)
        self._resource = resource
        self.entity_description = description

    @property
    def native_value(self):
        """Return the state of the sensor."""
        return self.entity_description.value_fn(self._resource)
