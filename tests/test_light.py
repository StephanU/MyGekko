"""Test MyGekko light."""
from unittest.mock import call
from unittest.mock import patch

import pytest
from custom_components.mygekko.const import DOMAIN
from homeassistant.components.light import DOMAIN as LIGHT_DOMAIN
from homeassistant.components.light import SERVICE_TURN_OFF
from homeassistant.components.light import SERVICE_TURN_ON
from homeassistant.const import ATTR_ENTITY_ID
from homeassistant.const import STATE_OFF
from homeassistant.const import STATE_ON
from PyMyGekko.resources.Lights import Light
from PyMyGekko.resources.Lights import LightState
from pytest_homeassistant_custom_component.common import MockConfigEntry

from .const import MOCK_DEMO_ENTRY_DATA

# Entities provided by the PyMyGekko demo data.
LIGHT_ON = "light.buro_decke"
LIGHT_OFF = "light.bad"


@pytest.fixture(name="demo_entry")
async def demo_entry_fixture(hass):
    """Set up the integration in demo mode."""
    config_entry = MockConfigEntry(
        domain=DOMAIN, data=MOCK_DEMO_ENTRY_DATA, entry_id="test", version=3
    )
    config_entry.add_to_hass(hass)
    await hass.config_entries.async_setup(config_entry.entry_id)
    await hass.async_block_till_done()
    return config_entry


async def test_light_state(hass, demo_entry):
    """Test that the light state is taken from the controller."""
    assert hass.states.get(LIGHT_ON).state == STATE_ON
    assert hass.states.get(LIGHT_OFF).state == STATE_OFF


async def test_light_name(hass, demo_entry):
    """Test that the light is named after the controller resource."""
    assert hass.states.get(LIGHT_ON).attributes["friendly_name"] == "Büro Decke"


async def test_light_turn_on(hass, demo_entry):
    """Test turning a light on."""
    with patch.object(Light, "set_state") as set_state:
        await hass.services.async_call(
            LIGHT_DOMAIN,
            SERVICE_TURN_ON,
            service_data={ATTR_ENTITY_ID: LIGHT_OFF},
            blocking=True,
        )

    assert set_state.call_args == call(LightState.ON)


async def test_light_turn_off(hass, demo_entry):
    """Test turning a light off."""
    with patch.object(Light, "set_state") as set_state:
        await hass.services.async_call(
            LIGHT_DOMAIN,
            SERVICE_TURN_OFF,
            service_data={ATTR_ENTITY_ID: LIGHT_ON},
            blocking=True,
        )

    assert set_state.call_args == call(LightState.OFF)
