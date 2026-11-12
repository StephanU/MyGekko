"""Adds config flow for MyGekko."""
import logging

import homeassistant.helpers.config_validation as cv
import voluptuous as vol
from aiohttp import ClientConnectorError
from homeassistant import config_entries
from homeassistant.components.binary_sensor import BinarySensorDeviceClass
from homeassistant.config_entries import ConfigSubentryFlow
from homeassistant.config_entries import OptionsFlow
from homeassistant.const import CONF_API_KEY
from homeassistant.const import CONF_DEVICE_CLASS
from homeassistant.const import CONF_IP_ADDRESS
from homeassistant.const import CONF_PASSWORD
from homeassistant.const import CONF_NAME
from homeassistant.const import CONF_USERNAME
from homeassistant.core import callback
from homeassistant.helpers import selector
from homeassistant.helpers.aiohttp_client import async_create_clientsession
from PyMyGekko import MyGekkoLocalApiClient
from PyMyGekko import MyGekkoQueryApiClient
from PyMyGekko.data_provider import MyGekkoError

from .const import CONF_ALARM_SYSTEM_READ_ONLY
from .const import CONF_CONNECTION_DEMO_MODE
from .const import CONF_CONNECTION_DEMO_MODE_LABEL
from .const import CONF_CONNECTION_LOCAL
from .const import CONF_CONNECTION_LOCAL_LABEL
from .const import CONF_CONNECTION_MY_GEKKO_CLOUD
from .const import CONF_CONNECTION_MY_GEKKO_CLOUD_LABEL
from .const import CONF_CONNECTION_TYPE
from .const import CONF_GEKKOID
from .const import CONF_INPUT_GROUP_INDEX
from .const import CONF_SECURITY_AREA
from .const import DOMAIN
from .const import SUBENTRY_TYPE_INPUT_GROUP

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


ALARM_SYSTEM_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_ALARM_SYSTEM_READ_ONLY, default=False): cv.boolean,
    }
)

# Kinds of detectors an input group of the alarm panel can stand for.
INPUT_GROUP_DEVICE_CLASSES = [
    BinarySensorDeviceClass.WINDOW,
    BinarySensorDeviceClass.DOOR,
    BinarySensorDeviceClass.GARAGE_DOOR,
    BinarySensorDeviceClass.OPENING,
    BinarySensorDeviceClass.MOTION,
    BinarySensorDeviceClass.VIBRATION,
    BinarySensorDeviceClass.TAMPER,
    BinarySensorDeviceClass.SAFETY,
]


class MyGekkoFlowHandler(config_entries.ConfigFlow, domain=DOMAIN):
    """Config flow for mygekko."""

    VERSION = 4
    CONNECTION_CLASS = config_entries.CONN_CLASS_CLOUD_POLL

    def __init__(self):
        """Initialize."""
        self._errors = {}
        # Title and data of the entry, while the alarm system step is shown.
        self._pending_entry = None

    @staticmethod
    @callback
    def async_get_options_flow(config_entry):
        """Return the options flow."""
        return MyGekkoOptionsFlow()

    @classmethod
    @callback
    def async_get_supported_subentry_types(cls, config_entry):
        """Return the subentries this integration supports."""
        return {SUBENTRY_TYPE_INPUT_GROUP: InputGroupSubentryFlow}

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
                    return await self._async_finish_connection(
                        client, user_input, user_input[CONF_GEKKOID]
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
                    return await self._async_finish_connection(
                        client, user_input, user_input[CONF_IP_ADDRESS]
                    )
                else:
                    self._errors["base"] = "auth_local"

        return self.async_show_form(
            step_id="connection_local",
            data_schema=self._with_current_values(LOCAL_CONNECTION_SCHEMA, user_input),
            errors=self._errors,
        )

    async def async_step_alarm_system(self, user_input=None):
        """Ask whether Home Assistant may arm the alarm system."""
        if user_input is not None:
            return self.async_create_entry(
                **self._pending_entry,
                options={
                    CONF_ALARM_SYSTEM_READ_ONLY: user_input[CONF_ALARM_SYSTEM_READ_ONLY]
                },
            )

        return self.async_show_form(
            step_id="alarm_system", data_schema=ALARM_SYSTEM_SCHEMA
        )

    async def _async_finish_connection(self, client, data, title_fallback):
        """Store the validated connection, after the alarm system step if needed."""
        if self._is_reconfigure:
            return self._async_update_entry(data)

        # Reading the name also reads all data, which tells about the alarm system.
        gekko_name = await self._read_gekko_name(client)
        self._pending_entry = {"title": gekko_name or title_fallback, "data": data}

        if _has_alarm_system(client):
            return await self.async_step_alarm_system()

        return self.async_create_entry(**self._pending_entry)

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
        entry = self._get_reconfigure_entry()
        # Replace the data instead of merging it, so switching the connection
        # type does not leave the credentials of the previous one behind. The
        # title is left untouched, the user may have renamed the entry.
        changed = self.hass.config_entries.async_update_entry(entry, data=data)
        if not changed or not entry.update_listeners:
            # The update listener of a loaded entry reloads it after a change.
            # Otherwise reload here, so the new connection is tried right away.
            self.hass.config_entries.async_schedule_reload(entry.entry_id)
        return self.async_abort(reason="reconfigure_successful")

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


def _has_alarm_system(client) -> bool:
    """Return whether the controller mirrors an alarm system."""
    try:
        return bool(client.get_alarm_systems())
    except Exception:  # noqa: BLE001
        # Only decides whether the alarm system step is shown, which must not
        # abort a flow whose credentials already validated.
        _LOGGER.debug("Could not read the alarm system", exc_info=True)
        return False


def _get_alarm_systems(hass, entry):
    """Return the security areas of a loaded entry, empty if there are none."""
    coordinator = hass.data.get(DOMAIN, {}).get(entry.entry_id)
    if coordinator is None:
        return []
    return coordinator.api.get_alarm_systems()


class MyGekkoOptionsFlow(OptionsFlow):
    """Options of a MyGekko entry. The update listener reloads the entry."""

    async def async_step_init(self, user_input=None):
        """Manage the options."""
        if not _get_alarm_systems(self.hass, self.config_entry):
            return self.async_abort(reason="no_options")

        if user_input is not None:
            return self.async_create_entry(data={**self.config_entry.options, **user_input})

        return self.async_show_form(
            step_id="init",
            data_schema=self.add_suggested_values_to_schema(
                ALARM_SYSTEM_SCHEMA, self.config_entry.options
            ),
        )


class InputGroupSubentryFlow(ConfigSubentryFlow):
    """Add or change an input group of the alarm panel as binary sensor.

    myGEKKO reports which input groups are active but not what they are, so
    the user enters the index (as listed by the "active input groups" sensor),
    a name, the kind of detector and optionally the security area.
    """

    async def async_step_user(self, user_input=None):
        """Add an input group."""
        return await self._async_step_input_group(user_input, None)

    async def async_step_reconfigure(self, user_input=None):
        """Change an input group."""
        return await self._async_step_input_group(
            user_input, self._get_reconfigure_subentry()
        )

    async def _async_step_input_group(self, user_input, subentry):
        entry = self._get_entry()
        alarm_systems = _get_alarm_systems(self.hass, entry)
        if not alarm_systems:
            return self.async_abort(reason="no_alarm_system")

        errors = {}
        if user_input is not None:
            index = int(user_input[CONF_INPUT_GROUP_INDEX])
            taken = {
                other.data[CONF_INPUT_GROUP_INDEX]
                for other in entry.get_subentries_of_type(SUBENTRY_TYPE_INPUT_GROUP)
                if subentry is None or other.subentry_id != subentry.subentry_id
            }
            if index in taken:
                errors[CONF_INPUT_GROUP_INDEX] = "input_group_already_configured"
            else:
                data = {
                    CONF_INPUT_GROUP_INDEX: index,
                    CONF_DEVICE_CLASS: user_input.get(CONF_DEVICE_CLASS),
                    CONF_SECURITY_AREA: user_input.get(CONF_SECURITY_AREA),
                }
                title = user_input[CONF_NAME]
                if subentry is None:
                    return self.async_create_entry(
                        title=title, data=data, unique_id=str(index)
                    )
                # The update listener reloads the entry.
                return self.async_update_and_abort(
                    entry,
                    subentry,
                    title=title,
                    data=data,
                    unique_id=str(index),
                )

        suggested = user_input
        if suggested is None and subentry is not None:
            suggested = {**subentry.data, CONF_NAME: subentry.title}

        input_group_count = alarm_systems[0].input_group_count or 512
        schema = vol.Schema(
            {
                vol.Required(CONF_INPUT_GROUP_INDEX): selector.NumberSelector(
                    selector.NumberSelectorConfig(
                        min=0,
                        max=input_group_count - 1,
                        step=1,
                        mode=selector.NumberSelectorMode.BOX,
                    )
                ),
                vol.Required(CONF_NAME): selector.TextSelector(),
                vol.Optional(CONF_DEVICE_CLASS): selector.SelectSelector(
                    selector.SelectSelectorConfig(
                        options=[str(cls) for cls in INPUT_GROUP_DEVICE_CLASSES],
                        mode=selector.SelectSelectorMode.DROPDOWN,
                        translation_key="input_group_device_class",
                    )
                ),
                vol.Optional(CONF_SECURITY_AREA): selector.SelectSelector(
                    selector.SelectSelectorConfig(
                        options=[
                            selector.SelectOptionDict(
                                value=alarm_system.entity_id, label=alarm_system.name
                            )
                            for alarm_system in alarm_systems
                        ],
                        mode=selector.SelectSelectorMode.DROPDOWN,
                    )
                ),
            }
        )

        return self.async_show_form(
            step_id="user" if subentry is None else "reconfigure",
            data_schema=self.add_suggested_values_to_schema(schema, suggested or {}),
            errors=errors,
        )
