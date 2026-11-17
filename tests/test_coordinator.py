"""Test the MyGekko data update coordinator."""
import logging
from unittest.mock import patch

import pytest
from aiohttp import ConnectionTimeoutError
from custom_components.mygekko.const import DOMAIN
from homeassistant.config_entries import ConfigEntryState
from homeassistant.const import CONF_PASSWORD
from PyMyGekko.data_provider import MyGekkoForbidden
from pytest_homeassistant_custom_component.common import MockConfigEntry

from .const import MOCK_LOCAL_CONFIG
from .const import MOCK_LOCAL_ENTRY_DATA
from .const import MOCK_LOCAL_TIMEOUT_MESSAGE

READ_DATA = "PyMyGekko.MyGekkoLocalApiClient.read_data"


async def _add_local_entry(hass):
    """Add a local config entry and run it through the regular setup path."""
    config_entry = MockConfigEntry(
        domain=DOMAIN, data=MOCK_LOCAL_ENTRY_DATA, entry_id="test", version=3
    )
    config_entry.add_to_hass(hass)
    await hass.config_entries.async_setup(config_entry.entry_id)
    await hass.async_block_till_done()
    return config_entry


async def test_setup_timeout_does_not_log_credentials(hass, caplog):
    """Test that a timeout during setup keeps the credentials out of the log."""
    caplog.set_level(logging.DEBUG)

    with patch(
        READ_DATA, side_effect=ConnectionTimeoutError(MOCK_LOCAL_TIMEOUT_MESSAGE)
    ):
        config_entry = await _add_local_entry(hass)

    assert config_entry.state is ConfigEntryState.SETUP_RETRY
    assert "ConnectionTimeoutError" in caplog.text
    assert MOCK_LOCAL_CONFIG[CONF_PASSWORD] not in caplog.text


@pytest.mark.parametrize(
    ("error", "logged"),
    [
        (ConnectionTimeoutError(MOCK_LOCAL_TIMEOUT_MESSAGE), "ConnectionTimeoutError"),
        (TimeoutError(), "TimeoutError"),
        (MyGekkoForbidden(), "MyGekkoForbidden"),
    ],
)
async def test_failed_poll_does_not_log_credentials(hass, caplog, error, logged):
    """Test that a failed poll is logged without the credentials."""
    with patch(READ_DATA):
        config_entry = await _add_local_entry(hass)
    assert config_entry.state is ConfigEntryState.LOADED
    coordinator = hass.data[DOMAIN][config_entry.entry_id]

    caplog.set_level(logging.DEBUG)
    caplog.clear()
    with patch(READ_DATA, side_effect=error):
        await coordinator.async_refresh()

    assert not coordinator.last_update_success
    assert f"Error fetching {DOMAIN} data: {logged}" in caplog.text
    # Home Assistant logs the traceback of UpdateFailed at debug level, so the
    # original aiohttp error must not be chained to it.
    assert "Connection timeout to host" not in caplog.text
    assert MOCK_LOCAL_CONFIG[CONF_PASSWORD] not in caplog.text
