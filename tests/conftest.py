"""Global fixtures for MyGekko integration."""
from unittest.mock import AsyncMock
from unittest.mock import patch

import pytest
from homeassistant.config_entries import ConfigEntryState
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.mygekko import coordinator as coordinator_module
from custom_components.mygekko.const import DOMAIN

from .const import DEMO_CONFIG

pytest_plugins = "pytest_homeassistant_custom_component"


@pytest.fixture(autouse=True)
def auto_enable_custom_integrations(enable_custom_integrations):
    """Enable loading of the custom integration in every test."""
    return enable_custom_integrations


@pytest.fixture(autouse=True)
def fast_writes(monkeypatch):
    """Do not wait between commands in tests."""
    monkeypatch.setattr(coordinator_module, "WRITE_MIN_DELAY", 0)


@pytest.fixture
def demo_entry(hass):
    """Return a demo mode config entry that was added to hass."""
    entry = MockConfigEntry(
        domain=DOMAIN, version=3, data=DEMO_CONFIG, unique_id="demo"
    )
    entry.add_to_hass(hass)
    return entry


@pytest.fixture
async def setup_demo(hass, demo_entry):
    """Set up the demo mode config entry and capture all commands."""
    with patch(
        "custom_components.mygekko.api.MyGekkoDemoModeClient.write",
        new_callable=AsyncMock,
    ) as write:
        await hass.config_entries.async_setup(demo_entry.entry_id)
        await hass.async_block_till_done()
        assert demo_entry.state is ConfigEntryState.LOADED
        demo_entry.write = write
        yield demo_entry
