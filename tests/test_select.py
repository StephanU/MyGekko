"""Test the optimistic option of MyGekko selects."""
from unittest.mock import AsyncMock
from unittest.mock import patch
from unittest.mock import PropertyMock

from custom_components.mygekko.const import DOMAIN
from homeassistant.const import ATTR_ENTITY_ID
from homeassistant.helpers import entity_registry as er
from PyMyGekko.resources.Vents import Vent
from PyMyGekko.resources.Vents import VentWorkingLevel
from pytest_homeassistant_custom_component.common import MockConfigEntry

from .const import MOCK_DEMO_ENTRY_DATA


async def test_earlier_option_does_not_end_latest(hass):
    """A poll showing an earlier selected option must keep the latest one."""
    config_entry = MockConfigEntry(
        domain=DOMAIN, data=MOCK_DEMO_ENTRY_DATA, entry_id="select_test", version=4
    )
    polled = {"working_level": VentWorkingLevel.LEVEL_1}
    with patch.object(
        Vent,
        "working_level",
        new_callable=PropertyMock,
        side_effect=lambda: polled["working_level"],
    ), patch.object(Vent, "set_working_level", new_callable=AsyncMock):
        config_entry.add_to_hass(hass)
        assert await hass.config_entries.async_setup(config_entry.entry_id)
        await hass.async_block_till_done()
        coordinator = hass.data[DOMAIN][config_entry.entry_id]
        entity_id = er.async_get(hass).async_get_entity_id(
            "select", DOMAIN, "select_test_ventsitem0Level"
        )

        for level in (VentWorkingLevel.LEVEL_2, VentWorkingLevel.LEVEL_3):
            await hass.services.async_call(
                "select",
                "select_option",
                {ATTR_ENTITY_ID: entity_id, "option": str(level)},
                blocking=True,
            )
        assert hass.states.get(entity_id).state == str(VentWorkingLevel.LEVEL_3)

        # The myGekko has processed the first command, but not the second yet.
        polled["working_level"] = VentWorkingLevel.LEVEL_2
        await coordinator.async_refresh()
        assert hass.states.get(entity_id).state == str(VentWorkingLevel.LEVEL_3)
