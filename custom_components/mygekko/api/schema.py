"""Declarative description of the MyGekko resource types.

The MyGekko status document reports every device as a `sumstate` string with
semicolon separated values. A `ResourceSpec` names those values in order, so the
generic parser in `store.py` can handle all device types.
"""
from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class ResourceSpec:
    """Describes how one MyGekko resource type is parsed."""

    # key of the resource type in the API documents, e.g. "lights"
    kind: str
    # path prefix used when writing commands, e.g. "/lights/"
    prefix: str
    # names of the sumstate values in order
    fields: tuple[str, ...] = ()
    # alternative field order for legacy hardware (Slide), if it differs
    legacy_fields: tuple[str, ...] | None = None
    # groups (keys starting with "group") are read with these fields; empty = no groups
    group_fields: tuple[str, ...] = ()
    # additional attributes copied from the resources document
    resource_attrs: tuple[str, ...] = ()

    def fields_for(self, hardware: str) -> tuple[str, ...]:
        """Return the sumstate field order for the given hardware."""
        if hardware == "legacy" and self.legacy_fields is not None:
            return self.legacy_fields
        return self.fields

    def accepts(self, key: str) -> bool:
        """Return whether a device key belongs to this resource type."""
        return key.startswith("item") or (
            bool(self.group_fields) and key.startswith("group")
        )


ACCESS_DOORS = ResourceSpec(
    "accessdoors",
    "/accessdoors/",
    (
        "accessControllerActionState",
        "elementInfo",
        "accessState",
        "gateRuntimeLevel",
        "accessType",
    ),
)
ACTIONS = ResourceSpec(
    "actions",
    "/actions/",
    ("currentState", "startConditionState", "elementInfo"),
    legacy_fields=("currentState", "elementInfo"),
)
ALARMS_LOGICS = ResourceSpec("alarms_logics", "/alarms_logics/", ("currentValue",))
BLINDS = ResourceSpec(
    "blinds",
    "/blinds/",
    ("currentState", "positionLevel", "rotationLevel", "elementInfo", "rotationRange"),
    group_fields=("currentState",),
)
CAMS = ResourceSpec(
    "cams",
    "/cams/",
    ("newRecordsAvailableState",),
    resource_attrs=("imagepath", "streampath"),
)
CLOCKS = ResourceSpec(
    "clocks", "/clocks/", ("currentState", "startConditionState", "elementInfo")
)
DOOR_INTER_COMS = ResourceSpec(
    "door_intercom",
    "/door_intercom/",
    (
        "soundMode",
        "actionOnRingState",
        "connectionState",
        "missedCallsValue",
        "lastMissedCallDate",
    ),
    resource_attrs=("imagepath", "streampath"),
)
EMOBILS = ResourceSpec(
    "emobils",
    "/emobils/",
    (
        "pluggedState",
        "chargeState",
        "chargeRequestState",
        "currentChargingPowerValue",
        "maximumChargingPowerValue",
        "chargingPowerSetPointValue",
        "electricCurrentSetPointValue",
        "chargeUserName",
        "chargeDurationTime",
        "currentChargingEnergyValue",
        "elementInfo",
        "chargeStartTime",
        "chargeUserIndex",
    ),
)
ENERGY_COSTS = ResourceSpec("energycosts", "/energycosts/")
ENERGY_MANAGERS = ResourceSpec(
    "energymanager",
    "/energymanager/",
    (
        "elementInfo",
        "gridMeterState",
        "solarPanelState",
        "batteryState",
        "gridMeterCurrentPowerValue",
        "currentPowerExportedToGridValue",
        "currentPowerFromSolarPanelsValue",
        "currentPowerFromBatteryValue",
        "currentPowerChargingBatteryValue",
        "currentHomePowerConsumptionValue",
        "currentAlternativePowerConsupmtionValue",
        "totalDailyImportedEnergyFromGridValue",
        "totalDailyExportedEnergyToGridValue",
        "totalDailyEnergyFromSolarPanelsValue",
        "totalDailyEnergyFromBatteryValue",
        "totalDailyEneryChargingBatteryValue",
        "totalDailyHomeEnergyConsumptionValue",
        "loadSheddingState",
        "EMSState",
        "batteryModel",
        "batterySoCLevel",
        "EMSEnabled",
        "maximumPowerConsumptionFromGridValue",
        "maximumPowerExportToGridValue",
        "maximumPowerSolarPanelsValue",
        "maximumPowerBatteryValue",
    ),
)
HEATING_CIRCUITS = ResourceSpec(
    "heatingcircuits",
    "/heatingcircuits/",
    (
        "deviceModel",
        "flowTemperatureValue",
        "returnFlowTemperatureValue",
        "dewPointValue",
        "pumpWorkingLevel",
        "coolingModeState",
        "flowTemperatureSetPointValue",
        "valveOpeningLevel",
        "elementInfo",
        "currentState",
    ),
)
HOT_WATER_SYSTEMS = ResourceSpec(
    "hotwater_systems",
    "/hotwater_systems/",
    (
        "type",
        "cooling",
        "setpointTemp",
        "topTemp",
        "bottomTemp",
        "collectorTemp",
        "state",
        "elementInfo",
    ),
)
LIGHTS = ResourceSpec(
    "lights",
    "/lights/",
    ("currentState", "dimLevel", "rgbColor", "tunableWhiteLevel", "elementInfo"),
    group_fields=("currentState",),
)
LOADS = ResourceSpec("loads", "/loads/", ("currentState", "elementInfo"))
ROOM_TEMPS = ResourceSpec(
    "roomtemps",
    "/roomtemps/",
    (
        "temperatureValue",
        "temperatureSetPointValue",
        "valveOpeningLevel",
        "workingMode",
        "Reserved",
        "temperatureAdjustmentValue",
        "coolingModeState",
        "elementInfo",
        "relativeHumidityLevel",
        "airQualityLevel",
        "floorTemperatureValue",
    ),
    # legacy hardware does not report humidity, air quality and floor temperature
    legacy_fields=(
        "temperatureValue",
        "temperatureSetPointValue",
        "valveOpeningLevel",
        "workingMode",
        "Reserved",
        "temperatureAdjustmentValue",
        "coolingModeState",
        "elementInfo",
    ),
)
_VENT_COMMON = (
    "workingLevel",
    "deviceModel",
    "workingMode",
    "bypassState",
    "maximumWorkingLevel",
    "relativeHumidityLevel",
)
VENTS = ResourceSpec(
    "vents",
    "/vents/",
    _VENT_COMMON
    + (
        "airQualityLevel",
        "co2Value",
        "supplyAirTemperatureValue",
        "exhaustAirTemperatureValue",
        "outsideAirTemperatureValue",
        "outgoingAirTemperatureValue",
        "supplyAirWorkingLevel",
        "exhaustAirWorkingLevel",
        "elementInfo",
        "subWorkingMode",
        "coolingModeState",
        "dehumidModeState",
        "bypassMode",
    ),
    # legacy hardware reports co2 before the air quality
    legacy_fields=_VENT_COMMON
    + (
        "co2Value",
        "airQualityLevel",
        "supplyAirTemperatureValue",
        "exhaustAirTemperatureValue",
        "outsideAirTemperatureValue",
        "outgoingAirTemperatureValue",
        "supplyAirWorkingLevel",
        "exhaustAirWorkingLevel",
        "elementInfo",
    ),
)

HEATING_SYSTEMS = ResourceSpec(
    "heatingsystems",
    "/heatingsystems/",
    (
        "deviceModel",
        "coolingModeState",
        "flowTemperatureValue",
        "flowTemperatureSetPointValue",
        "currentState",
        "elementInfo",
    ),
)
ALARM_SYSTEMS = ResourceSpec(
    "alarmsystem",
    "/alarmsystem/",
    (
        "alarmState",
        "zone1DeviceStatus",
        "zone1SharpState",
        "zone1AlarmState",
        "zone2DeviceStatus",
        "zone2SharpState",
        "zone2AlarmState",
        "deviceModel",
    ),
    resource_attrs=("zone1", "zone2"),
)
MULTIROOMS = ResourceSpec(
    "multirooms",
    "/multirooms/",
    (
        "playerCurrentState",
        "currentVolumeLevel",
        "currentPlayingTime",
        "currentAudioTitle",
        "currentPlaylistIndex",
    )
    + tuple(f"playlist{index}Name" for index in range(16))
    + ("currentSongIndex",),
)
SMS_EMAILS = ResourceSpec("smsemail", "/smsemail/", ("currentState",))
TRENDS = ResourceSpec(
    "trends",
    "/trends/",
    tuple(
        f"variable{number}{field}"
        for number in range(1, 5)
        for field in ("State", "Type", "Name", "Value", "Unit")
    )
    + ("elementInfo",),
)

# Human readable device type, used as model of the devices in Home Assistant.
LABELS: dict[str, str] = {
    "accessdoors": "Access door",
    "alarmsystem": "Alarm system",
    "heatingsystems": "Heating system",
    "multirooms": "Multiroom audio",
    "smsemail": "SMS / e-mail",
    "trends": "Trend",
    "actions": "Action",
    "alarms_logics": "Alarm / logic",
    "blinds": "Blind",
    "cams": "Camera",
    "clocks": "Clock",
    "door_intercom": "Door intercom",
    "emobils": "E-mobility",
    "energycosts": "Energy meter",
    "energymanager": "Energy manager",
    "heatingcircuits": "Heating circuit",
    "hotwater_systems": "Hot water system",
    "lights": "Light",
    "loads": "Load",
    "roomtemps": "Room temperature",
    "vents": "Ventilation",
}

# All device resource types in the order they are exposed.
SPECS: tuple[ResourceSpec, ...] = (
    ACCESS_DOORS,
    ACTIONS,
    ALARMS_LOGICS,
    BLINDS,
    CAMS,
    CLOCKS,
    DOOR_INTER_COMS,
    EMOBILS,
    ENERGY_COSTS,
    ENERGY_MANAGERS,
    HEATING_CIRCUITS,
    HOT_WATER_SYSTEMS,
    LIGHTS,
    LOADS,
    ROOM_TEMPS,
    VENTS,
    HEATING_SYSTEMS,
    ALARM_SYSTEMS,
    MULTIROOMS,
    SMS_EMAILS,
    TRENDS,
)
