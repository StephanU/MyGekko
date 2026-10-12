"""Custom integration to integrate MyGekko with Home Assistant.

For more details about this integration, please refer to
https://github.com/merlin2533/MyGekko
"""
import logging

from .coordinator import MyGekkoConfigEntry
from .coordinator import MyGekkoDataUpdateCoordinator
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_API_KEY
from homeassistant.const import CONF_IP_ADDRESS
from homeassistant.helpers import device_registry as dr
from homeassistant.helpers import issue_registry as ir
from homeassistant.helpers.storage import Store
from homeassistant.core import HomeAssistant

from .const import CONF_CONNECTION_LOCAL
from .const import CONF_CONNECTION_MY_GEKKO_CLOUD
from .const import CONF_CONNECTION_TYPE
from .const import CONF_GEKKOID
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

    _adopt_unique_id(hass, entry)
    _update_duplicate_issues(hass)

    coordinator = MyGekkoDataUpdateCoordinator(hass, entry=entry)
    await coordinator.async_load_cache()

    await coordinator.async_config_entry_first_refresh()

    entry.runtime_data = coordinator
    entry.async_on_unload(coordinator.async_cancel_queued)
    _register_controller(hass, entry, coordinator)

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    return True


def _expected_unique_id(entry: ConfigEntry) -> str | None:
    """Return the unique id the config flow gives to the MyGekko of an entry."""
    connection_type = entry.data.get(CONF_CONNECTION_TYPE)
    if connection_type == CONF_CONNECTION_MY_GEKKO_CLOUD and entry.data.get(CONF_GEKKOID):
        return f"cloud_{entry.data[CONF_GEKKOID]}"
    if connection_type == CONF_CONNECTION_LOCAL and entry.data.get(CONF_IP_ADDRESS):
        return f"local_{entry.data[CONF_IP_ADDRESS]}"
    return None


def _adopt_unique_id(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Give entries of older versions their unique id, so they cannot be added twice."""
    unique_id = _expected_unique_id(entry)
    if entry.unique_id is not None or unique_id is None:
        return
    if any(
        other.unique_id == unique_id
        for other in hass.config_entries.async_entries(DOMAIN)
        if other.entry_id != entry.entry_id
    ):
        return
    hass.config_entries.async_update_entry(entry, unique_id=unique_id)


def _update_duplicate_issues(hass: HomeAssistant, removed_entry_id: str | None = None) -> None:
    """Report MyGekkos that are set up more than once (disabled entries included)."""
    entries = [
        entry
        for entry in hass.config_entries.async_entries(DOMAIN)
        if entry.entry_id != removed_entry_id
    ]
    for entry in entries:
        issue_id = f"duplicate_entry_{entry.entry_id}"
        unique_id = _expected_unique_id(entry)
        duplicates = [
            other
            for other in entries
            if unique_id is not None and _expected_unique_id(other) == unique_id
        ]
        # one issue per MyGekko: reported by the first of its entries
        if len(duplicates) > 1 and duplicates[0].entry_id == entry.entry_id:
            ir.async_create_issue(
                hass,
                DOMAIN,
                issue_id,
                is_fixable=False,
                severity=ir.IssueSeverity.WARNING,
                translation_key="duplicate_entry",
                translation_placeholders={
                    "name": entry.title,
                    "count": str(len(duplicates)),
                    "disabled": str(sum(1 for other in duplicates if other.disabled_by)),
                },
            )
        else:
            ir.async_delete_issue(hass, DOMAIN, issue_id)


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
    ir.async_delete_issue(hass, DOMAIN, f"duplicate_entry_{entry.entry_id}")
    _update_duplicate_issues(hass, removed_entry_id=entry.entry_id)
    hass.data.get(DOMAIN, {}).get("rate_limit_pauses", {}).pop(entry.entry_id, None)
    # the last state saved by the coordinator
    await Store(hass, 1, f"{DOMAIN}.{entry.entry_id}").async_remove()


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry):
    """Handle removal of an entry."""
    return await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
