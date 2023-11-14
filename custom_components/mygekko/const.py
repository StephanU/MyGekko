"""Constants for MyGekko."""
# Base component constants
NAME = "MyGekko"
DOMAIN = "mygekko"
DOMAIN_DATA = f"{DOMAIN}_data"
VERSION = "0.0.24"

ATTRIBUTION = "Data provided by http://jsonplaceholder.typicode.com/"
ISSUE_URL = "https://github.com/stephanu/mygekko/issues"

# Icons
ICON = "mdi:format-quote-close"


# Platforms
SENSOR = "sensor"
COVER = "cover"
LIGHT = "light"
CLIMATE = "climate"
PLATFORMS = [COVER, LIGHT, CLIMATE]


# Configuration and options
CONF_DEMO_MODE = "demo_mode"
CONF_USERNAME = "username"
CONF_APIKEY = "apikey"
CONF_GEKKOID = "gekkoid"

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
