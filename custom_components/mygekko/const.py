"""Constants for MyGekko."""
# Base component constants
NAME = "MyGekko"
MANUFACTURER = "myGEKKO | Ekon GmbH"
DOMAIN = "mygekko"
DOMAIN_DATA = f"{DOMAIN}_data"
VERSION = "1.5.0"

ATTRIBUTION = "Data provided by http://jsonplaceholder.typicode.com/"
ISSUE_URL = "https://github.com/stephanu/mygekko/issues"


# Platforms
SENSOR = "sensor"
COVER = "cover"
LIGHT = "light"
CLIMATE = "climate"
SWITCH = "switch"
SCENE = "scene"
WATER_HEATER = "water_heater"
BUTTON = "button"
BINARY_SENSOR = "binary_sensor"
SELECT = "select"
CAMERA = "camera"
ALARM_CONTROL_PANEL = "alarm_control_panel"
PLATFORMS = [
    ALARM_CONTROL_PANEL,
    BINARY_SENSOR,
    BUTTON,
    CAMERA,
    CLIMATE,
    COVER,
    LIGHT,
    SCENE,
    SELECT,
    SENSOR,
    SWITCH,
    WATER_HEATER,
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

# Defaults
DEFAULT_NAME = DOMAIN
CONF_SCAN_INTERVAL = "scan_interval"
CONF_USE_PAGES_AS_AREAS = "use_pages_as_areas"
CONF_SCHEME = "scheme"  # "https" (default) or "http" of a local MyGekko
DEFAULT_SCAN_INTERVAL = 30  # seconds
MIN_SCAN_INTERVAL = 10
MAX_SCAN_INTERVAL = 600


STARTUP_MESSAGE = f"""
-------------------------------------------------------------------
{NAME}
Version: {VERSION}
This is a custom integration!
If you have any issues with this you need to open an issue here:
{ISSUE_URL}
-------------------------------------------------------------------
"""
