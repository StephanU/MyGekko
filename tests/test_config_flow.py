"""Tests for the MyGekko config flow."""
from unittest.mock import AsyncMock
from unittest.mock import patch

import pytest
from homeassistant import config_entries
from homeassistant.data_entry_flow import FlowResultType
from aiohttp import ClientConnectorError
from aiohttp import ClientConnectorSSLError
from aiohttp.client_reqrep import ConnectionKey
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.mygekko.api import MyGekkoError
from custom_components.mygekko.const import CONF_CONNECTION_DEMO_MODE
from custom_components.mygekko.const import CONF_CONNECTION_LOCAL
from custom_components.mygekko.const import CONF_CONNECTION_MY_GEKKO_CLOUD
from custom_components.mygekko.const import CONF_CONNECTION_TYPE
from custom_components.mygekko.const import DOMAIN

from .const import CLOUD_CONFIG
from .const import CLOUD_INPUT
from .const import DEMO_CONFIG
from .const import LOCAL_CONFIG
from .const import LOCAL_INPUT

TRY_CONNECT = "custom_components.mygekko.api.MyGekkoClient.try_connect"


@pytest.fixture(autouse=True)
def no_setup():
    """Do not set up the integration when a flow creates an entry."""
    with patch("custom_components.mygekko.async_setup_entry", return_value=True):
        yield


async def _select(hass, connection_type):
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    assert result["type"] is FlowResultType.FORM
    return await hass.config_entries.flow.async_configure(
        result["flow_id"], {CONF_CONNECTION_TYPE: connection_type}
    )


async def test_demo_flow(hass):
    """The demo mode needs no credentials."""
    result = await _select(hass, CONF_CONNECTION_DEMO_MODE)
    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert result["data"] == {CONF_CONNECTION_TYPE: CONF_CONNECTION_DEMO_MODE}


async def test_cloud_flow(hass):
    """The cloud flow checks the credentials and creates the entry."""
    result = await _select(hass, CONF_CONNECTION_MY_GEKKO_CLOUD)
    assert result["step_id"] == "connection_mygekko_cloud"
    with patch(TRY_CONNECT, new_callable=AsyncMock):
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"], CLOUD_INPUT
        )
    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert result["data"] == CLOUD_CONFIG


async def test_cloud_flow_rejected_credentials(hass):
    """Rejected credentials show an error and allow another try."""
    result = await _select(hass, CONF_CONNECTION_MY_GEKKO_CLOUD)
    with patch(TRY_CONNECT, side_effect=MyGekkoError("HTTP 403")):
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"], CLOUD_INPUT
        )
    assert result["type"] is FlowResultType.FORM
    assert result["errors"] == {"base": "auth_cloud"}


async def test_cloud_flow_timeout(hass):
    """A timeout does not crash the flow."""
    result = await _select(hass, CONF_CONNECTION_MY_GEKKO_CLOUD)
    with patch(TRY_CONNECT, side_effect=TimeoutError):
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"], CLOUD_INPUT
        )
    assert result["errors"] == {"base": "auth_cloud"}


async def test_cloud_flow_is_unique(hass):
    """The same Gekko cannot be configured twice."""
    MockConfigEntry(
        domain=DOMAIN, version=3, data=CLOUD_CONFIG, unique_id="cloud_A1B2C3"
    ).add_to_hass(hass)
    result = await _select(hass, CONF_CONNECTION_MY_GEKKO_CLOUD)
    with patch(TRY_CONNECT, new_callable=AsyncMock):
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"], CLOUD_INPUT
        )
    assert result["type"] is FlowResultType.ABORT
    assert result["reason"] == "already_configured"


async def test_local_flow(hass):
    """The local flow checks the credentials and creates the entry."""
    result = await _select(hass, CONF_CONNECTION_LOCAL)
    assert result["step_id"] == "connection_local"
    with patch(TRY_CONNECT, new_callable=AsyncMock):
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"], LOCAL_INPUT
        )
    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert result["data"] == {**LOCAL_CONFIG, "scheme": "https"}


async def test_local_flow_falls_back_to_http(hass):
    """A MyGekko that does not answer on https is tried with http (issue StephanU/MyGekko#365)."""
    result = await _select(hass, CONF_CONNECTION_LOCAL)
    with patch(
        TRY_CONNECT,
        new_callable=AsyncMock,
        side_effect=[
            ClientConnectorSSLError(
                ConnectionKey("192.168.1.50", 443, True, True, None, None, None),
                OSError("SSLV3_ALERT_HANDSHAKE_FAILURE"),
            ),
            None,
        ],
    ):
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"], LOCAL_INPUT
        )
    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert result["data"]["scheme"] == "http"


async def test_local_flow_timeout_does_not_fall_back(hass):
    """A slow https MyGekko is not switched to unencrypted http."""
    result = await _select(hass, CONF_CONNECTION_LOCAL)
    with patch(
        TRY_CONNECT, new_callable=AsyncMock, side_effect=TimeoutError
    ) as try_connect:
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"], LOCAL_INPUT
        )
    assert result["errors"] == {"base": "auth_local"}
    assert try_connect.await_count == 1


async def test_local_flow_nothing_answers(hass):
    """Neither https nor http works."""
    result = await _select(hass, CONF_CONNECTION_LOCAL)
    with patch(
        TRY_CONNECT,
        new_callable=AsyncMock,
        side_effect=ClientConnectorError(
            ConnectionKey("192.168.1.50", 443, True, True, None, None, None),
            OSError("refused"),
        ),
    ):
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"], LOCAL_INPUT
        )
    assert result["errors"] == {"base": "auth_local"}


async def test_local_flow_wrong_login_does_not_fall_back(hass):
    """A rejected login is not retried with http."""
    result = await _select(hass, CONF_CONNECTION_LOCAL)
    with patch(
        TRY_CONNECT, new_callable=AsyncMock, side_effect=MyGekkoError("403")
    ) as try_connect:
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"], LOCAL_INPUT
        )
    assert result["errors"] == {"base": "auth_local"}
    assert try_connect.await_count == 1


async def test_local_flow_is_unique(hass):
    """The same local Gekko cannot be configured twice."""
    MockConfigEntry(
        domain=DOMAIN, version=3, data=LOCAL_CONFIG, unique_id="local_192.168.1.50"
    ).add_to_hass(hass)
    result = await _select(hass, CONF_CONNECTION_LOCAL)
    with patch(TRY_CONNECT, new_callable=AsyncMock):
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"], LOCAL_INPUT
        )
    assert result["type"] is FlowResultType.ABORT


async def _reconfigure(hass, entry, user_input):
    result = await entry.start_reconfigure_flow(hass)
    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "reconfigure"
    return await hass.config_entries.flow.async_configure(
        result["flow_id"], user_input
    )


async def test_reconfigure_cloud(hass):
    """The credentials of a cloud entry can be changed."""
    entry = MockConfigEntry(
        domain=DOMAIN, version=3, data=CLOUD_CONFIG, unique_id="cloud_A1B2C3"
    )
    entry.add_to_hass(hass)
    with patch(TRY_CONNECT, new_callable=AsyncMock):
        result = await _reconfigure(hass, entry, {**CLOUD_INPUT, "api_key": "new"})
    assert result["type"] is FlowResultType.ABORT
    assert result["reason"] == "reconfigure_successful"
    assert entry.data["api_key"] == "new"
    assert entry.data[CONF_CONNECTION_TYPE] == CONF_CONNECTION_MY_GEKKO_CLOUD


async def test_reconfigure_local_changes_address(hass):
    """The address of a local entry can be changed."""
    entry = MockConfigEntry(
        domain=DOMAIN, version=3, data=LOCAL_CONFIG, unique_id="local_192.168.1.50"
    )
    entry.add_to_hass(hass)
    with patch(TRY_CONNECT, new_callable=AsyncMock):
        result = await _reconfigure(hass, entry, {**LOCAL_INPUT, "ip_address": "10.0.0.5"})
    assert result["reason"] == "reconfigure_successful"
    assert entry.data["ip_address"] == "10.0.0.5"
    assert entry.unique_id == "local_10.0.0.5"
    assert entry.data["scheme"] == "https"


async def test_reconfigure_local_detects_http(hass):
    """Reconfiguring detects the scheme again and stores it."""
    entry = MockConfigEntry(
        domain=DOMAIN, version=3, data=LOCAL_CONFIG, unique_id="local_192.168.1.50"
    )
    entry.add_to_hass(hass)
    with patch(
        TRY_CONNECT,
        new_callable=AsyncMock,
        side_effect=[
            ClientConnectorError(
                ConnectionKey("192.168.1.50", 443, True, True, None, None, None),
                OSError("refused"),
            ),
            None,
        ],
    ):
        result = await _reconfigure(hass, entry, LOCAL_INPUT)
    assert result["reason"] == "reconfigure_successful"
    assert entry.data["scheme"] == "http"


async def test_reconfigure_wrong_credentials(hass):
    """Wrong credentials keep the old configuration."""
    entry = MockConfigEntry(
        domain=DOMAIN, version=3, data=CLOUD_CONFIG, unique_id="cloud_A1B2C3"
    )
    entry.add_to_hass(hass)
    with patch(TRY_CONNECT, side_effect=MyGekkoError("HTTP 403")):
        result = await _reconfigure(hass, entry, {**CLOUD_INPUT, "api_key": "bad"})
    assert result["type"] is FlowResultType.FORM
    assert result["errors"] == {"base": "auth_cloud"}
    assert entry.data["api_key"] == "secret"


async def test_reconfigure_demo_is_not_supported(hass):
    """The demo mode has nothing to reconfigure."""
    entry = MockConfigEntry(domain=DOMAIN, version=3, data=DEMO_CONFIG)
    entry.add_to_hass(hass)
    result = await entry.start_reconfigure_flow(hass)
    assert result["type"] is FlowResultType.ABORT
    assert result["reason"] == "reconfigure_not_supported"


async def test_reauth_flow(hass):
    """New credentials replace the rejected ones."""
    entry = MockConfigEntry(
        domain=DOMAIN, version=3, data=CLOUD_CONFIG, unique_id="cloud_A1B2C3"
    )
    entry.add_to_hass(hass)
    result = await entry.start_reauth_flow(hass)
    assert result["step_id"] == "reauth_confirm"
    with patch(TRY_CONNECT, new_callable=AsyncMock):
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"], {**CLOUD_INPUT, "api_key": "renewed"}
        )
    assert result["type"] is FlowResultType.ABORT
    assert result["reason"] == "reauth_successful"
    assert entry.data["api_key"] == "renewed"


async def test_reauth_with_wrong_credentials(hass):
    """Wrong credentials are reported and the entry stays unchanged."""
    entry = MockConfigEntry(
        domain=DOMAIN, version=3, data=CLOUD_CONFIG, unique_id="cloud_A1B2C3"
    )
    entry.add_to_hass(hass)
    result = await entry.start_reauth_flow(hass)
    with patch(TRY_CONNECT, side_effect=MyGekkoError("HTTP 403")):
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"], {**CLOUD_INPUT, "api_key": "bad"}
        )
    assert result["errors"] == {"base": "auth_cloud"}
    assert entry.data["api_key"] == "secret"


async def test_reauth_cannot_switch_to_another_gekko(hass):
    """The login of a different MyGekko is not accepted for this entry."""
    entry = MockConfigEntry(
        domain=DOMAIN, version=3, data=CLOUD_CONFIG, unique_id="cloud_A1B2C3"
    )
    entry.add_to_hass(hass)
    result = await entry.start_reauth_flow(hass)
    with patch(TRY_CONNECT, new_callable=AsyncMock):
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"], {**CLOUD_INPUT, "gekkoid": "OTHER"}
        )
    assert result["type"] is FlowResultType.ABORT
    assert result["reason"] == "wrong_account"
    assert entry.data["gekkoid"] == "A1B2C3"
