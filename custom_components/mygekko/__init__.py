"""Custom integration to integrate MyGekko with Home Assistant.

For more details about this integration, please refer to
https://github.com/stephanu/mygekko
"""
import logging

from .coordinator import MyGekkoConfigEntry
from .coordinator import MyGekkoDataUpdateCoordinator
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_API_KEY
from homeassistant.core import HomeAssistant

from .const import CONF_CONNECTION_MY_GEKKO_CLOUD
from .const import CONF_CONNECTION_TYPE
from .const import PLATFORMS
from .const import STARTUP_MESSAGE

_LOGGER: logging.Logger = logging.getLogger(__name__)


async def async_setup_entry(hass: HomeAssistant, entry: MyGekkoConfigEntry):
    """Set up this integration using UI."""
    _LOGGER.debug(STARTUP_MESSAGE)

    _LOGGER.debug("async_setup_entry %s", entry.data.get(CONF_CONNECTION_TYPE))

    coordinator = MyGekkoDataUpdateCoordinator(hass, entry=entry)

    await coordinator.async_config_entry_first_refresh()

    entry.runtime_data = coordinator

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    entry.async_on_unload(entry.add_update_listener(async_reload_entry))
    return True


async def async_migrate_entry(hass, config_entry: ConfigEntry):
    """Migrate old entry."""
    _LOGGER.debug("Migrating from version %s", config_entry.version)

    if config_entry.version > 3:
        return False

    if config_entry.version == 1:
        new = {**config_entry.data}
        new[CONF_CONNECTION_TYPE] = CONF_CONNECTION_MY_GEKKO_CLOUD

        hass.config_entries.async_update_entry(config_entry, data=new, version=2)

    if config_entry.version == 2:
        new = {**config_entry.data}
        if "apikey" in new:
            new[CONF_API_KEY] = new.pop("apikey")

        hass.config_entries.async_update_entry(config_entry, data=new, version=3)

    _LOGGER.debug("Migration to version %s successful", config_entry.version)

    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry):
    """Handle removal of an entry."""
    return await hass.config_entries.async_unload_platforms(entry, PLATFORMS)


async def async_reload_entry(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Reload config entry."""
    await hass.config_entries.async_reload(entry.entry_id)
