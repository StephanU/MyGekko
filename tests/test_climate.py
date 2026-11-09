"""Test the optimistic target temperature of MyGekko climate entities."""
from unittest.mock import AsyncMock
from unittest.mock import patch
from unittest.mock import PropertyMock

import pytest
from custom_components.mygekko.const import DOMAIN
from homeassistant.components.climate import ATTR_TEMPERATURE
from homeassistant.const import ATTR_ENTITY_ID
from homeassistant.helpers import entity_registry as er
from PyMyGekko.resources.RoomTemps import RoomTemp
from pytest_homeassistant_custom_component.common import MockConfigEntry

from .const import MOCK_DEMO_ENTRY_DATA


@pytest.fixture(name="polled")
def polled_fixture():
    """Control what a poll returns for the demo room temperatures."""
    polled = {"target_temperature": 20.0}
    with patch.object(
        RoomTemp,
        "target_temperature",
        new_callable=PropertyMock,
        side_effect=lambda: polled["target_temperature"],
    ), patch.object(RoomTemp, "set_target_temperature", new_callable=AsyncMock):
        yield polled


async def _setup_climate(hass):
    """Set up a demo entry and return the coordinator and a climate entity id."""
    config_entry = MockConfigEntry(
        domain=DOMAIN, data=MOCK_DEMO_ENTRY_DATA, entry_id="climate_test", version=4
    )
    config_entry.add_to_hass(hass)
    assert await hass.config_entries.async_setup(config_entry.entry_id)
    await hass.async_block_till_done()
    entity_id = er.async_get(hass).async_get_entity_id(
        "climate", DOMAIN, "climate_test_room_tempsitem0"
    )
    return hass.data[DOMAIN][config_entry.entry_id], entity_id


async def _set_temperature(hass, entity_id, temperature):
    """Call climate.set_temperature."""
    await hass.services.async_call(
        "climate",
        "set_temperature",
        {ATTR_ENTITY_ID: entity_id, ATTR_TEMPERATURE: temperature},
        blocking=True,
    )


def _target_temperature(hass, entity_id):
    """Return the target temperature Home Assistant shows."""
    return hass.states.get(entity_id).attributes[ATTR_TEMPERATURE]


async def test_earlier_command_does_not_end_latest(hass, polled):
    """A poll showing an earlier command must keep the latest one."""
    coordinator, entity_id = await _setup_climate(hass)

    await _set_temperature(hass, entity_id, 21.0)
    await _set_temperature(hass, entity_id, 22.0)
    assert _target_temperature(hass, entity_id) == 22.0

    # The myGekko has processed the first command, but not the second yet.
    polled["target_temperature"] = 21.0
    await coordinator.async_refresh()
    assert _target_temperature(hass, entity_id) == 22.0

    polled["target_temperature"] = 22.0
    await coordinator.async_refresh()
    assert _target_temperature(hass, entity_id) == 22.0

    # Once confirmed, a change on the controller shows right away.
    polled["target_temperature"] = 19.0
    await coordinator.async_refresh()
    assert _target_temperature(hass, entity_id) == 19.0


async def test_value_of_no_command_ends_optimistic_value(hass, polled):
    """A poll showing a value no command has sent must end the optimistic value."""
    coordinator, entity_id = await _setup_climate(hass)

    await _set_temperature(hass, entity_id, 21.0)
    await _set_temperature(hass, entity_id, 22.0)

    polled["target_temperature"] = 18.0
    await coordinator.async_refresh()
    assert _target_temperature(hass, entity_id) == 18.0


async def test_poll_of_earlier_command_drops_older_values(hass, polled):
    """After a poll shows an earlier command, the values before it end the optimistic value."""
    coordinator, entity_id = await _setup_climate(hass)

    await _set_temperature(hass, entity_id, 21.0)
    await _set_temperature(hass, entity_id, 22.0)

    polled["target_temperature"] = 21.0
    await coordinator.async_refresh()
    assert _target_temperature(hass, entity_id) == 22.0

    # Back to the value before the first command: changed on the controller.
    polled["target_temperature"] = 20.0
    await coordinator.async_refresh()
    assert _target_temperature(hass, entity_id) == 20.0
