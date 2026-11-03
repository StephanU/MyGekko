"""Test the optimistic movement state of MyGekko covers."""
from unittest.mock import AsyncMock
from unittest.mock import patch
from unittest.mock import PropertyMock

import pytest
from custom_components.mygekko.const import CONF_CONNECTION_DEMO_MODE
from custom_components.mygekko.const import CONF_CONNECTION_TYPE
from custom_components.mygekko.const import DOMAIN
from homeassistant.components.cover import CoverState
from homeassistant.const import ATTR_ENTITY_ID
from homeassistant.helpers import entity_registry as er
from PyMyGekko.resources.Blinds import Blind
from PyMyGekko.resources.Blinds import BlindState
from pytest_homeassistant_custom_component.common import MockConfigEntry

DEMO_CONFIG = {CONF_CONNECTION_TYPE: CONF_CONNECTION_DEMO_MODE}


@pytest.fixture(name="polled")
def polled_fixture(enable_custom_integrations):
    """Control what a poll returns for the demo blinds."""
    polled = {"state": BlindState.STOP, "position": 90.0}
    with patch.object(
        Blind, "state", new_callable=PropertyMock, side_effect=lambda: polled["state"]
    ), patch.object(
        Blind,
        "position",
        new_callable=PropertyMock,
        side_effect=lambda: polled["position"],
    ), patch.object(Blind, "set_state", new_callable=AsyncMock):
        yield polled


async def _setup_cover(hass):
    """Set up a demo entry and return the coordinator and a cover entity id."""
    config_entry = MockConfigEntry(
        domain=DOMAIN, data=DEMO_CONFIG, entry_id="cover_test", version=4
    )
    config_entry.add_to_hass(hass)
    assert await hass.config_entries.async_setup(config_entry.entry_id)
    await hass.async_block_till_done()
    entity_id = er.async_get(hass).async_get_entity_id(
        "cover", DOMAIN, "cover_test_blindsitem0"
    )
    return hass.data[DOMAIN][config_entry.entry_id], entity_id


async def _call(hass, service, entity_id):
    """Call a cover service."""
    await hass.services.async_call(
        "cover", service, {ATTR_ENTITY_ID: entity_id}, blocking=True
    )


@pytest.mark.asyncio
async def test_short_movement_between_polls(hass, polled):
    """A movement that ends between two polls must not stay closing."""
    coordinator, entity_id = await _setup_cover(hass)

    # The refresh right after the command still returns the old values.
    await _call(hass, "close_cover", entity_id)
    assert hass.states.get(entity_id).state == CoverState.CLOSING

    polled["position"] = 100.0
    await coordinator.async_refresh()
    assert hass.states.get(entity_id).state == CoverState.CLOSED

    Blind.set_state.reset_mock()
    await _call(hass, "toggle", entity_id)
    Blind.set_state.assert_awaited_once_with(BlindState.HOLD_UP)


@pytest.mark.asyncio
async def test_no_movement_when_already_closed(hass, polled):
    """Closing a closed blind must not report it as closing."""
    polled["position"] = 100.0
    _, entity_id = await _setup_cover(hass)

    await _call(hass, "close_cover", entity_id)
    assert hass.states.get(entity_id).state == CoverState.CLOSED


@pytest.mark.asyncio
async def test_no_movement_when_already_open(hass, polled):
    """Opening an open blind must not report it as opening."""
    polled["position"] = 0.0
    _, entity_id = await _setup_cover(hass)

    await _call(hass, "open_cover", entity_id)
    assert hass.states.get(entity_id).state == CoverState.OPEN


@pytest.mark.asyncio
async def test_stop_survives_stale_poll_of_moving_blind(hass, polled):
    """A stale poll of a moving blind must not undo a stop."""
    polled.update(state=BlindState.DOWN, position=40.0)
    coordinator, entity_id = await _setup_cover(hass)
    assert hass.states.get(entity_id).state == CoverState.CLOSING

    await _call(hass, "stop_cover", entity_id)
    assert hass.states.get(entity_id).state == CoverState.OPEN

    # The blind has moved on, but the myGekko has not processed the stop yet.
    polled["position"] = 55.0
    await coordinator.async_refresh()
    assert hass.states.get(entity_id).state == CoverState.OPEN

    polled.update(state=BlindState.STOP, position=60.0)
    await coordinator.async_refresh()
    assert hass.states.get(entity_id).state == CoverState.OPEN
