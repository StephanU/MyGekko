"""Constants for MyGekko tests."""

from homeassistant.const import CONF_API_KEY
from homeassistant.const import CONF_USERNAME

from custom_components.mygekko.const import (
    CONF_GEKKOID,
)

MOCK_CONFIG = {
    CONF_USERNAME: "test_username",
    CONF_API_KEY: "test_apikey",
    CONF_GEKKOID: "test_gekkoid",
}
