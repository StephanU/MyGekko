"""Constants for MyGekko."""
# Base component constants
NAME = "MyGekko"
MANUFACTURER = "myGEKKO | Ekon GmbH"
DOMAIN = "mygekko"
DOMAIN_DATA = f"{DOMAIN}_data"
VERSION = "1.3.0"

ATTRIBUTION = "Data provided by http://jsonplaceholder.typicode.com/"
ISSUE_URL = "https://github.com/stephanu/mygekko/issues"


# Platforms
ALARM_CONTROL_PANEL = "alarm_control_panel"
BINARY_SENSOR = "binary_sensor"
SENSOR = "sensor"
COVER = "cover"
LIGHT = "light"
CLIMATE = "climate"
SWITCH = "switch"
SCENE = "scene"
WATER_HEATER = "water_heater"
BUTTON = "button"
SELECT = "select"
CAMERA = "camera"
NUMBER = "number"
PLATFORMS = [
    ALARM_CONTROL_PANEL,
    BINARY_SENSOR,
    COVER,
    LIGHT,
    CLIMATE,
    SWITCH,
    SCENE,
    WATER_HEATER,
    SENSOR,
    BUTTON,
    SELECT,
    CAMERA,
    NUMBER,
]


# Configuration and options
CONF_DEMO_MODE = "demo_mode"
CONF_GEKKOID = "gekkoid"
CONF_CONNECTION_TYPE = "connection_type"
CONF_CONNECTION_MY_GEKKO_CLOUD = "my_gekko_cloud"
CONF_CONNECTION_MY_GEKKO_CLOUD_LABEL = "MyGekko Plus Query API"
CONF_CONNECTION_LOCAL = "local"
CONF_CONNECTION_LOCAL_LABEL = "Local"
CONF_CONNECTION_DEMO_MODE = "demo_mode"
CONF_CONNECTION_DEMO_MODE_LABEL = "Demo Mode"
CONF_ALARM_SYSTEM_READ_ONLY = "alarm_system_read_only"

# Config subentries
SUBENTRY_TYPE_INPUT_GROUP = "input_group"
CONF_INPUT_GROUP_INDEX = "index"
CONF_SECURITY_AREA = "security_area"

# Defaults
DEFAULT_NAME = DOMAIN


STARTUP_MESSAGE = f"""
-------------------------------------------------------------------
{NAME}
Version: {VERSION}
This is a custom integration!
If you have any issues with this you need to open an issue here:
{ISSUE_URL}
-------------------------------------------------------------------
"""
