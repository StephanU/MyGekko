"""Custom integration to integrate MyGekko with Home Assistant.

For more details about this integration, please refer to
https://github.com/stephanu/mygekko
"""
import asyncio
import logging

from custom_components.mygekko.coordinator import MyGekkoDataUpdateCoordinator
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_API_KEY
from homeassistant.core import Config
from homeassistant.core import HomeAssistant

from .const import CONF_CONNECTION_MY_GEKKO_CLOUD
from .const import CONF_CONNECTION_TYPE
from .const import DOMAIN
from .const import PLATFORMS
from .const import STARTUP_MESSAGE

_LOGGER: logging.Logger = logging.getLogger(__name__)


async def async_setup(_hass: HomeAssistant, _config: Config):
    """Set up this integration using YAML is not supported."""
    return True


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry):
    """Set up this integration using UI."""
    if hass.data.get(DOMAIN) is None:
        hass.data.setdefault(DOMAIN, {})
        _LOGGER.info(STARTUP_MESSAGE)

    _LOGGER.debug("async_setup_entry %s", entry.data.get(CONF_CONNECTION_TYPE))

    coordinator = MyGekkoDataUpdateCoordinator(hass, entry=entry)

    await coordinator.async_config_entry_first_refresh()

    hass.data[DOMAIN][entry.entry_id] = coordinator

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    entry.add_update_listener(async_reload_entry)
    return True


async def async_migrate_entry(hass, config_entry: ConfigEntry):
    """Migrate old entry."""
    _LOGGER.debug("Migrating from version %s", config_entry.version)

    if config_entry.version == 1:
        new = {**config_entry.data}
        new[CONF_CONNECTION_TYPE] = CONF_CONNECTION_MY_GEKKO_CLOUD

        config_entry.version = 2
        hass.config_entries.async_update_entry(config_entry, data=new)

    if config_entry.version == 2:
        new = {**config_entry.data}
        new[CONF_API_KEY] = new["apikey"]
        new.pop("apikey")

        config_entry.version = 3
        hass.config_entries.async_update_entry(config_entry, data=new)

    _LOGGER.debug("Migration to version %s successful", config_entry.version)

    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry):
    # Unload platforms
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)

    # Clean stored data
    if unload_ok:
        hass.data[DOMAIN].pop(entry.entry_id)

    return unload_ok


async def async_reload_entry(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Reload config entry."""
    await async_unload_entry(hass, entry)
    await async_setup_entry(hass, entry)
