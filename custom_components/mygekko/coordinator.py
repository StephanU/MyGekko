"""Data Update Coordinator for the MyGekko integration."""
import asyncio
import logging
import time
from datetime import datetime
from datetime import timedelta

from aiohttp import ClientError
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_API_KEY
from homeassistant.const import CONF_IP_ADDRESS
from homeassistant.const import CONF_PASSWORD
from homeassistant.const import CONF_USERNAME
from homeassistant.core import HomeAssistant
from homeassistant.core import callback
from homeassistant.exceptions import ConfigEntryAuthFailed
from homeassistant.exceptions import ConfigEntryError
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers import issue_registry as ir
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.debounce import Debouncer
from homeassistant.helpers.event import async_call_later
from homeassistant.helpers.storage import Store
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator
from homeassistant.helpers.update_coordinator import UpdateFailed
from homeassistant.util import dt as dt_util
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
from .const import CONF_SCHEME
from .const import DEFAULT_SCAN_INTERVAL
from .const import DOMAIN


SCAN_INTERVAL = timedelta(seconds=DEFAULT_SCAN_INTERVAL)
# after HTTP 429 (rate limit) no request is sent for this time
RATE_LIMIT_PAUSE = timedelta(minutes=4)
# a rate limit lasting this long is reported as repair issue (the values are kept)
RATE_LIMIT_ISSUE_AFTER = timedelta(minutes=30)
# other errors (timeout, network, server) keep the last values for this time
ERROR_GRACE = timedelta(minutes=15)
UPDATE_TIMEOUT = 40
REFRESH_COOLDOWN = 2.0
WRITE_TIMEOUT = 15
WRITE_MIN_DELAY = 0.3
# rejected requests (HTTP 401/403) before the user has to log in again
MAX_AUTH_FAILURES = 3
# a command delayed by the rate limit is tried after this many pauses at most
MAX_QUEUED_ATTEMPTS = 3
# the last state is saved at most this often (and when Home Assistant stops)
CACHE_SAVE_DELAY = 300
CACHE_VERSION = 1

API_STATE_OK = "ok"
API_STATE_RATE_LIMITED = "rate_limited"
API_STATE_ERROR = "error"

_LOGGER: logging.Logger = logging.getLogger(__name__)

MyGekkoConfigEntry = ConfigEntry["MyGekkoDataUpdateCoordinator"]


class MyGekkoDataUpdateCoordinator(DataUpdateCoordinator):
    """Class to manage fetching data from the API.

    The last state read from MyGekko is always kept: a rate limit (HTTP 429)
    pauses all requests for RATE_LIMIT_PAUSE, other errors are tolerated for
    ERROR_GRACE, and the state is saved so that a restart during a rate limit
    or an outage starts with the last known values instead of unavailable ones.
    """

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
            client = MyGekkoLocalApiClient(
                username,
                password,
                session,
                ip_address,
                scheme=entry.data.get(CONF_SCHEME, "https"),
            )

        if entry.data.get(CONF_CONNECTION_TYPE) == CONF_CONNECTION_DEMO_MODE:
            client = MyGekkoDemoModeClient()

        if client is None:
            _LOGGER.exception(
                "Creating MyGekkoDataUpdateCoordinator failed: client is None"
            )
            raise ConfigEntryError

        self.api = client
        self._write_lock = asyncio.Lock()
        # commands kept during a rate limit pause: key -> (method, args, attempts)
        self._queued: dict[tuple, tuple] = {}
        self._unsub_queued = None
        self._cache: Store = Store(
            hass, CACHE_VERSION, f"{DOMAIN}.{entry.entry_id}", private=True
        )
        self._cached: dict | None = None
        # a rate limit pause outlives a retried setup (new coordinator, same entry)
        self._pauses: dict[str, float] = hass.data.setdefault(DOMAIN, {}).setdefault(
            "rate_limit_pauses", {}
        )
        self._backoff_until = self._pauses.get(entry.entry_id, 0.0)
        self._has_data = False
        self._auth_failures = 0
        self._rate_limited_since: datetime | None = None
        self._failing_since: datetime | None = None
        self.rate_limited_until: datetime | None = None
        self.last_success: datetime | None = None
        self.api_state: str = API_STATE_OK
        self.controller_registry_id: str | None = None

    @property
    def base_interval(self) -> timedelta:
        """Return the configured poll interval."""
        return self._base_interval

    @property
    def is_backing_off(self) -> bool:
        """Return whether polls are currently skipped because of the rate limit."""
        return self._has_data and time.monotonic() < self._backoff_until

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

    # --- saved state ---------------------------------------------------------------

    async def async_load_cache(self) -> None:
        """Load the state saved before the last restart."""
        try:
            cached = await self._cache.async_load()
        except Exception:  # noqa: BLE001
            _LOGGER.warning("The saved MyGekko state could not be read")
            return
        if (
            isinstance(cached, dict)
            and isinstance(cached.get("resources"), dict)
            and isinstance(cached.get("status"), dict)
        ):
            self._cached = cached

    def _cache_data(self) -> dict:
        return {
            "resources": self.api.last_resources,
            "status": self.api.last_status,
            "saved_at": self.last_success.isoformat() if self.last_success else None,
            "rate_limited_until": (
                self.rate_limited_until.isoformat() if self.rate_limited_until else None
            ),
        }

    def _save_cache(self) -> None:
        if self.api.last_resources is not None and self.api.last_status is not None:
            self._cache.async_delay_save(self._cache_data, CACHE_SAVE_DELAY)

    async def async_remove_cache(self) -> None:
        """Delete the saved state (the config entry was removed)."""
        await self._cache.async_remove()

    def _restore_cache(self) -> bool:
        """Use the saved state when MyGekko cannot be read at startup."""
        if self._has_data or self._cached is None:
            return False
        self.api.restore(self._cached["resources"], self._cached["status"])
        saved_at = dt_util.parse_datetime(self._cached.get("saved_at") or "")
        self.last_success = saved_at
        self._cached = None
        self._has_data = True
        _LOGGER.warning(
            "MyGekko cannot be read right now, using the state saved at %s", saved_at
        )
        return True

    def _saved_rate_limit_pause(self) -> float:
        """Return the seconds left of a rate limit pause from before the restart."""
        if self._cached is None:
            return 0.0
        until = dt_util.parse_datetime(self._cached.get("rate_limited_until") or "")
        if until is None:
            return 0.0
        return max(0.0, (until - dt_util.utcnow()).total_seconds())

    # --- polling -------------------------------------------------------------------

    def _pause_for_rate_limit(self, seconds: float | None = None) -> None:
        """Stop sending requests for the rate limit pause."""
        pause = max(RATE_LIMIT_PAUSE, self._base_interval)
        if seconds is not None:
            pause = timedelta(seconds=seconds)
        now = dt_util.utcnow()
        self._backoff_until = time.monotonic() + pause.total_seconds()
        self._pauses[self.config_entry.entry_id] = self._backoff_until
        self.rate_limited_until = now + pause
        self._rate_limited_since = self._rate_limited_since or now
        self.api_state = API_STATE_RATE_LIMITED
        self.update_interval = max(pause, self._base_interval)
        if now - self._rate_limited_since >= RATE_LIMIT_ISSUE_AFTER:
            self._create_rate_limit_issue()

    async def _async_update_data(self):
        """Update data via the MyGekko API.

        HTTP 429 (rate limit) pauses the requests for RATE_LIMIT_PAUSE, the
        entities keep their last values for as long as the rate limit lasts.
        Other errors keep the last values for ERROR_GRACE.
        """
        if self.is_backing_off:
            _LOGGER.debug("Skipping update, MyGekko rate limit pause is active")
            return self.data

        # a rate limit pause from before the restart is respected
        remaining = self._saved_rate_limit_pause()
        if remaining and self._restore_cache():
            self._pause_for_rate_limit(remaining)
            return self.data

        if not self._has_data and time.monotonic() < self._backoff_until:
            # no request during the pause, also not while the setup is retried
            if self._restore_cache():
                self.api_state = API_STATE_RATE_LIMITED
                return self.data
            raise UpdateFailed(
                "MyGekko rate limit pause is active, waiting before the next request"
            )

        _LOGGER.debug("_async_update_data")
        try:
            async with asyncio.timeout(UPDATE_TIMEOUT):
                result = await self.api.read_data()
        except MyGekkoTooManyRequests as exception:
            self._restore_cache()
            if not self._has_data:
                # nothing to keep (first start without saved state): setup retries
                self._pause_for_rate_limit()
                raise UpdateFailed(
                    f"MyGekko rate limit reached, retrying in {self.update_interval}"
                ) from exception
            self._pause_for_rate_limit()
            self._save_cache()
            _LOGGER.warning(
                "MyGekko rate limit reached (HTTP 429), keeping the last state and "
                "pausing requests until %s",
                dt_util.as_local(self.rate_limited_until).strftime("%H:%M:%S"),
            )
            return self.data
        except MyGekkoForbidden as exception:
            # a running integration tolerates a few rejections before asking the user
            self._auth_failures += 1
            if not self._has_data or self._auth_failures >= MAX_AUTH_FAILURES:
                raise ConfigEntryAuthFailed(
                    "MyGekko rejected the credentials or access"
                ) from exception
            self.api_state = API_STATE_ERROR
            _LOGGER.warning(
                "MyGekko rejected the request (%s/%s), keeping the last state",
                self._auth_failures,
                MAX_AUTH_FAILURES,
            )
            return self.data
        except Exception as exception:  # noqa: BLE001
            if isinstance(exception, TimeoutError):
                message = f"Timeout after {UPDATE_TIMEOUT}s while fetching MyGekko data"
            else:
                message = (
                    f"Error fetching MyGekko data: {type(exception).__name__}: {exception}"
                )
            self._restore_cache()
            self.api_state = API_STATE_ERROR
            self._failing_since = self._failing_since or dt_util.utcnow()
            if self._within_grace():
                _LOGGER.warning("%s, keeping the last state", message)
                return self.data
            raise UpdateFailed(message) from exception

        if self.api_state != API_STATE_OK or self.update_interval != self._base_interval:
            _LOGGER.info("MyGekko API reachable again, restoring update interval")
        self._has_data = True
        self._cached = None
        self._auth_failures = 0
        self._backoff_until = 0.0
        self._rate_limited_since = None
        self._failing_since = None
        self._pauses.pop(self.config_entry.entry_id, None)
        self.rate_limited_until = None
        self.last_success = dt_util.utcnow()
        self.api_state = API_STATE_OK
        self.update_interval = self._base_interval
        self._clear_rate_limit_issue()
        self._save_cache()
        return result

    def _within_grace(self) -> bool:
        """Return whether the errors started recently enough to keep the last state."""
        if not self._has_data or self._failing_since is None:
            return False
        return dt_util.utcnow() - self._failing_since < ERROR_GRACE

    # --- commands ----------------------------------------------------------------

    @staticmethod
    def _command_key(method) -> tuple:
        """Return the key of a command: a newer command for the same target replaces it."""
        return (id(getattr(method, "__self__", method)), getattr(method, "__name__", ""))

    def _queue_command(self, method, args) -> None:
        """Keep a command until the rate limit pause is over, then send it."""
        key = self._command_key(method)
        attempts = self._queued.get(key, (None, None, 0))[2]
        self._queued[key] = (method, args, attempts)
        self._schedule_queued()
        _LOGGER.warning(
            "MyGekko rate limit: the command is sent automatically at %s",
            dt_util.as_local(self.rate_limited_until or dt_util.utcnow()).strftime(
                "%H:%M:%S"
            ),
        )

    def _schedule_queued(self) -> None:
        if self._unsub_queued is not None or not self._queued:
            return
        delay = max(0.0, self._backoff_until - time.monotonic()) + 1
        self._unsub_queued = async_call_later(self.hass, delay, self._async_send_queued)

    async def _async_send_queued(self, _now=None) -> None:
        """Send the commands kept during the rate limit pause."""
        if self._unsub_queued is not None:
            self._unsub_queued()
            self._unsub_queued = None
        if self.is_backing_off:
            self._schedule_queued()
            return
        queued, self._queued = self._queued, {}
        sent = False
        for key, (method, args, attempts) in queued.items():
            if self._backoff_until > time.monotonic():
                # rate limited again: the rest waits for the next pause to end
                self._queued[key] = (method, args, attempts)
                continue
            try:
                await self._async_send(method, args)
                sent = True
            except MyGekkoTooManyRequests:
                if attempts + 1 >= MAX_QUEUED_ATTEMPTS:
                    _LOGGER.error(
                        "MyGekko rate limit persists, a command was dropped after %s attempts",
                        MAX_QUEUED_ATTEMPTS,
                    )
                    continue
                self._queued[key] = (method, args, attempts + 1)
            except HomeAssistantError as err:
                _LOGGER.error("Sending a delayed command to MyGekko failed: %s", err)
        self._schedule_queued()
        if sent and not self.is_backing_off:
            await self.async_request_refresh()

    @callback
    def async_cancel_queued(self) -> None:
        """Drop the commands kept for later (the entry is unloaded)."""
        if self._unsub_queued is not None:
            self._unsub_queued()
            self._unsub_queued = None
        self._queued.clear()

    async def _async_send(self, method, args) -> None:
        """Send one command; HTTP 429 pauses the requests and is raised."""
        async with self._write_lock:
            try:
                async with asyncio.timeout(WRITE_TIMEOUT):
                    await method(*args)
            except MyGekkoTooManyRequests:
                self._pause_for_rate_limit()
                raise
            except TimeoutError as exception:
                raise HomeAssistantError(
                    f"Timeout while sending command to MyGekko ({WRITE_TIMEOUT}s)"
                ) from exception
            except (MyGekkoError, ClientError) as exception:
                raise HomeAssistantError(
                    f"MyGekko command failed: {type(exception).__name__}"
                ) from exception
            finally:
                await asyncio.sleep(WRITE_MIN_DELAY)

    async def async_write(self, method, *args) -> None:
        """Send a command to MyGekko.

        Commands are serialized, spaced out and followed by a (debounced) refresh.
        When MyGekko limits the requests (HTTP 429), or a rate limit pause is
        active, the command is kept and sent automatically when the pause of
        RATE_LIMIT_PAUSE is over. Other errors surface as HomeAssistantError.
        """
        if self.is_backing_off:
            self._queue_command(method, args)
            return
        try:
            await self._async_send(method, args)
        except MyGekkoTooManyRequests:
            self._queue_command(method, args)
            return
        await self.async_request_refresh()
