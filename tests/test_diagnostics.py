"""Tests for the diagnostics."""
import json

from homeassistant.components.diagnostics import REDACTED
from pytest_homeassistant_custom_component.common import MockConfigEntry
from pytest_homeassistant_custom_component.components.diagnostics import (
    get_diagnostics_for_config_entry,
)

from custom_components.mygekko.const import DOMAIN

from .const import CLOUD_CONFIG


async def test_diagnostics_hide_credentials(hass, hass_client, setup_demo):
    """The diagnostics contain statistics and no secrets."""
    diagnostics = await get_diagnostics_for_config_entry(hass, hass_client, setup_demo)
    assert diagnostics["home_assistant"]["version"]
    assert diagnostics["home_assistant"]["integration_version"]
    assert isinstance(diagnostics["home_assistant"]["native_temperature_api"], bool)
    assert diagnostics["coordinator"]["last_update_success"] is True
    assert diagnostics["coordinator"]["backoff_active"] is False
    assert diagnostics["devices"]["lights"] == 4  # three lights and one group
    assert "gekkoname" not in json.dumps(diagnostics)


async def test_diagnostics_redact_the_entry_data(hass, hass_client):
    """Credentials of the config entry are redacted."""
    entry = MockConfigEntry(domain=DOMAIN, version=3, data=CLOUD_CONFIG)
    entry.add_to_hass(hass)
    from unittest.mock import patch

    with patch("custom_components.mygekko.api.MyGekkoClient.read_data"):
        await hass.config_entries.async_setup(entry.entry_id)
        await hass.async_block_till_done()
        diagnostics = await get_diagnostics_for_config_entry(hass, hass_client, entry)
    data = diagnostics["entry"]["data"]
    assert data["api_key"] == REDACTED
    assert data["username"] == REDACTED
    assert data["gekkoid"] == REDACTED
    assert "secret" not in json.dumps(diagnostics)
