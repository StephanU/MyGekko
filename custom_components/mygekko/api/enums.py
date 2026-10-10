"""Enumerations describing the values and commands of the MyGekko API."""
from enum import IntEnum
from enum import StrEnum


class AccessDoorAccessState(IntEnum):
    """MyGekko AccessDoors Access State."""

    CLOSED = 0
    OPEN = 1


class AccessDoorAccessType(IntEnum):
    """MyGekko AccessDoors State."""

    DOOR = 0
    GATE_CONTROL = 1
    BARRIER_CONTROL = 2
    GATE_OPERATION = 3
    MYGEKKO_NET_REMOTE_DOOR = 10


class AccessDoorState(IntEnum):
    """MyGekko AccessDoors State."""

    CLOSE = 0
    OPEN = 1
    HOLD_DOWN = 2
    PARTIALLY_OPEN = 3
    PARTIALLY_HOLD_OPEN = 4


class AccessDoorCommand(IntEnum):
    """MyGekko AccessDoors Command."""

    STOP = -3
    CLOSE = -2
    LOCK = -1
    OPEN = 1
    HOLD_OPEN = 2


class AccessDoorFeature(IntEnum):
    """MyGekko AccessDoors Feature."""

    OPEN = 0


class AccessDoorElementInfo(IntEnum):
    """MyGekko AccessDoors Element Info."""

    OK = 0
    MANUAL_OFF = 1
    MANUAL_ON = 2
    LOCKED = 3
    ALARM = 4


class ActionState(IntEnum):
    """MyGekko Action State."""

    OFF = 0
    ON = 1


class ActionFeature(IntEnum):
    """MyGekko Action Features."""

    ON_OFF = 0


class BlindState(IntEnum):
    """MyGekko Blinds State."""

    HOLD_DOWN = -2
    DOWN = -1
    STOP = 0
    UP = 1
    HOLD_UP = 2


class BlindFeature(IntEnum):
    """MyGekko Blinds Feature."""

    OPEN_CLOSE_STOP = 0
    SET_POSITION = 1
    SET_TILT_POSITION = 2
    OPEN_CLOSE = 3


class BlindElementInfo(IntEnum):
    """MyGekko Blinds Element Info."""

    OK = 0
    MANUAL_OFF = 1
    MANUAL_ON = 2
    LOCKED = 3
    ALARM = 4


class CamNewRecordAvailableState(IntEnum):
    """MyGekko Cams Record Available State."""

    NO = 0
    YES = 1


class CamFeature(IntEnum):
    """MyGekko Cams Feature."""

    ON_OFF = 0
    STREAM = 1


class ClockState(IntEnum):
    """MyGekko Clocks State."""

    OFF = 0
    ON = 1
    ON_COINCIDENCE = 2


class ClockStartCondition(IntEnum):
    """MyGekko Clocks Start Condition State."""

    OFF = 0
    ON = 1


class DoorInterComFeature(IntEnum):
    """MyGekko Door Inter Com Feature."""

    ON_OFF = 0
    STREAM = 1


class DoorInterComSoundMode(IntEnum):
    """MyGekko DoorInterCom Sound Mode."""

    MUTE = 0
    RINGING = 1


class DoorInterComActionOnRingState(IntEnum):
    """MyGekko DoorInterCom Action on ring state."""

    OFF = 0
    ON = 1


class DoorInterComConnectionState(IntEnum):
    """MyGekko DoorInterCom Connection state."""

    ERROR_PROCESSING = -6
    ERROR_AUTHORIZATION = -5
    VOIP_NOT_ACTIVE = -4
    ERROR_FAV_CHECK = -3
    ERROR_PROVISIONING = -2
    ERROR_CONNECTION = -1
    NOT_SET_UP = 0
    OK = 1


class DoorInterComCommand(StrEnum):
    """MyGekko DoorInterCom Commands."""

    OPEN = 'O'
    RINGING = 'M1'
    MUTE = 'M0'
    ACTION_ON = 'A1'
    ACTION_OFF = 'A0'


class EMobilPluggedState(IntEnum):
    """MyGekko EMobils Plugged State."""

    NOT_PLUGGED = 0
    PLUGGED = 1


class EMobilChargeState(IntEnum):
    """MyGekko EMobils Charge State."""

    OFF = 0
    ON = 1
    PAUSED = 2


class EMobilChargeRequestState(IntEnum):
    """MyGekko EMobils Charge Request State."""

    OFF = 0
    ON = 1


class EnergyManagerComponentState(IntEnum):
    """MyGekko EnergyManager Component State."""

    NOT_ACTIVE = 0
    ACTIVE = 1


class EnergyManagerState(IntEnum):
    """MyGekko EnergyManager On/Off State."""

    OFF = 0
    ON = 1


class EnergyManagerEmsEnabled(IntEnum):
    """MyGekko EnergyManager EMS Enabled State."""

    DISABLED = 0
    ENABLED = 1


class EnergyManagerBatteryModel(IntEnum):
    """MyGekko EnergyManager Battery Model."""

    UNAVAILABLE = 0
    E3DC_S10 = 1
    BYD = 2
    VARTA_STORAGE = 3
    INDIVIDUAL = 4
    BY_SUN_SPEC_INVERTERS = 5


class HeatingCircuitDeviceModel(IntEnum):
    """MyGekko HeatingCircuits Device Model."""

    INDIVIDUAL = 0
    BUDERUS = 1
    STIEBEL = 2
    VAILLANT = 3


class HeatingCircuitCoolingModeState(IntEnum):
    """MyGekko HeatingCircuits Cooling Mode State."""

    OFF = 0
    ON = 1


class HeatingCircuitState(IntEnum):
    """MyGekko HeatingCircuits State."""

    OFF = 0
    ON = 1
    AUTO = 2


class HotWaterSystemState(IntEnum):
    """MyGekko HotWaterSystem state."""

    OFF = 0
    ON = 1


class HotWaterSystemFeature(IntEnum):
    """MyGekko HotWaterSystem Feature."""

    ON_OFF = 0
    TARGET_TEMPERATURE = 1
    BOTTOM_TEMPERATURE = 2
    TOP_TEMPERATURE = 3


class LightState(IntEnum):
    """MyGekko Lights State."""

    OFF = 0
    ON = 1


class LightFeature(IntEnum):
    """MyGekko Lights Feature."""

    ON_OFF = 0
    DIMMABLE = 1
    RGB_COLOR = 2


class LoadState(IntEnum):
    """MyGekko Loads State."""

    OFF = 0
    ON_IMPULSE = 1
    ON_PERMANENT = 2


class LoadFeature(IntEnum):
    """MyGekko Loads Feature."""

    ON_OFF = 0


class RoomTempsMode(IntEnum):
    """MyGekko RoomTemps Mode."""

    OFF = 1
    COMFORT = 8
    REDUCED = 16
    MANUAL = 64
    STANDBY = 256


class RoomTempsFeature(IntEnum):
    """MyGekko RoomTemps Feature."""

    TARGET_TEMPERATURE = 0
    AIR_QUALITY = 1
    HUMIDITY = 2


class VentWorkingMode(IntEnum):
    """MyGekko Vent Working Mode."""

    AUTO = 0
    MANUAL = 1
    PLUGGIT_AUTO = 2
    PLUGGIT_WEEK = 3


class VentWorkingModeZimmermann(IntEnum):
    """MyGekko Vent Working Mode for Zimmermann."""

    OFF = 0
    ECO_SUMMER = 1
    ECO_WINTER = 2
    COMFORT = 3
    STOVE = 4


class VentSubWorkingMode(IntEnum):
    """MyGekko Vent SubWorkingMode."""

    EXHAUST = 0
    EXHAUST_SUPPLY = 1
    EXHAUST_SUPPLY_HEAT_RECOVERY = 2


class VentSubWorkingModeZimmermann(IntEnum):
    """MyGekko Vent SubWorkingMode for Zimmermann."""

    MIDDLE_TEMP_OFFSET = 0
    ONLY_OFFSET = 1


class VentWorkingLevel(IntEnum):
    """MyGekko Vent Working Level."""

    OFF = 0
    LEVEL_1 = 1
    LEVEL_2 = 2
    LEVEL_3 = 3
    LEVEL_4 = 4


class VentDeviceModel(IntEnum):
    """MyGekko Vent Device Model."""

    STANDARD = 0
    PLUGGIT = 1
    ZIMMERMANN_V1 = 2
    WESTAFLEX = 3
    STIEBEL_LWZ = 4
    ZIMMERMANN_V2 = 5


class VentFeature(IntEnum):
    """MyGekko Vent Features."""

    WORKING_LEVEL = 0
    CO2 = 1
    HUMIDITY = 2
    AIR_QUALITY = 3


class VentElementInfo(IntEnum):
    """MyGekko Vent ElementInfo."""

    OK = 0
    MANUAL_OFF = 1
    MANUAL_ON = 2
    LOCKED = 3
    ALARM = 4


class VentCoolingMode(IntEnum):
    """MyGekko Vent Cooling Mode."""

    OFF = 0
    ON = 1


class VentDehumidMode(IntEnum):
    """MyGekko Vent Dehumid Mode."""

    OFF = 0
    ON = 1


class VentBypassMode(IntEnum):
    """MyGekko Vent Bypass Mode."""

    AUTO = 0
    MANUAL = 1
    SUMMER = 2


class VentBypassState(IntEnum):
    """MyGekko Vent Bypass State."""

    AUTO = 0
    MANUAL = 1
    SUMMER = 2


class HeatingSystemDeviceModel(IntEnum):
    """MyGekko heating system device model."""

    INDIVIDUAL = 0
    BUDERUS = 1
    STIEBEL = 2
    TECALOR = 3
    VAILLANT = 4


class OnOffState(IntEnum):
    """Generic off/on state."""

    OFF = 0
    ON = 1


class AlarmSystemAlarmState(IntEnum):
    """MyGekko alarm system state."""

    OK = 0
    ALARM = 1


class AlarmSystemZoneAlarmState(IntEnum):
    """MyGekko alarm system zone alarm state."""

    OK = 0
    ALARM_BUT_UNSHARP = 2
    ALARM = 3


class AlarmSystemSharpState(IntEnum):
    """MyGekko alarm system zone sharp (armed) state."""

    UNSHARP = 0
    SHARP = 1
