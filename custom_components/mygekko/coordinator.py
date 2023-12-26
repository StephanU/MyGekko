"""Data Update Coordinator for the MyGekko integration."""
import logging
from datetime import timedelta

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_API_KEY
from homeassistant.const import CONF_IP_ADDRESS
from homeassistant.const import CONF_PASSWORD
from homeassistant.const import CONF_USERNAME
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryError
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator
from homeassistant.helpers.update_coordinator import UpdateFailed
from PyMyGekko import MyGekkoDemoModeClient
from PyMyGekko import MyGekkoLocalApiClient
from PyMyGekko import MyGekkoQueryApiClient

from .const import CONF_CONNECTION_DEMO_MODE
from .const import CONF_CONNECTION_LOCAL
from .const import CONF_CONNECTION_MY_GEKKO_CLOUD
from .const import CONF_CONNECTION_TYPE
from .const import CONF_GEKKOID
from .const import DOMAIN


SCAN_INTERVAL = timedelta(seconds=30)

_LOGGER: logging.Logger = logging.getLogger(__name__)


class MyGekkoDataUpdateCoordinator(DataUpdateCoordinator):
    """Class to manage fetching data from the API."""

    def __init__(
        self,
        hass: HomeAssistant,
        entry: ConfigEntry,
    ) -> None:
        """Initialize."""
        self.platforms = []

        super().__init__(hass, _LOGGER, name=DOMAIN, update_interval=SCAN_INTERVAL)

        client = None

        if entry.data.get(CONF_CONNECTION_TYPE) == CONF_CONNECTION_MY_GEKKO_CLOUD:
            username = entry.data.get(CONF_USERNAME)
            apikey = entry.data.get(CONF_API_KEY)
            gekkoid = entry.data.get(CONF_GEKKOID)

            session = async_get_clientsession(hass)
            client = MyGekkoQueryApiClient(username, apikey, gekkoid, session)

        if entry.data.get(CONF_CONNECTION_TYPE) == CONF_CONNECTION_LOCAL:
            username = entry.data.get(CONF_USERNAME)
            password = entry.data.get(CONF_PASSWORD)
            ip_address = entry.data.get(CONF_IP_ADDRESS)

            session = async_get_clientsession(hass, verify_ssl=False)
            client = MyGekkoLocalApiClient(username, password, session, ip_address)

        if entry.data.get(CONF_CONNECTION_TYPE) == CONF_CONNECTION_DEMO_MODE:
            client = MyGekkoDemoModeClient()

        if client is None:
            _LOGGER.exception(
                "Creating MyGekkoDataUpdateCoordinator failed: client is None"
            )
            raise ConfigEntryError

        self.api = client

    async def _async_update_data(self):
        """Update data via library."""
        _LOGGER.debug("_async_update_data ")
        try:
            return await self.api.read_data()
        except Exception as exception:
            _LOGGER.exception("_async_update_data failed")
            raise UpdateFailed() from exception
