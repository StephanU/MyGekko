"""Adds config flow for MyGekko."""
import logging

import homeassistant.helpers.config_validation as cv
import voluptuous as vol
from aiohttp import ClientConnectorError
from homeassistant import config_entries
from homeassistant.const import CONF_API_KEY
from homeassistant.const import CONF_IP_ADDRESS
from homeassistant.const import CONF_PASSWORD
from homeassistant.const import CONF_USERNAME
from homeassistant.helpers.aiohttp_client import async_create_clientsession
from PyMyGekko import MyGekkoLocalApiClient
from PyMyGekko import MyGekkoQueryApiClient
from PyMyGekko.data_provider import MyGekkoError

from .const import CONF_CONNECTION_DEMO_MODE
from .const import CONF_CONNECTION_DEMO_MODE_LABEL
from .const import CONF_CONNECTION_LOCAL
from .const import CONF_CONNECTION_LOCAL_LABEL
from .const import CONF_CONNECTION_MY_GEKKO_CLOUD
from .const import CONF_CONNECTION_MY_GEKKO_CLOUD_LABEL
from .const import CONF_CONNECTION_TYPE
from .const import CONF_GEKKOID
from .const import DOMAIN

_LOGGER: logging.Logger = logging.getLogger(__name__)

CONNECTION_SCHEMA = vol.Schema(
    {
        vol.Required(
            CONF_CONNECTION_TYPE, default=CONF_CONNECTION_MY_GEKKO_CLOUD
        ): vol.In(
            {
                CONF_CONNECTION_MY_GEKKO_CLOUD: CONF_CONNECTION_MY_GEKKO_CLOUD_LABEL,
                CONF_CONNECTION_LOCAL: CONF_CONNECTION_LOCAL_LABEL,
                CONF_CONNECTION_DEMO_MODE: CONF_CONNECTION_DEMO_MODE_LABEL,
            }
        )
    }
)

CLOUD_CONNECTION_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_USERNAME): cv.string,
        vol.Required(CONF_API_KEY): cv.string,
        vol.Required(CONF_GEKKOID): cv.string,
    }
)

LOCAL_CONNECTION_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_IP_ADDRESS): cv.string,
        vol.Required(CONF_USERNAME): cv.string,
        vol.Required(CONF_PASSWORD): cv.string,
    }
)


class MyGekkoFlowHandler(config_entries.ConfigFlow, domain=DOMAIN):
    """Config flow for mygekko."""

    VERSION = 3
    CONNECTION_CLASS = config_entries.CONN_CLASS_CLOUD_POLL

    def __init__(self):
        """Initialize."""
        self._errors = {}

    async def async_step_user(self, user_input=None):
        """Handle a flow initialized by the user."""
        self._errors = {}
        _LOGGER.debug("Config flow async_step_user %s", user_input)

        # Uncomment the next 2 lines if only a single instance of the integration is allowed:
        # if self._async_current_entries():
        #     return self.async_abort(reason="single_instance_allowed")

        return await self.async_step_connection_selection(user_input)

    async def async_step_connection_selection(self, user_input):
        """Show the configuration form to edit location data."""
        _LOGGER.debug("Config flow async_step_connection_selection %s", user_input)

        if user_input is not None:
            connection_type = user_input[CONF_CONNECTION_TYPE]

            if connection_type == CONF_CONNECTION_MY_GEKKO_CLOUD:
                return await self.async_step_connection_mygekko_cloud(user_input)

            if connection_type == CONF_CONNECTION_LOCAL:
                return await self.async_step_connection_local(user_input)

            if connection_type == CONF_CONNECTION_DEMO_MODE:
                return self.async_create_entry(
                    title=CONF_CONNECTION_DEMO_MODE_LABEL, data=user_input
                )

        return self.async_show_form(
            step_id="connection_selection",
            data_schema=CONNECTION_SCHEMA,
            errors=self._errors,
            last_step=False,
        )

    async def async_step_connection_mygekko_cloud(self, user_input):
        """Show the configuration form to edit location data."""
        _LOGGER.debug("Config flow async_step_connection_mygekko_cloud %s", user_input)

        if user_input is not None:
            if (
                CONF_USERNAME in user_input
                and CONF_API_KEY in user_input
                and CONF_GEKKOID in user_input
            ):
                valid = await self._test_credentials_cloud_mygekko(
                    user_input[CONF_USERNAME],
                    user_input[CONF_API_KEY],
                    user_input[CONF_GEKKOID],
                )
                if valid:
                    user_input[CONF_CONNECTION_TYPE] = CONF_CONNECTION_MY_GEKKO_CLOUD
                    return self.async_create_entry(
                        title=user_input[CONF_USERNAME], data=user_input
                    )
                else:
                    self._errors["base"] = "auth_cloud"

        return self.async_show_form(
            step_id="connection_mygekko_cloud",
            data_schema=CLOUD_CONNECTION_SCHEMA,
            errors=self._errors,
        )

    async def async_step_connection_local(self, user_input):
        """Show the configuration form to edit location data."""
        _LOGGER.debug("Config flow async_step_connection_local")

        if user_input is not None:
            if (
                CONF_IP_ADDRESS in user_input
                and CONF_USERNAME in user_input
                and CONF_PASSWORD in user_input
            ):
                valid = await self._test_credentials_local_mygekko(
                    user_input[CONF_IP_ADDRESS],
                    user_input[CONF_USERNAME],
                    user_input[CONF_PASSWORD],
                )
                if valid:
                    user_input[CONF_CONNECTION_TYPE] = CONF_CONNECTION_LOCAL
                    return self.async_create_entry(
                        title=user_input[CONF_USERNAME], data=user_input
                    )
                else:
                    self._errors["base"] = "auth_local"

        return self.async_show_form(
            step_id="connection_local",
            data_schema=LOCAL_CONNECTION_SCHEMA,
            errors=self._errors,
        )

    async def _test_credentials_cloud_mygekko(self, username, apikey, gekkoid):
        """Return true if credentials is valid."""
        try:
            session = async_create_clientsession(self.hass)
            client = MyGekkoQueryApiClient(username, apikey, gekkoid, session)
            await client.try_connect()
            return True
        except ClientConnectorError:
            _LOGGER.error("ClientConnectorError")
        except MyGekkoError:
            _LOGGER.error("MyGekkoError")
        return False

    async def _test_credentials_local_mygekko(self, ip_address, username, password):
        """Return true if credentials is valid."""
        try:
            session = async_create_clientsession(self.hass)
            client = MyGekkoLocalApiClient(username, password, session, ip_address)
            await client.try_connect()
            return True
        except ClientConnectorError:
            _LOGGER.error("ClientConnectorError")
        except MyGekkoError:
            _LOGGER.error("MyGekkoError")

        return False
