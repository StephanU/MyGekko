"""Constants for MyGekko tests."""

from homeassistant.const import CONF_API_KEY
from homeassistant.const import CONF_IP_ADDRESS
from homeassistant.const import CONF_PASSWORD
from homeassistant.const import CONF_USERNAME

from custom_components.mygekko.const import (
    CONF_CONNECTION_DEMO_MODE,
)
from custom_components.mygekko.const import (
    CONF_CONNECTION_LOCAL,
)
from custom_components.mygekko.const import (
    CONF_CONNECTION_MY_GEKKO_CLOUD,
)
from custom_components.mygekko.const import (
    CONF_CONNECTION_TYPE,
)
from custom_components.mygekko.const import (
    CONF_GEKKOID,
)

# Credentials as entered in the connection_mygekko_cloud step.
MOCK_CONFIG = {
    CONF_USERNAME: "test_username",
    CONF_API_KEY: "test_apikey",
    CONF_GEKKOID: "test_gekkoid",
}

# Credentials as entered in the connection_local step.
MOCK_LOCAL_CONFIG = {
    CONF_IP_ADDRESS: "192.168.1.2",
    CONF_USERNAME: "test_username",
    CONF_PASSWORD: "test_password",
}

# Config entry data, which is what the flow stores once a step succeeded.
MOCK_CLOUD_ENTRY_DATA = {
    **MOCK_CONFIG,
    CONF_CONNECTION_TYPE: CONF_CONNECTION_MY_GEKKO_CLOUD,
}
MOCK_LOCAL_ENTRY_DATA = {
    **MOCK_LOCAL_CONFIG,
    CONF_CONNECTION_TYPE: CONF_CONNECTION_LOCAL,
}
MOCK_DEMO_ENTRY_DATA = {CONF_CONNECTION_TYPE: CONF_CONNECTION_DEMO_MODE}
