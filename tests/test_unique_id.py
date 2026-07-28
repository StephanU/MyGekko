"""Test that MyGekko entities are scoped to their config entry."""
import pytest
from custom_components.mygekko import async_migrate_entry
from custom_components.mygekko.const import CONF_CONNECTION_DEMO_MODE
from custom_components.mygekko.const import CONF_CONNECTION_TYPE
from custom_components.mygekko.const import DOMAIN
from homeassistant.helpers import device_registry as dr
from homeassistant.helpers import entity_registry as er
from pytest_homeassistant_custom_component.common import MockConfigEntry

DEMO_CONFIG = {CONF_CONNECTION_TYPE: CONF_CONNECTION_DEMO_MODE}


async def _setup_demo_entry(hass, entry_id):
    """Set up a demo mode config entry."""
    config_entry = MockConfigEntry(
        domain=DOMAIN, data=DEMO_CONFIG, entry_id=entry_id, version=4
    )
    config_entry.add_to_hass(hass)
    assert await hass.config_entries.async_setup(config_entry.entry_id)
    await hass.async_block_till_done()
    return config_entry


@pytest.mark.asyncio
async def test_two_entries_do_not_clash(hass, enable_custom_integrations):
    """Two controllers must not produce colliding unique ids."""
    first = await _setup_demo_entry(hass, "first_entry")
    second = await _setup_demo_entry(hass, "second_entry")

    registry = er.async_get(hass)
    first_ids = {
        e.unique_id for e in er.async_entries_for_config_entry(registry, first.entry_id)
    }
    second_ids = {
        e.unique_id for e in er.async_entries_for_config_entry(registry, second.entry_id)
    }

    assert first_ids, "no entities registered for the first entry"
    # Both controllers expose the same resources, so equal counts prove nothing got
    # dropped as a duplicate.
    assert len(first_ids) == len(second_ids)
    assert not first_ids & second_ids
    assert all(uid.startswith("first_entry_") for uid in first_ids)
    assert all(uid.startswith("second_entry_") for uid in second_ids)

    # The devices of both controllers must stay separate too.
    device_registry = dr.async_get(hass)
    first_devices = dr.async_entries_for_config_entry(device_registry, first.entry_id)
    second_devices = dr.async_entries_for_config_entry(device_registry, second.entry_id)
    assert first_devices
    assert not {d.id for d in first_devices} & {d.id for d in second_devices}


@pytest.mark.asyncio
async def test_migrate_v3_keeps_existing_entities(hass):
    """Migrating from version 3 renames entities instead of orphaning them."""
    config_entry = MockConfigEntry(
        domain=DOMAIN, data=DEMO_CONFIG, entry_id="legacy_entry", version=3
    )
    config_entry.add_to_hass(hass)

    device_registry = dr.async_get(hass)
    device = device_registry.async_get_or_create(
        config_entry_id=config_entry.entry_id,
        identifiers={(DOMAIN, "lightsitem13")},
    )
    registry = er.async_get(hass)
    entity = registry.async_get_or_create(
        "light",
        DOMAIN,
        "lightsitem13",
        config_entry=config_entry,
        device_id=device.id,
    )

    assert await async_migrate_entry(hass, config_entry)
    await hass.async_block_till_done()

    assert config_entry.version == 4
    # Same registry rows, new ids - so entity_id and history survive.
    assert registry.async_get(entity.entity_id).unique_id == "legacy_entry_lightsitem13"
    assert device_registry.async_get(device.id).identifiers == {
        (DOMAIN, "legacy_entry_lightsitem13")
    }


@pytest.mark.asyncio
async def test_migration_skips_taken_unique_id(hass):
    """A clashing target id must not abort a half applied migration."""
    config_entry = MockConfigEntry(
        domain=DOMAIN, data=DEMO_CONFIG, entry_id="legacy_entry", version=3
    )
    config_entry.add_to_hass(hass)

    registry = er.async_get(hass)
    blocked = registry.async_get_or_create(
        "light", DOMAIN, "lightsitem13", config_entry=config_entry
    )
    # A leftover row already occupies the id the migration wants to use.
    registry.async_get_or_create(
        "light", DOMAIN, "legacy_entry_lightsitem13", config_entry=config_entry
    )
    migratable = registry.async_get_or_create(
        "light", DOMAIN, "lightsitem14", config_entry=config_entry
    )

    assert await async_migrate_entry(hass, config_entry)

    assert config_entry.version == 4
    # The clash is skipped, everything else still migrates.
    assert registry.async_get(blocked.entity_id).unique_id == "lightsitem13"
    assert (
        registry.async_get(migratable.entity_id).unique_id == "legacy_entry_lightsitem14"
    )


@pytest.mark.asyncio
async def test_migration_is_idempotent(hass):
    """An already scoped entry must not be prefixed twice."""
    config_entry = MockConfigEntry(
        domain=DOMAIN, data=DEMO_CONFIG, entry_id="legacy_entry", version=3
    )
    config_entry.add_to_hass(hass)

    registry = er.async_get(hass)
    entity = registry.async_get_or_create(
        "light", DOMAIN, "legacy_entry_lightsitem13", config_entry=config_entry
    )

    assert await async_migrate_entry(hass, config_entry)

    assert registry.async_get(entity.entity_id).unique_id == "legacy_entry_lightsitem13"
