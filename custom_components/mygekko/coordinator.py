"""Data Update Coordinator for the MyGekko integration."""
import asyncio
import logging
from datetime import timedelta

from aiohttp import ClientError
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_API_KEY
from homeassistant.const import CONF_IP_ADDRESS
from homeassistant.const import CONF_PASSWORD
from homeassistant.const import CONF_USERNAME
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryError
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.debounce import Debouncer
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator
from homeassistant.helpers.update_coordinator import UpdateFailed
from .pymygekko import MyGekkoDemoModeClient
from .pymygekko import MyGekkoLocalApiClient
from .pymygekko import MyGekkoQueryApiClient
from .pymygekko.data_provider import MyGekkoError
from .pymygekko.data_provider import MyGekkoForbidden
from .pymygekko.data_provider import MyGekkoTooManyRequests

from .const import CONF_CONNECTION_DEMO_MODE
from .const import CONF_CONNECTION_LOCAL
from .const import CONF_CONNECTION_MY_GEKKO_CLOUD
from .const import CONF_CONNECTION_TYPE
from .const import CONF_GEKKOID
from .const import DOMAIN


SCAN_INTERVAL = timedelta(seconds=30)
MAX_BACKOFF_INTERVAL = timedelta(minutes=5)
UPDATE_TIMEOUT = 25
REFRESH_COOLDOWN = 2.0
WRITE_TIMEOUT = 15
WRITE_MIN_DELAY = 0.3
WRITE_RETRIES = 3
WRITE_RETRY_DELAY = 2

_LOGGER: logging.Logger = logging.getLogger(__name__)

MyGekkoConfigEntry = ConfigEntry["MyGekkoDataUpdateCoordinator"]


class MyGekkoDataUpdateCoordinator(DataUpdateCoordinator):
    """Class to manage fetching data from the API."""

    def __init__(
        self,
        hass: HomeAssistant,
        entry: ConfigEntry,
    ) -> None:
        """Initialize."""
        super().__init__(
            hass,
            _LOGGER,
            config_entry=entry,
            name=DOMAIN,
            update_interval=SCAN_INTERVAL,
            request_refresh_debouncer=Debouncer(
                hass, _LOGGER, cooldown=REFRESH_COOLDOWN, immediate=False
            ),
        )

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
        self._write_lock = asyncio.Lock()

    async def _async_update_data(self):
        """Update data via library."""
        _LOGGER.debug("_async_update_data")
        try:
            async with asyncio.timeout(UPDATE_TIMEOUT):
                result = await self.api.read_data()
        except MyGekkoTooManyRequests as exception:
            # Rate limited by MyGekko: back off instead of hammering the API.
            current = self.update_interval or SCAN_INTERVAL
            self.update_interval = min(current * 2, MAX_BACKOFF_INTERVAL)
            raise UpdateFailed(
                f"MyGekko rate limit reached, retrying in {self.update_interval}"
            ) from exception
        except MyGekkoForbidden as exception:
            raise UpdateFailed(
                "MyGekko rejected the credentials or access (403 Forbidden)"
            ) from exception
        except TimeoutError as exception:
            raise UpdateFailed(
                f"Timeout after {UPDATE_TIMEOUT}s while fetching MyGekko data"
            ) from exception
        except Exception as exception:
            raise UpdateFailed(
                f"Error fetching MyGekko data: {type(exception).__name__}: {exception}"
            ) from exception

        if self.update_interval != SCAN_INTERVAL:
            _LOGGER.info("MyGekko API reachable again, restoring update interval")
            self.update_interval = SCAN_INTERVAL
        return result

    async def async_write(self, method, *args) -> None:
        """Send a command to MyGekko.

        Commands are serialized, spaced out, retried on rate limiting and
        followed by a (debounced) refresh. Errors surface as HomeAssistantError.
        """
        async with self._write_lock:
            for attempt in range(1, WRITE_RETRIES + 1):
                try:
                    async with asyncio.timeout(WRITE_TIMEOUT):
                        await method(*args)
                    break
                except MyGekkoTooManyRequests as exception:
                    if attempt == WRITE_RETRIES:
                        raise HomeAssistantError(
                            "MyGekko rate limit reached, command was not executed"
                        ) from exception
                    await asyncio.sleep(WRITE_RETRY_DELAY * attempt)
                except TimeoutError as exception:
                    raise HomeAssistantError(
                        f"Timeout while sending command to MyGekko ({WRITE_TIMEOUT}s)"
                    ) from exception
                except (MyGekkoError, ClientError) as exception:
                    raise HomeAssistantError(
                        f"MyGekko command failed: {type(exception).__name__}"
                    ) from exception
            await asyncio.sleep(WRITE_MIN_DELAY)
        await self.async_request_refresh()
