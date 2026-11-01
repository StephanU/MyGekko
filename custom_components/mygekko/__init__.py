"""Custom integration to integrate MyGekko with Home Assistant.

For more details about this integration, please refer to
https://github.com/stephanu/mygekko
"""
import logging

from custom_components.mygekko.coordinator import MyGekkoDataUpdateCoordinator
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_API_KEY
from homeassistant.core_config import Config
from homeassistant.core import callback
from homeassistant.core import HomeAssistant
from homeassistant.helpers import device_registry as dr
from homeassistant.helpers import entity_registry as er

from .const import CONF_CONNECTION_MY_GEKKO_CLOUD
from .const import CONF_CONNECTION_TYPE
from .const import DOMAIN
from .const import PLATFORMS
from .const import STARTUP_MESSAGE
from .entity import scoped_id

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

    return True


async def _async_scope_registries_to_entry(
    hass: HomeAssistant, config_entry: ConfigEntry
) -> None:
    """Namespace already registered entities and devices to their config entry.

    Before version 4 the unique ids and device identifiers were built from the
    controller local resource id only, so a second controller could not be set up.
    Prefixing the existing registry entries keeps the entities (and their history)
    of already configured controllers intact.
    """
    entry_id = config_entry.entry_id
    # A device that already clashed is linked to both config entries, so it can show
    # up here again after the other entry migrated it. Anything carrying a known entry
    # id is therefore already scoped and must be left alone.
    known_prefixes = tuple(
        f"{entry.entry_id}_" for entry in hass.config_entries.async_entries(DOMAIN)
    )

    device_registry = dr.async_get(hass)
    for device in dr.async_entries_for_config_entry(device_registry, entry_id):
        identifiers = set()
        for domain, identifier in device.identifiers:
            if domain == DOMAIN and not identifier.startswith(known_prefixes):
                identifier = scoped_id(entry_id, identifier)
            identifiers.add((domain, identifier))

        if identifiers == device.identifiers:
            continue

        taken = [
            identifier
            for identifier in identifiers
            if (other := device_registry.async_get_device(identifiers={identifier}))
            and other.id != device.id
        ]
        if taken:
            # async_update_device would raise and leave the migration half applied.
            _LOGGER.warning(
                "Skipping device migration, identifiers %s are already in use", taken
            )
            continue

        device_registry.async_update_device(device.id, new_identifiers=identifiers)

    entity_registry = er.async_get(hass)

    @callback
    def _migrate_unique_id(entity_entry: er.RegistryEntry) -> dict | None:
        if entity_entry.unique_id.startswith(known_prefixes):
            return None

        new_unique_id = scoped_id(entry_id, entity_entry.unique_id)
        if conflict := entity_registry.async_get_entity_id(
            entity_entry.domain, entity_entry.platform, new_unique_id
        ):
            # async_update_entity would raise and leave the migration half applied.
            _LOGGER.warning(
                "Skipping migration of %s, unique id %s is already used by %s",
                entity_entry.entity_id,
                new_unique_id,
                conflict,
            )
            return None

        return {"new_unique_id": new_unique_id}

    await er.async_migrate_entries(hass, entry_id, _migrate_unique_id)


async def async_migrate_entry(hass: HomeAssistant, config_entry: ConfigEntry):
    """Migrate old entry."""
    _LOGGER.debug("Migrating from version %s", config_entry.version)

    if config_entry.version > 4:
        # Downgrade from a future version is not supported.
        return False

    if config_entry.version == 1:
        new = {**config_entry.data}
        new[CONF_CONNECTION_TYPE] = CONF_CONNECTION_MY_GEKKO_CLOUD

        hass.config_entries.async_update_entry(config_entry, data=new, version=2)

    if config_entry.version == 2:
        new = {**config_entry.data}
        new[CONF_API_KEY] = new["apikey"]
        new.pop("apikey")

        hass.config_entries.async_update_entry(config_entry, data=new, version=3)

    if config_entry.version == 3:
        await _async_scope_registries_to_entry(hass, config_entry)

        hass.config_entries.async_update_entry(config_entry, version=4)

    _LOGGER.debug("Migration to version %s successful", config_entry.version)

    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry):
    """Handle removal of an entry."""
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)

    if unload_ok:
        hass.data[DOMAIN].pop(entry.entry_id)

    return unload_ok
