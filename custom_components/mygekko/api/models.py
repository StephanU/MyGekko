"""Device models of the MyGekko resource types.

Models are thin views on the data of the `ResourceStore`. Reading a property
never raises: missing or unknown values are reported as `None`.
"""
from __future__ import annotations

from collections.abc import Callable
from datetime import datetime
from enum import Enum
from math import ceil
from typing import TYPE_CHECKING
from typing import Any

from . import schema
from .enums import (
    AccessDoorAccessState,
    AccessDoorAccessType,
    AccessDoorCommand,
    AccessDoorElementInfo,
    AccessDoorFeature,
    ActionFeature,
    ActionState,
    BlindElementInfo,
    BlindFeature,
    BlindState,
    CamFeature,
    ClockStartCondition,
    ClockState,
    DoorInterComActionOnRingState,
    DoorInterComCommand,
    DoorInterComConnectionState,
    DoorInterComFeature,
    DoorInterComSoundMode,
    EMobilChargeRequestState,
    EMobilChargeState,
    EMobilPluggedState,
    EnergyManagerBatteryModel,
    EnergyManagerComponentState,
    EnergyManagerEmsEnabled,
    EnergyManagerState,
    HeatingCircuitCoolingModeState,
    HeatingCircuitDeviceModel,
    HeatingCircuitState,
    HotWaterSystemFeature,
    HotWaterSystemState,
    LightFeature,
    LightState,
    LoadFeature,
    LoadState,
    RoomTempsFeature,
    RoomTempsMode,
    VentBypassMode,
    VentBypassState,
    VentCoolingMode,
    VentDehumidMode,
    VentDeviceModel,
    VentElementInfo,
    VentFeature,
    VentSubWorkingMode,
    VentSubWorkingModeZimmermann,
    VentWorkingLevel,
    VentWorkingMode,
    VentWorkingModeZimmermann,
)

if TYPE_CHECKING:
    from .client import MyGekkoClient

_ZIMMERMANN = (VentDeviceModel.ZIMMERMANN_V1, VentDeviceModel.ZIMMERMANN_V2)


def _to_enum(enum: type[Enum]) -> Callable[[str], Any]:
    return lambda raw: enum(int(float(raw)))


def _field(name: str, convert: Callable[[str], Any] = str) -> property:
    """Create a read only property for the raw value `name`, converted by `convert`."""
    return property(lambda self: self._read(name, convert))


def _float(name: str) -> property:
    return _field(name, float)


def _int(name: str) -> property:
    return _field(name, lambda raw: int(float(raw)))


def _enum(name: str, enum: type[Enum]) -> property:
    return _field(name, _to_enum(enum))


class ColorUtilities:
    """Conversion between the decimal color of MyGekko and RGB tuples."""

    @staticmethod
    def decimal_to_rgb(decimal_rgb_color: int) -> tuple[int, int, int]:
        """Convert a decimal color to a rgb tuple."""
        return (
            (decimal_rgb_color >> 16) & 255,
            (decimal_rgb_color >> 8) & 255,
            decimal_rgb_color & 255,
        )

    @staticmethod
    def rgb_to_decimal(rgb: tuple[int, int, int]) -> int:
        """Convert a rgb tuple to a decimal color."""
        return (rgb[0] << 16) + (rgb[1] << 8) + rgb[2]


class ReadOnlyEntity:
    """Base class of everything that has an id and a name."""

    def __init__(self, entity_id: str, name: str) -> None:
        """Initialize the entity."""
        self.entity_id = entity_id
        self.name = name


class Device(ReadOnlyEntity):
    """Base class of the devices of a MyGekko resource type."""

    SPEC: schema.ResourceSpec

    def __init__(self, client: MyGekkoClient, entity_id: str, name: str) -> None:
        """Initialize the device."""
        super().__init__(entity_id, name)
        self._client = client

    @property
    def resource_path(self) -> str:
        """Return the path of this device in the MyGekko API."""
        return self.SPEC.prefix + self.entity_id

    def _value(self, field: str) -> str | None:
        return self._client.store.value(self.SPEC, self.entity_id, field)

    def _read(self, field: str, convert: Callable[[str], Any]) -> Any:
        """Return the converted value, None if it is missing or invalid."""
        raw = self._value(field)
        if raw is None:
            return None
        try:
            return convert(raw)
        except (ValueError, TypeError):
            return None

    def _features(self, rules: dict[Any, str]) -> list[Any]:
        """Return the features whose value is currently reported."""
        return [feature for feature, field in rules.items() if self._value(field)]

    async def _write(self, value: str) -> None:
        await self._client.write(self.resource_path, value)


class AccessDoor(Device):
    """Access door, gate or barrier."""

    SPEC = schema.ACCESS_DOORS

    access_state = _enum("accessState", AccessDoorAccessState)
    access_type = _enum("accessType", AccessDoorAccessType)
    element_info = _enum("elementInfo", AccessDoorElementInfo)

    @property
    def supported_features(self) -> list[AccessDoorFeature]:
        """Return the supported features."""
        return self._features({AccessDoorFeature.OPEN: "accessControllerActionState"})

    async def set_state(self, state: AccessDoorCommand) -> None:
        """Send a command to the door."""
        await self._write(str(int(state)))


class Action(Device):
    """Action (scene) of MyGekko."""

    SPEC = schema.ACTIONS

    state = _enum("currentState", ActionState)
    start_condition_state = _enum("startConditionState", ActionState)

    @property
    def supported_features(self) -> list[ActionFeature]:
        """Return the supported features."""
        return self._features({ActionFeature.ON_OFF: "currentState"})

    async def set_state(self, state: ActionState) -> None:
        """Start or stop the action."""
        await self._write(str(int(state)))


class AlarmsLogic(Device):
    """Alarm or logic value."""

    SPEC = schema.ALARMS_LOGICS

    value = _float("currentValue")


class Blind(Device):
    """Blind, shutter or group of those."""

    SPEC = schema.BLINDS

    position = _float("positionLevel")
    tilt_position = _float("rotationLevel")
    state = _enum("currentState", BlindState)
    element_info = _enum("elementInfo", BlindElementInfo)

    @property
    def supported_features(self) -> list[BlindFeature]:
        """Return the supported features."""
        if self.entity_id.startswith("group"):
            return [BlindFeature.OPEN_CLOSE]
        return self._features(
            {
                BlindFeature.OPEN_CLOSE_STOP: "currentState",
                BlindFeature.SET_POSITION: "positionLevel",
                BlindFeature.SET_TILT_POSITION: "rotationLevel",
            }
        )

    async def set_state(self, state: BlindState) -> None:
        """Move or stop the blind."""
        await self._write(str(int(state)))

    async def set_position(self, position: float) -> None:
        """Set the position in percent (0 = open, 100 = closed)."""
        if 0 <= position <= 100.0:
            await self._write("P" + str(position))

    async def set_tilt_position(self, position: float) -> None:
        """Set the slat angle in percent."""
        if 0 <= position <= 100.0:
            await self._write("S" + str(position))


class Cam(Device):
    """Camera."""

    SPEC = schema.CAMS

    image_url = _field("imagepath")
    stream_url = _field("streampath")

    @property
    def supported_features(self) -> list[CamFeature]:
        """Return the supported features."""
        return self._features({CamFeature.STREAM: "streampath"})


class Clock(Device):
    """Time switch."""

    SPEC = schema.CLOCKS

    state = _enum("currentState", ClockState)
    start_condition = _enum("startConditionState", ClockStartCondition)

    async def set_state(self, state: ClockState) -> None:
        """Set the mode of the clock."""
        await self._write(str(int(state)))


class DoorInterCom(Device):
    """Door intercom."""

    SPEC = schema.DOOR_INTER_COMS

    image_url = _field("imagepath")
    stream_url = _field("streampath")
    sound_mode = _enum("soundMode", DoorInterComSoundMode)
    action_on_ring_state = _enum("actionOnRingState", DoorInterComActionOnRingState)
    connection_state = _enum("connectionState", DoorInterComConnectionState)
    missed_calls = _int("missedCallsValue")
    last_missed_call_date = _field(
        "lastMissedCallDate", lambda raw: datetime.strptime(raw, "%d.%m.%Y %H:%M:%S")
    )

    @property
    def supported_features(self) -> list[DoorInterComFeature]:
        """Return the supported features."""
        return self._features({DoorInterComFeature.STREAM: "streampath"})

    async def send_command(self, command: DoorInterComCommand) -> None:
        """Send a command to the intercom."""
        await self._write(str(command))


class EMobil(Device):
    """E-mobility charging station."""

    SPEC = schema.EMOBILS

    plugged_state = _enum("pluggedState", EMobilPluggedState)
    charge_state = _enum("chargeState", EMobilChargeState)
    charge_request_state = _enum("chargeRequestState", EMobilChargeRequestState)
    current_charging_power = _float("currentChargingPowerValue")
    maximum_charging_power = _float("maximumChargingPowerValue")
    charging_power_setpoint = _float("chargingPowerSetPointValue")
    electric_current_setpoint = _int("electricCurrentSetPointValue")
    charge_user_name = _field("chargeUserName")
    charge_duration_time = _field("chargeDurationTime")
    current_charging_energy = _float("currentChargingEnergyValue")
    charge_start_time = _field("chargeStartTime")
    charge_user_index = _int("chargeUserIndex")

    async def start_charge(self) -> None:
        """Start charging."""
        await self._write("1")

    async def stop_charge(self) -> None:
        """Stop charging."""
        await self._write("-1")

    async def set_charging_power_setpoint(self, power: float) -> None:
        """Set the charging power in kW."""
        await self._write("CS" + str(power))


class EnergyCost(Device):
    """Energy meter."""

    SPEC = schema.ENERGY_COSTS

    @property
    def sensor_data(self) -> dict[str, Any] | None:
        """Return the name and the decoded values of the meter."""
        return self._client.store.devices(self.SPEC).get(self.entity_id) or None


class EnergyManager(Device):
    """Energy manager (grid, solar panels and battery)."""

    SPEC = schema.ENERGY_MANAGERS

    grid_meter_state = _enum("gridMeterState", EnergyManagerComponentState)
    solar_panel_state = _enum("solarPanelState", EnergyManagerComponentState)
    battery_state = _enum("batteryState", EnergyManagerComponentState)
    grid_meter_power = _float("gridMeterCurrentPowerValue")
    power_exported_to_grid = _float("currentPowerExportedToGridValue")
    power_from_solar_panels = _float("currentPowerFromSolarPanelsValue")
    power_from_battery = _float("currentPowerFromBatteryValue")
    power_charging_battery = _float("currentPowerChargingBatteryValue")
    home_power_consumption = _float("currentHomePowerConsumptionValue")
    alternative_power_consumption = _float("currentAlternativePowerConsupmtionValue")
    daily_energy_imported_from_grid = _float("totalDailyImportedEnergyFromGridValue")
    daily_energy_exported_to_grid = _float("totalDailyExportedEnergyToGridValue")
    daily_energy_from_solar_panels = _float("totalDailyEnergyFromSolarPanelsValue")
    daily_energy_from_battery = _float("totalDailyEnergyFromBatteryValue")
    daily_energy_charging_battery = _float("totalDailyEneryChargingBatteryValue")
    daily_home_energy_consumption = _float("totalDailyHomeEnergyConsumptionValue")
    load_shedding_state = _enum("loadSheddingState", EnergyManagerState)
    ems_state = _enum("EMSState", EnergyManagerState)
    battery_model = _enum("batteryModel", EnergyManagerBatteryModel)
    battery_soc = _float("batterySoCLevel")
    ems_enabled = _enum("EMSEnabled", EnergyManagerEmsEnabled)
    max_power_consumption_from_grid = _float("maximumPowerConsumptionFromGridValue")
    max_power_export_to_grid = _float("maximumPowerExportToGridValue")
    max_power_solar_panels = _float("maximumPowerSolarPanelsValue")
    max_power_battery = _float("maximumPowerBatteryValue")


class HeatingCircuit(Device):
    """Heating circuit."""

    SPEC = schema.HEATING_CIRCUITS

    device_model = _enum("deviceModel", HeatingCircuitDeviceModel)
    flow_temperature = _float("flowTemperatureValue")
    return_flow_temperature = _float("returnFlowTemperatureValue")
    dew_point = _float("dewPointValue")
    pump_working_level = _float("pumpWorkingLevel")
    cooling_mode_state = _enum("coolingModeState", HeatingCircuitCoolingModeState)
    flow_temperature_setpoint = _float("flowTemperatureSetPointValue")
    valve_opening_level = _float("valveOpeningLevel")
    state = _enum("currentState", HeatingCircuitState)


class HotWaterSystem(Device):
    """Hot water system."""

    SPEC = schema.HOT_WATER_SYSTEMS

    state = _enum("state", HotWaterSystemState)
    target_temperature = _float("setpointTemp")
    current_temperature_top = _float("topTemp")
    current_temperature_bottom = _float("bottomTemp")

    @property
    def supported_features(self) -> list[HotWaterSystemFeature]:
        """Return the supported features."""
        return self._features(
            {
                HotWaterSystemFeature.ON_OFF: "state",
                HotWaterSystemFeature.TARGET_TEMPERATURE: "setpointTemp",
                HotWaterSystemFeature.BOTTOM_TEMPERATURE: "bottomTemp",
                HotWaterSystemFeature.TOP_TEMPERATURE: "topTemp",
            }
        )

    async def set_state(self, state: HotWaterSystemState) -> None:
        """Switch the hot water system."""
        await self._write(str(int(state)))

    async def set_target_temperature(self, target_temperature: float) -> None:
        """Set the target temperature in °C."""
        await self._write("T" + str(target_temperature))


class Light(Device):
    """Light or group of lights."""

    SPEC = schema.LIGHTS

    state = _enum("currentState", LightState)
    brightness = _field("dimLevel", lambda raw: ceil(float(raw)))
    rgb_color = _field(
        "rgbColor", lambda raw: ColorUtilities.decimal_to_rgb(int(float(raw)))
    )

    @property
    def supported_features(self) -> list[LightFeature]:
        """Return the supported features."""
        if self.entity_id.startswith("group"):
            return [LightFeature.ON_OFF]
        return self._features(
            {
                LightFeature.ON_OFF: "currentState",
                LightFeature.DIMMABLE: "dimLevel",
                LightFeature.RGB_COLOR: "rgbColor",
            }
        )

    async def set_state(self, state: LightState) -> None:
        """Switch the light."""
        await self._write(str(int(state)))

    async def set_brightness(self, brightness: int) -> None:
        """Set the brightness in percent."""
        if 0 <= brightness <= 100:
            await self._write("D" + str(brightness))

    async def set_rgb_color(self, rgb_color: tuple[int, int, int]) -> None:
        """Set the color."""
        if all(0 <= channel <= 255 for channel in rgb_color):
            await self._write("C" + str(ColorUtilities.rgb_to_decimal(rgb_color)))


class Load(Device):
    """Switchable load."""

    SPEC = schema.LOADS

    state = _enum("currentState", LoadState)

    @property
    def supported_features(self) -> list[LoadFeature]:
        """Return the supported features."""
        return self._features({LoadFeature.ON_OFF: "currentState"})

    async def set_state(self, state: LoadState) -> None:
        """Switch the load."""
        await self._write(str(int(state)))


class Meteo(ReadOnlyEntity):
    """Weather station."""

    def __init__(self, client: MyGekkoClient) -> None:
        """Initialize the weather station."""
        super().__init__("meteo", "Weather")
        self._client = client

    @property
    def sensor_data(self) -> dict[str, Any]:
        """Return the values of the weather station."""
        return self._client.store.meteo


class RoomTemp(Device):
    """Room temperature controller."""

    SPEC = schema.ROOM_TEMPS

    working_mode = _enum("workingMode", RoomTempsMode)
    current_temperature = _float("temperatureValue")
    target_temperature = _float("temperatureSetPointValue")
    humidity = _float("relativeHumidityLevel")
    air_quality = _float("airQualityLevel")

    @property
    def supported_features(self) -> list[RoomTempsFeature]:
        """Return the supported features."""
        return self._features(
            {
                RoomTempsFeature.TARGET_TEMPERATURE: "temperatureSetPointValue",
                RoomTempsFeature.HUMIDITY: "relativeHumidityLevel",
                RoomTempsFeature.AIR_QUALITY: "airQualityLevel",
            }
        )

    async def set_target_temperature(self, target_temperature: float) -> None:
        """Set the target temperature in °C."""
        await self._write("S" + str(target_temperature))

    async def set_working_mode(self, working_mode: RoomTempsMode) -> None:
        """Set the working mode."""
        await self._write("M" + str(int(working_mode)))


class Vent(Device):
    """Ventilation."""

    SPEC = schema.VENTS

    element_info = _enum("elementInfo", VentElementInfo)
    working_level = _enum("workingLevel", VentWorkingLevel)
    maximum_working_level = _enum("maximumWorkingLevel", VentWorkingLevel)
    device_model = _enum("deviceModel", VentDeviceModel)
    relative_humidity = _float("relativeHumidityLevel")
    air_quality = _float("airQualityLevel")
    co2 = _float("co2Value")
    supply_air_temperature = _float("supplyAirTemperatureValue")
    exhaust_air_temperature = _float("exhaustAirTemperatureValue")
    outside_air_temperature = _float("outsideAirTemperatureValue")
    outgoing_air_temperature = _float("outgoingAirTemperatureValue")
    supply_air_working_level = _float("supplyAirWorkingLevel")
    exhaust_air_working_level = _float("exhaustAirWorkingLevel")
    cooling_mode = _enum("coolingModeState", VentCoolingMode)
    dehumid_mode = _enum("dehumidModeState", VentDehumidMode)
    bypass_mode = _enum("bypassMode", VentBypassMode)
    bypass_state = _enum("bypassState", VentBypassState)

    @property
    def supported_features(self) -> list[VentFeature]:
        """Return the supported features."""
        return self._features(
            {
                VentFeature.WORKING_LEVEL: "workingLevel",
                VentFeature.AIR_QUALITY: "airQualityLevel",
                VentFeature.CO2: "co2Value",
                VentFeature.HUMIDITY: "relativeHumidityLevel",
            }
        )

    @property
    def working_mode(self) -> VentWorkingMode | VentWorkingModeZimmermann | None:
        """Return the working mode, its meaning depends on the device model."""
        enum = (
            VentWorkingModeZimmermann
            if self.device_model in _ZIMMERMANN
            else VentWorkingMode
        )
        return self._read("workingMode", _to_enum(enum))

    @property
    def sub_working_mode(
        self,
    ) -> VentSubWorkingMode | VentSubWorkingModeZimmermann | None:
        """Return the sub working mode, its meaning depends on the device model."""
        enum = (
            VentSubWorkingModeZimmermann
            if self.device_model in _ZIMMERMANN
            else VentSubWorkingMode
        )
        return self._read("subWorkingMode", _to_enum(enum))

    async def set_working_level(self, working_level: VentWorkingLevel) -> None:
        """Set the working level, off is sent as -1."""
        level = int(working_level)
        await self._write(str(-1 if level == VentWorkingLevel.OFF else level))

    async def set_bypass_state(self, bypass_state: VentBypassState) -> None:
        """Set the bypass state."""
        await self._write("BY" + str(int(bypass_state)))

    async def set_cooling_mode(self, cooling_mode: VentCoolingMode) -> None:
        """Switch the cooling mode."""
        await self._write("C" + str(int(cooling_mode)))

    async def set_dehumid_mode(self, dehumid_mode: VentDehumidMode) -> None:
        """Switch the dehumidification."""
        await self._write("D" + str(int(dehumid_mode)))

    async def set_working_mode(
        self, working_mode: VentWorkingMode | VentWorkingModeZimmermann
    ) -> None:
        """Set the working mode."""
        await self._write("M" + str(int(working_mode)))
