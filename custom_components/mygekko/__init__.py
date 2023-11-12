"""
Custom integration to integrate MyGekko with Home Assistant.

For more details about this integration, please refer to
https://github.com/stephanu/mygekko
"""
import asyncio
import logging
from datetime import timedelta

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import Config
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryNotReady
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator
from homeassistant.helpers.update_coordinator import UpdateFailed
from PyMyGekko import MyGekkoApiClient

from .const import CONF_APIKEY
from .const import CONF_GEKKOID
from .const import CONF_USERNAME
from .const import DOMAIN
from .const import PLATFORMS
from .const import STARTUP_MESSAGE

SCAN_INTERVAL = timedelta(seconds=30)

_LOGGER: logging.Logger = logging.getLogger(__package__)


async def async_setup(hass: HomeAssistant, config: Config):
    """Set up this integration using YAML is not supported."""
    return True


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry):
    """Set up this integration using UI."""
    if hass.data.get(DOMAIN) is None:
        hass.data.setdefault(DOMAIN, {})
        _LOGGER.info(STARTUP_MESSAGE)

    print("Testlog: async_setup_entry")

    username = entry.data.get(CONF_USERNAME)
    apikey = entry.data.get(CONF_APIKEY)
    gekkoid = entry.data.get(CONF_GEKKOID)

    session = async_get_clientsession(hass)

    print("Testlog: async_setup_entry: MyGekkoApiClient creation")
    client = MyGekkoApiClient(username, apikey, gekkoid, session)

    print("Testlog: async_setup_entry: MyGekkoDataUpdateCoordinator creation")
    coordinator = MyGekkoDataUpdateCoordinator(hass, client=client)
    print("Testlog: async_setup_entry: MyGekkoDataUpdateCoordinator async_refresh")
    await coordinator.async_refresh()

    if not coordinator.last_update_success:
        print("Testlog: async_setup_entry: ConfigEntryNotReady")
        raise ConfigEntryNotReady

    hass.data[DOMAIN][entry.entry_id] = coordinator

    for platform in PLATFORMS:
        if entry.options.get(platform, True):
            coordinator.platforms.append(platform)
            hass.async_add_job(
                hass.config_entries.async_forward_entry_setup(entry, platform)
            )

    entry.add_update_listener(async_reload_entry)
    return True


class MyGekkoDataUpdateCoordinator(DataUpdateCoordinator):
    """Class to manage fetching data from the API."""

    def __init__(
        self,
        hass: HomeAssistant,
        client: MyGekkoApiClient,
    ) -> None:
        """Initialize."""
        self.api = client
        self.platforms = []

        super().__init__(hass, _LOGGER, name=DOMAIN, update_interval=SCAN_INTERVAL)

    async def _async_update_data(self):
        """Update data via library."""
        print("Testlog: _async_update_data ")
        try:
            return await self.api.read_data()
        except Exception as exception:
            print("Testlog: _async_update_data failed", exception)
            raise UpdateFailed() from exception


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Handle removal of an entry."""
    coordinator = hass.data[DOMAIN][entry.entry_id]
    unloaded = all(
        await asyncio.gather(
            *[
                hass.config_entries.async_forward_entry_unload(entry, platform)
                for platform in PLATFORMS
                if platform in coordinator.platforms
            ]
        )
    )
    if unloaded:
        hass.data[DOMAIN].pop(entry.entry_id)

    return unloaded


async def async_reload_entry(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Reload config entry."""
    await async_unload_entry(hass, entry)
    await async_setup_entry(hass, entry)
