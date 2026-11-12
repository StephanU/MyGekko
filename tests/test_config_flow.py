"""Test MyGekko config flow."""
from unittest.mock import patch

import pytest
from custom_components.mygekko.const import (
    CONF_CONNECTION_DEMO_MODE,
)
from custom_components.mygekko.const import (
    CONF_CONNECTION_DEMO_MODE_LABEL,
)
from custom_components.mygekko.const import (
    CONF_CONNECTION_LOCAL,
)
from custom_components.mygekko.const import (
    CONF_CONNECTION_MY_GEKKO_CLOUD,
)
from custom_components.mygekko.const import (
    CONF_CONNECTION_TYPE,
)
from custom_components.mygekko.const import (
    DOMAIN,
)
from custom_components.mygekko.const import (
    CONF_ALARM_SYSTEM_READ_ONLY,
)
from homeassistant import config_entries
from homeassistant import data_entry_flow
from pytest_homeassistant_custom_component.common import MockConfigEntry

from .conftest import API_CLIENTS
from .const import MOCK_CLOUD_ENTRY_DATA
from .const import MOCK_CONFIG
from .const import MOCK_DEMO_ENTRY_DATA
from .const import MOCK_LOCAL_CONFIG
from .const import MOCK_LOCAL_ENTRY_DATA


# This fixture bypasses the actual setup of the integration
# since we only want to test the config flow. We test the
# actual functionality of the integration in other test modules.
@pytest.fixture(autouse=True)
def bypass_setup_fixture():
    """Prevent setup."""
    with patch(
        "custom_components.mygekko.async_setup",
        return_value=True,
    ), patch(
        "custom_components.mygekko.async_setup_entry",
        return_value=True,
    ):
        yield


async def _start_flow(hass, connection_type):
    """Start a flow and pick a connection type."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )

    # The first step lets the user choose how to connect.
    assert result["type"] is data_entry_flow.FlowResultType.FORM
    assert result["step_id"] == "connection_selection"

    return await hass.config_entries.flow.async_configure(
        result["flow_id"], user_input={CONF_CONNECTION_TYPE: connection_type}
    )


async def test_cloud_config_flow(hass, bypass_try_connect, bypass_get_data, gekko_name):
    """Test a successful config flow via the MyGekko Plus Query API."""
    result = await _start_flow(hass, CONF_CONNECTION_MY_GEKKO_CLOUD)

    assert result["type"] is data_entry_flow.FlowResultType.FORM
    assert result["step_id"] == "connection_mygekko_cloud"

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], user_input=MOCK_CONFIG
    )

    assert result["type"] is data_entry_flow.FlowResultType.CREATE_ENTRY
    assert result["title"] == "Test Gekko"
    # The flow stores the selected connection type alongside the credentials.
    assert result["data"] == MOCK_CLOUD_ENTRY_DATA
    assert result["result"].version == 4


async def test_local_config_flow(hass, bypass_try_connect, bypass_get_data, gekko_name):
    """Test a successful config flow via a local connection."""
    result = await _start_flow(hass, CONF_CONNECTION_LOCAL)

    assert result["type"] is data_entry_flow.FlowResultType.FORM
    assert result["step_id"] == "connection_local"

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], user_input=MOCK_LOCAL_CONFIG
    )

    assert result["type"] is data_entry_flow.FlowResultType.CREATE_ENTRY
    assert result["title"] == "Test Gekko"
    assert result["data"] == MOCK_LOCAL_ENTRY_DATA


@pytest.mark.parametrize(
    ("connection_type", "user_input", "title"),
    [
        (CONF_CONNECTION_MY_GEKKO_CLOUD, MOCK_CONFIG, "test_gekkoid"),
        (CONF_CONNECTION_LOCAL, MOCK_LOCAL_CONFIG, "192.168.1.2"),
    ],
)
async def test_config_flow_title_without_gekko_name(
    hass, bypass_try_connect, bypass_get_data, connection_type, user_input, title
):
    """Test that the entry falls back to the gekko id or IP address as title."""
    result = await _start_flow(hass, connection_type)
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], user_input=user_input
    )

    assert result["type"] is data_entry_flow.FlowResultType.CREATE_ENTRY
    assert result["title"] == title


async def test_demo_mode_config_flow(hass):
    """Test that demo mode needs no further input."""
    result = await _start_flow(hass, CONF_CONNECTION_DEMO_MODE)

    assert result["type"] is data_entry_flow.FlowResultType.CREATE_ENTRY
    assert result["title"] == CONF_CONNECTION_DEMO_MODE_LABEL
    assert result["data"] == MOCK_DEMO_ENTRY_DATA


async def test_cloud_config_flow_invalid_credentials(hass, error_on_try_connect):
    """Test that invalid cloud credentials are reported on the form."""
    result = await _start_flow(hass, CONF_CONNECTION_MY_GEKKO_CLOUD)
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], user_input=MOCK_CONFIG
    )

    assert result["type"] is data_entry_flow.FlowResultType.FORM
    assert result["step_id"] == "connection_mygekko_cloud"
    assert result["errors"] == {"base": "auth_cloud"}


async def test_local_config_flow_invalid_credentials(hass, error_on_try_connect):
    """Test that invalid local credentials are reported on the form."""
    result = await _start_flow(hass, CONF_CONNECTION_LOCAL)
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], user_input=MOCK_LOCAL_CONFIG
    )

    assert result["type"] is data_entry_flow.FlowResultType.FORM
    assert result["step_id"] == "connection_local"
    assert result["errors"] == {"base": "auth_local"}


async def test_multiple_entries_allowed(hass, bypass_try_connect):
    """Test that a second controller can be configured."""
    for _ in range(2):
        result = await _start_flow(hass, CONF_CONNECTION_DEMO_MODE)
        assert result["type"] is data_entry_flow.FlowResultType.CREATE_ENTRY

    assert len(hass.config_entries.async_entries(DOMAIN)) == 2


async def test_config_flow_asks_about_alarm_system(
    hass, bypass_try_connect, bypass_get_data, gekko_name
):
    """A controller with alarm system asks whether it is read only."""
    with patch(f"{API_CLIENTS[0]}.get_alarm_systems", return_value=[object()]):
        result = await _start_flow(hass, CONF_CONNECTION_MY_GEKKO_CLOUD)
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"], user_input=MOCK_CONFIG
        )

    assert result["type"] is data_entry_flow.FlowResultType.FORM
    assert result["step_id"] == "alarm_system"

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], user_input={CONF_ALARM_SYSTEM_READ_ONLY: True}
    )

    assert result["type"] is data_entry_flow.FlowResultType.CREATE_ENTRY
    assert result["title"] == "Test Gekko"
    assert result["data"] == MOCK_CLOUD_ENTRY_DATA
    assert result["options"] == {CONF_ALARM_SYSTEM_READ_ONLY: True}


async def test_reconfigure_replaces_data_and_reloads(hass, bypass_try_connect):
    """Reconfiguring replaces the connection data and reloads the entry."""
    entry = MockConfigEntry(
        domain=DOMAIN, data=MOCK_CLOUD_ENTRY_DATA, title="Office", version=4
    )
    entry.add_to_hass(hass)

    with patch.object(
        hass.config_entries, "async_schedule_reload"
    ) as schedule_reload:
        result = await entry.start_reconfigure_flow(hass)
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"], user_input={CONF_CONNECTION_TYPE: CONF_CONNECTION_LOCAL}
        )
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"], user_input=MOCK_LOCAL_CONFIG
        )

    assert result["type"] is data_entry_flow.FlowResultType.ABORT
    assert result["reason"] == "reconfigure_successful"
    assert dict(entry.data) == MOCK_LOCAL_ENTRY_DATA
    assert entry.title == "Office"
    schedule_reload.assert_called_once_with(entry.entry_id)
