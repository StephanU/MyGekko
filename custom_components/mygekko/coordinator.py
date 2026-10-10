"""Data Update Coordinator for the MyGekko integration."""
import asyncio
import logging
import time
from datetime import timedelta

from aiohttp import ClientError
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_API_KEY
from homeassistant.const import CONF_IP_ADDRESS
from homeassistant.const import CONF_PASSWORD
from homeassistant.const import CONF_USERNAME
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryAuthFailed
from homeassistant.exceptions import ConfigEntryError
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers import issue_registry as ir
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.debounce import Debouncer
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator
from homeassistant.helpers.update_coordinator import UpdateFailed
from .api import MyGekkoDemoModeClient
from .api import MyGekkoLocalApiClient
from .api import MyGekkoQueryApiClient
from .api import MyGekkoError
from .api import MyGekkoForbidden
from .api import MyGekkoTooManyRequests

from .const import CONF_CONNECTION_DEMO_MODE
from .const import CONF_CONNECTION_LOCAL
from .const import CONF_CONNECTION_MY_GEKKO_CLOUD
from .const import CONF_CONNECTION_TYPE
from .const import CONF_GEKKOID
from .const import CONF_SCAN_INTERVAL
from .const import DEFAULT_SCAN_INTERVAL
from .const import DOMAIN


SCAN_INTERVAL = timedelta(seconds=DEFAULT_SCAN_INTERVAL)
MAX_BACKOFF_INTERVAL = timedelta(minutes=5)
UPDATE_TIMEOUT = 40
REFRESH_COOLDOWN = 2.0
WRITE_TIMEOUT = 15
WRITE_MIN_DELAY = 0.3
# rate limited polls that are skipped silently before the entities become unavailable
MAX_SKIPPED_POLLS = 5
# rejected requests (HTTP 401/403) before the user has to log in again
MAX_AUTH_FAILURES = 3
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
        self._base_interval = timedelta(
            seconds=entry.options.get(CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL)
        )
        super().__init__(
            hass,
            _LOGGER,
            config_entry=entry,
            name=DOMAIN,
            update_interval=self._base_interval,
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
        self._skipped_polls = 0
        self._backoff_until = 0.0
        self._has_data = False
        self._auth_failures = 0
        self.controller_registry_id: str | None = None

    @property
    def base_interval(self) -> timedelta:
        """Return the configured poll interval."""
        return self._base_interval

    def _issue_id(self) -> str:
        return f"rate_limited_{self.config_entry.entry_id}"

    def _create_rate_limit_issue(self) -> None:
        """Tell the user that MyGekko limits the requests."""
        ir.async_create_issue(
            self.hass,
            DOMAIN,
            self._issue_id(),
            is_fixable=False,
            severity=ir.IssueSeverity.WARNING,
            translation_key="rate_limited",
            translation_placeholders={"name": self.config_entry.title},
        )

    def _clear_rate_limit_issue(self) -> None:
        ir.async_delete_issue(self.hass, DOMAIN, self._issue_id())

    @property
    def is_backing_off(self) -> bool:
        """Return whether polls are currently skipped because of the rate limit."""
        return self._has_data and time.monotonic() < self._backoff_until

    async def _async_update_data(self):
        """Update data via the MyGekko API.

        When MyGekko answers with HTTP 429 (rate limit) this update is skipped:
        the entities keep their last values, the poll interval is increased and
        refreshes requested in the meantime are dropped. Only if the rate limit
        persists for several polls the entities are set to unavailable.
        """
        if self.is_backing_off:
            _LOGGER.debug("Skipping update, MyGekko rate limit backoff is active")
            return self.data

        _LOGGER.debug("_async_update_data")
        try:
            async with asyncio.timeout(UPDATE_TIMEOUT):
                result = await self.api.read_data()
        except MyGekkoTooManyRequests as exception:
            current = self.update_interval or self._base_interval
            self.update_interval = min(
                current * 2, max(MAX_BACKOFF_INTERVAL, self._base_interval)
            )
            self._backoff_until = time.monotonic() + self.update_interval.total_seconds()
            self._skipped_polls += 1
            # without data (e.g. at startup) there is nothing to keep: setup must retry
            if not self._has_data or self._skipped_polls > MAX_SKIPPED_POLLS:
                if self._skipped_polls > MAX_SKIPPED_POLLS:
                    self._create_rate_limit_issue()
                raise UpdateFailed(
                    f"MyGekko rate limit persists, retrying in {self.update_interval}"
                ) from exception
            _LOGGER.warning(
                "MyGekko rate limit reached, skipping this update (%s/%s), next attempt in %s",
                self._skipped_polls,
                MAX_SKIPPED_POLLS,
                self.update_interval,
            )
            return self.data
        except MyGekkoForbidden as exception:
            # a running integration tolerates a few rejections before asking the user
            self._auth_failures += 1
            if not self._has_data or self._auth_failures >= MAX_AUTH_FAILURES:
                raise ConfigEntryAuthFailed(
                    "MyGekko rejected the credentials or access"
                ) from exception
            raise UpdateFailed(
                f"MyGekko rejected the request ({self._auth_failures}/{MAX_AUTH_FAILURES})"
            ) from exception
        except TimeoutError as exception:
            raise UpdateFailed(
                f"Timeout after {UPDATE_TIMEOUT}s while fetching MyGekko data"
            ) from exception
        except Exception as exception:
            raise UpdateFailed(
                f"Error fetching MyGekko data: {type(exception).__name__}: {exception}"
            ) from exception

        if self._skipped_polls or self.update_interval != self._base_interval:
            _LOGGER.info("MyGekko API reachable again, restoring update interval")
        self._has_data = True
        self._auth_failures = 0
        self._skipped_polls = 0
        self._backoff_until = 0.0
        self.update_interval = self._base_interval
        self._clear_rate_limit_issue()
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
