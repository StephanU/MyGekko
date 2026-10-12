"""Constants for MyGekko tests."""
from homeassistant.const import CONF_API_KEY
from homeassistant.const import CONF_IP_ADDRESS
from homeassistant.const import CONF_PASSWORD
from homeassistant.const import CONF_USERNAME

from custom_components.mygekko.const import CONF_CONNECTION_DEMO_MODE
from custom_components.mygekko.const import CONF_CONNECTION_LOCAL
from custom_components.mygekko.const import CONF_CONNECTION_MY_GEKKO_CLOUD
from custom_components.mygekko.const import CONF_CONNECTION_TYPE
from custom_components.mygekko.const import CONF_GEKKOID

DEMO_CONFIG = {CONF_CONNECTION_TYPE: CONF_CONNECTION_DEMO_MODE}
CLOUD_INPUT = {
    CONF_USERNAME: "user",
    CONF_API_KEY: "secret",
    CONF_GEKKOID: "A1B2C3",
}
CLOUD_CONFIG = {CONF_CONNECTION_TYPE: CONF_CONNECTION_MY_GEKKO_CLOUD, **CLOUD_INPUT}
LOCAL_INPUT = {
    CONF_IP_ADDRESS: "192.168.1.50",
    CONF_USERNAME: "user",
    CONF_PASSWORD: "secret",
}
LOCAL_CONFIG = {CONF_CONNECTION_TYPE: CONF_CONNECTION_LOCAL, **LOCAL_INPUT}
