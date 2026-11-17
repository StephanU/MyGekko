"""Test MyGekko setup process."""
from custom_components.mygekko import MyGekkoDataUpdateCoordinator
from custom_components.mygekko.const import CONF_CONNECTION_TYPE
from custom_components.mygekko.const import DOMAIN
from homeassistant.config_entries import ConfigEntryState
from pytest_homeassistant_custom_component.common import MockConfigEntry

from .const import MOCK_CLOUD_ENTRY_DATA
from .const import MOCK_DEMO_ENTRY_DATA


async def _add_entry(hass, data, entry_id="test"):
    """Add a config entry and run it through the regular setup path."""
    config_entry = MockConfigEntry(
        domain=DOMAIN, data=data, entry_id=entry_id, version=3
    )
    config_entry.add_to_hass(hass)
    await hass.config_entries.async_setup(config_entry.entry_id)
    await hass.async_block_till_done()
    return config_entry


async def test_setup_unload_and_reload_entry(hass):
    """Test entry setup, reload and unload."""
    # Demo mode ships its own data, so no API has to be mocked here.
    config_entry = await _add_entry(hass, MOCK_DEMO_ENTRY_DATA)

    assert config_entry.state is ConfigEntryState.LOADED
    assert isinstance(
        hass.data[DOMAIN][config_entry.entry_id], MyGekkoDataUpdateCoordinator
    )

    assert await hass.config_entries.async_reload(config_entry.entry_id)
    await hass.async_block_till_done()
    assert config_entry.state is ConfigEntryState.LOADED
    assert isinstance(
        hass.data[DOMAIN][config_entry.entry_id], MyGekkoDataUpdateCoordinator
    )

    assert await hass.config_entries.async_unload(config_entry.entry_id)
    await hass.async_block_till_done()
    assert config_entry.state is ConfigEntryState.NOT_LOADED
    assert config_entry.entry_id not in hass.data[DOMAIN]


async def test_setup_entry_creates_entities(hass):
    """Test that setting up an entry actually adds entities."""
    await _add_entry(hass, MOCK_DEMO_ENTRY_DATA)

    assert hass.states.async_entity_ids("light")


async def test_setup_entry_retries_on_api_error(hass, error_on_get_data):
    """Test that a failing API puts the entry into retry instead of crashing."""
    config_entry = await _add_entry(hass, MOCK_CLOUD_ENTRY_DATA)

    assert config_entry.state is ConfigEntryState.SETUP_RETRY


async def test_setup_entry_without_connection_type(hass):
    """Test that an entry without a usable connection type errors out."""
    config_entry = await _add_entry(hass, {CONF_CONNECTION_TYPE: "does_not_exist"})

    assert config_entry.state is ConfigEntryState.SETUP_ERROR
