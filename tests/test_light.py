"""Test MyGekko light."""
from unittest.mock import call
from unittest.mock import patch

import pytest
from custom_components.mygekko import (
    async_setup_entry,
)
from custom_components.mygekko.const import (
    DEFAULT_NAME,
)
from custom_components.mygekko.const import (
    DOMAIN,
)
from custom_components.mygekko.const import (
    LIGHT,
)
from homeassistant.components.light import SERVICE_TURN_OFF
from homeassistant.components.light import SERVICE_TURN_ON
from homeassistant.const import ATTR_ENTITY_ID
from pytest_homeassistant_custom_component.common import MockConfigEntry

from .const import MOCK_CONFIG


@pytest.mark.asyncio
async def test_light_services(hass):
    """Test light services."""
    # Create a mock entry so we don't have to go through config flow
    config_entry = MockConfigEntry(domain=DOMAIN, data=MOCK_CONFIG, entry_id="test")
    assert await async_setup_entry(hass, config_entry)
    await hass.async_block_till_done()

    # Functions/objects can be patched directly in test code as well and can be used to test
    # additional things, like whether a function was called or what arguments it was called with
    with patch(
        "custom_components.mygekko.MyGekkoApiClient.async_set_title"
    ) as title_func:
        await hass.services.async_call(
            LIGHT,
            SERVICE_TURN_OFF,
            service_data={ATTR_ENTITY_ID: f"{LIGHT}.{DEFAULT_NAME}_{LIGHT}"},
            blocking=True,
        )
        assert title_func.called
        assert title_func.call_args == call("foo")

        title_func.reset_mock()

        await hass.services.async_call(
            LIGHT,
            SERVICE_TURN_ON,
            service_data={ATTR_ENTITY_ID: f"{LIGHT}.{DEFAULT_NAME}_{LIGHT}"},
            blocking=True,
        )
        assert title_func.called
        assert title_func.call_args == call("bar")
