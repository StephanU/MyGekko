"""Test the commands of MyGekko charging station switches."""
import asyncio
from unittest.mock import AsyncMock
from unittest.mock import patch
from unittest.mock import PropertyMock

from custom_components.mygekko.const import DOMAIN
from homeassistant.const import ATTR_ENTITY_ID
from homeassistant.const import STATE_OFF
from homeassistant.helpers import entity_registry as er
from PyMyGekko.resources.EMobils import EMobil
from PyMyGekko.resources.EMobils import EMobilChargeState
from pytest_homeassistant_custom_component.common import MockConfigEntry

from .const import MOCK_DEMO_ENTRY_DATA


async def test_concurrent_charge_commands_keep_call_order(hass):
    """A start whose write returns late must not overtake a later stop."""
    config_entry = MockConfigEntry(
        domain=DOMAIN, data=MOCK_DEMO_ENTRY_DATA, entry_id="switch_test", version=4
    )
    release = asyncio.Event()
    reached_mygekko = []

    async def start_charge():
        await release.wait()
        reached_mygekko.append("start")

    async def stop_charge():
        reached_mygekko.append("stop")

    with patch.object(
        EMobil,
        "charge_state",
        new_callable=PropertyMock,
        return_value=EMobilChargeState.OFF,
    ), patch.object(
        EMobil, "start_charge", new_callable=AsyncMock, side_effect=start_charge
    ), patch.object(
        EMobil, "stop_charge", new_callable=AsyncMock, side_effect=stop_charge
    ):
        config_entry.add_to_hass(hass)
        assert await hass.config_entries.async_setup(config_entry.entry_id)
        await hass.async_block_till_done()
        entity_id = er.async_get(hass).async_get_entity_id(
            "switch", DOMAIN, "switch_test_emobilsitem0charge"
        )

        turn_on = hass.async_create_task(
            hass.services.async_call(
                "switch", "turn_on", {ATTR_ENTITY_ID: entity_id}, blocking=True
            )
        )
        while not EMobil.start_charge.await_count:
            await asyncio.sleep(0)
        turn_off = hass.async_create_task(
            hass.services.async_call(
                "switch", "turn_off", {ATTR_ENTITY_ID: entity_id}, blocking=True
            )
        )
        for _ in range(10):
            await asyncio.sleep(0)
        release.set()
        await turn_on
        await turn_off

        assert reached_mygekko == ["start", "stop"]
        assert hass.states.get(entity_id).state == STATE_OFF
