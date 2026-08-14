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

    async def async_step_reconfigure(self, user_input=None):
        """Handle a flow initialized by reconfiguring an existing entry."""
        self._errors = {}
        _LOGGER.debug("Config flow async_step_reconfigure %s", user_input)

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
                if self._is_reconfigure:
                    return self._async_update_entry(user_input)

                return self.async_create_entry(
                    title=CONF_CONNECTION_DEMO_MODE_LABEL, data=user_input
                )

        return self.async_show_form(
            step_id="connection_selection",
            data_schema=self._with_current_values(CONNECTION_SCHEMA, user_input),
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
                client = await self._test_credentials_cloud_mygekko(
                    user_input[CONF_USERNAME],
                    user_input[CONF_API_KEY],
                    user_input[CONF_GEKKOID],
                )
                if client is not None:
                    user_input[CONF_CONNECTION_TYPE] = CONF_CONNECTION_MY_GEKKO_CLOUD
                    if self._is_reconfigure:
                        return self._async_update_entry(user_input)

                    gekko_name = await self._read_gekko_name(client)
                    return self.async_create_entry(
                        title=gekko_name or user_input[CONF_GEKKOID],
                        data=user_input,
                    )
                else:
                    self._errors["base"] = "auth_cloud"

        return self.async_show_form(
            step_id="connection_mygekko_cloud",
            data_schema=self._with_current_values(CLOUD_CONNECTION_SCHEMA, user_input),
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
                client = await self._test_credentials_local_mygekko(
                    user_input[CONF_IP_ADDRESS],
                    user_input[CONF_USERNAME],
                    user_input[CONF_PASSWORD],
                )
                if client is not None:
                    user_input[CONF_CONNECTION_TYPE] = CONF_CONNECTION_LOCAL
                    if self._is_reconfigure:
                        return self._async_update_entry(user_input)

                    gekko_name = await self._read_gekko_name(client)
                    return self.async_create_entry(
                        title=gekko_name or user_input[CONF_IP_ADDRESS],
                        data=user_input,
                    )
                else:
                    self._errors["base"] = "auth_local"

        return self.async_show_form(
            step_id="connection_local",
            data_schema=self._with_current_values(LOCAL_CONNECTION_SCHEMA, user_input),
            errors=self._errors,
        )

    @property
    def _is_reconfigure(self):
        """Return whether an existing entry is being reconfigured."""
        return self.source == config_entries.SOURCE_RECONFIGURE

    def _with_current_values(self, schema, user_input=None):
        """Prefill a form with the data of the entry that is being reconfigured.

        What the user just submitted takes precedence over what is stored, so a
        form redisplayed after a validation error keeps their input instead of
        resetting it to the values they are trying to replace.
        """
        if not self._is_reconfigure:
            return schema

        return self.add_suggested_values_to_schema(
            schema, {**self._get_reconfigure_entry().data, **(user_input or {})}
        )

    def _async_update_entry(self, data):
        """Update the entry that is being reconfigured and finish the flow."""
        # Replace the data instead of merging it, so switching the connection
        # type does not leave the credentials of the previous one behind. The
        # title is left untouched, the user may have renamed the entry.
        return self.async_update_reload_and_abort(
            self._get_reconfigure_entry(), data=data
        )

    async def _test_credentials_cloud_mygekko(self, username, apikey, gekkoid):
        """Return the client if the credentials are valid, None otherwise."""
        try:
            session = async_create_clientsession(self.hass)
            client = MyGekkoQueryApiClient(username, apikey, gekkoid, session)
            await client.try_connect()
            return client
        except ClientConnectorError:
            _LOGGER.exception("ClientConnectorError")
        except MyGekkoError:
            _LOGGER.exception("MyGekkoError")
        return None

    async def _test_credentials_local_mygekko(self, ip_address, username, password):
        """Return the client if the credentials are valid, None otherwise."""
        try:
            session = async_create_clientsession(self.hass, verify_ssl=False)
            client = MyGekkoLocalApiClient(username, password, session, ip_address)
            await client.try_connect()
            return client
        except ClientConnectorError:
            _LOGGER.exception("ClientConnectorError")
        except MyGekkoError:
            _LOGGER.exception("MyGekkoError")

        return None

    async def _read_gekko_name(self, client):
        """Read the gekko friendly name, None if it cannot be determined."""
        try:
            await client.read_data()
            globals_network = client.get_globals_network()
            if globals_network:
                return globals_network.get("gekkoname")
        except Exception:  # noqa: BLE001
            # The name is only used as the entry title and has a fallback, so no
            # failure here may abort a flow whose credentials already validated.
            # get_globals_network() indexes the payload without guarding, which
            # raises KeyError on an unexpected response.
            _LOGGER.debug("Could not determine the gekko name", exc_info=True)
        return None
