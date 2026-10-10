"""Tests for setting up, unloading and migrating the integration."""
from unittest.mock import patch

from homeassistant.config_entries import ConfigEntryState
from homeassistant.helpers import device_registry as dr
from homeassistant.helpers import entity_registry as er
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.mygekko.api import MyGekkoForbidden
from custom_components.mygekko.api import MyGekkoTooManyRequests
from custom_components.mygekko.const import CONF_CONNECTION_MY_GEKKO_CLOUD
from custom_components.mygekko.const import DOMAIN

from .const import CLOUD_INPUT


async def test_demo_setup_creates_entities(hass, setup_demo):
    """All platforms create their entities in demo mode."""
    domains = {state.domain for state in hass.states.async_all()}
    assert {
        "light",
        "cover",
        "climate",
        "switch",
        "sensor",
        "select",
        "scene",
        "button",
        "water_heater",
    } <= domains
    registry = er.async_get(hass)
    entries = er.async_entries_for_config_entry(registry, setup_demo.entry_id)
    assert len(entries) == len({entry.unique_id for entry in entries})
    assert dr.async_entries_for_config_entry(dr.async_get(hass), setup_demo.entry_id)


async def test_unload_and_reload(hass, setup_demo):
    """The entry can be unloaded and reloaded without leftovers."""
    count = len(hass.states.async_all())
    await hass.config_entries.async_reload(setup_demo.entry_id)
    await hass.async_block_till_done()
    assert setup_demo.state is ConfigEntryState.LOADED
    assert len(hass.states.async_all()) == count

    await hass.config_entries.async_unload(setup_demo.entry_id)
    await hass.async_block_till_done()
    assert setup_demo.state is ConfigEntryState.NOT_LOADED


async def test_setup_retries_when_gekko_is_not_reachable(hass):
    """An unreachable MyGekko makes the setup retry instead of fail."""
    entry = MockConfigEntry(
        domain=DOMAIN,
        version=3,
        data={"connection_type": CONF_CONNECTION_MY_GEKKO_CLOUD, **CLOUD_INPUT},
    )
    entry.add_to_hass(hass)
    for error in (MyGekkoTooManyRequests("429"), MyGekkoForbidden("403"), TimeoutError()):
        with patch(
            "custom_components.mygekko.api.MyGekkoClient.read_data", side_effect=error
        ):
            await hass.config_entries.async_setup(entry.entry_id)
        assert entry.state is ConfigEntryState.SETUP_RETRY
        await hass.config_entries.async_unload(entry.entry_id)


async def test_migration_from_version_1(hass):
    """Old entries are migrated to the current version."""
    entry = MockConfigEntry(
        domain=DOMAIN,
        version=1,
        data={"username": "u", "apikey": "k", "gekkoid": "g"},
    )
    entry.add_to_hass(hass)
    with patch("custom_components.mygekko.api.MyGekkoClient.read_data"):
        await hass.config_entries.async_setup(entry.entry_id)
    assert entry.version == 3
    assert entry.data["api_key"] == "k"
    assert "apikey" not in entry.data
