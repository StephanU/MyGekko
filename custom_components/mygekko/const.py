"""Constants for MyGekko."""
# Base component constants
NAME = "MyGekko"
MANUFACTURER = "myGEKKO | Ekon GmbH"
DOMAIN = "mygekko"
DOMAIN_DATA = f"{DOMAIN}_data"
VERSION = "1.2.4"

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
SELECT = "select"
CAMERA = "camera"
PLATFORMS = [COVER, LIGHT, CLIMATE, SWITCH, SCENE, WATER_HEATER, SENSOR, BUTTON, SELECT, CAMERA]


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

# Options configuration keys
CONF_SCAN_INTERVAL = "scan_interval"

# Defaults
DEFAULT_NAME = DOMAIN
DEFAULT_SCAN_INTERVAL = 30


STARTUP_MESSAGE = f"""
-------------------------------------------------------------------
{NAME}
Version: {VERSION}
This is a custom integration!
If you have any issues with this you need to open an issue here:
{ISSUE_URL}
-------------------------------------------------------------------
"""
