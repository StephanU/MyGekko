"""Custom integration to integrate MyGekko with Home Assistant.

For more details about this integration, please refer to
https://github.com/stephanu/mygekko
"""
import logging

from .coordinator import MyGekkoConfigEntry
from .coordinator import MyGekkoDataUpdateCoordinator
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_API_KEY
from homeassistant.const import CONF_IP_ADDRESS
from homeassistant.helpers import device_registry as dr
from homeassistant.helpers import issue_registry as ir
from homeassistant.core import HomeAssistant

from .const import CONF_CONNECTION_LOCAL
from .const import CONF_CONNECTION_MY_GEKKO_CLOUD
from .const import CONF_CONNECTION_TYPE
from .const import CONF_SCHEME
from .const import DOMAIN
from .const import PLATFORMS
from .entity import controller_device_id
from .entity import controller_device_info
from .const import STARTUP_MESSAGE

_LOGGER: logging.Logger = logging.getLogger(__name__)


async def async_setup_entry(hass: HomeAssistant, entry: MyGekkoConfigEntry):
    """Set up this integration using UI."""
    _LOGGER.debug(STARTUP_MESSAGE)

    _LOGGER.debug("async_setup_entry %s", entry.data.get(CONF_CONNECTION_TYPE))

    coordinator = MyGekkoDataUpdateCoordinator(hass, entry=entry)

    await coordinator.async_config_entry_first_refresh()

    entry.runtime_data = coordinator
    _register_controller(hass, entry, coordinator)

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    return True


def _register_controller(
    hass: HomeAssistant, entry: MyGekkoConfigEntry, coordinator
) -> None:
    """Register the MyGekko controller as device, the other devices connect to it."""
    network = coordinator.api.get_globals_network()
    if not controller_device_id(network):
        return
    if entry.data.get(CONF_CONNECTION_TYPE) == CONF_CONNECTION_LOCAL:
        url = f"{entry.data.get(CONF_SCHEME, 'https')}://{entry.data.get(CONF_IP_ADDRESS)}"
    elif entry.data.get(CONF_CONNECTION_TYPE) == CONF_CONNECTION_MY_GEKKO_CLOUD:
        url = "https://live.my-gekko.com"
    else:
        url = None
    device = dr.async_get(hass).async_get_or_create(
        config_entry_id=entry.entry_id, **controller_device_info(network, url)
    )
    coordinator.controller_registry_id = device.id


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


async def async_remove_entry(hass: HomeAssistant, entry: MyGekkoConfigEntry) -> None:
    """Remove what the entry created outside of the entity registry."""
    ir.async_delete_issue(hass, DOMAIN, f"rate_limited_{entry.entry_id}")


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry):
    """Handle removal of an entry."""
    return await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
