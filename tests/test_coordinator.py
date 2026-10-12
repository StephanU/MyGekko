"""Tests for the polling behavior of the coordinator."""
import json
from datetime import timedelta
from unittest.mock import patch

from homeassistant.helpers import issue_registry as ir
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.mygekko import coordinator as coordinator_module
from custom_components.mygekko.api import MyGekkoForbidden
from custom_components.mygekko.api import MyGekkoTooManyRequests
from custom_components.mygekko.const import DOMAIN

from .const import CLOUD_CONFIG
from .const import DEMO_CONFIG

def _demo(name):
    with open(f"custom_components/mygekko/api/demo/{name}", encoding="utf-8") as file:
        return json.load(file)


READ_DATA = "custom_components.mygekko.api.MyGekkoDemoModeClient.read_data"


async def test_rate_limit_pauses_and_keeps_entities_available(hass, setup_demo):
    """HTTP 429 pauses the requests for 4 minutes, the entities keep their values."""
    coordinator = setup_demo.runtime_data
    assert hass.states.get("light.kitchen").state == "on"

    with patch(READ_DATA, side_effect=MyGekkoTooManyRequests("429")):
        for _ in range(10):
            coordinator._backoff_until = 0
            await coordinator.async_refresh()
            assert coordinator.last_update_success
            assert hass.states.get("light.kitchen").state == "on"
    assert coordinator.update_interval == coordinator_module.RATE_LIMIT_PAUSE
    assert coordinator.api_state == coordinator_module.API_STATE_RATE_LIMITED
    assert coordinator.rate_limited_until is not None
    assert hass.states.get("sensor.mygekko_demo_api_status").state == "rate_limited"


async def test_refresh_is_dropped_during_backoff(hass, setup_demo):
    """No request is sent while the rate limit pause is active."""
    coordinator = setup_demo.runtime_data
    with patch(READ_DATA, side_effect=MyGekkoTooManyRequests("429")) as read_data:
        await coordinator.async_refresh()
        calls = read_data.call_count
        await coordinator.async_refresh()
        await coordinator.async_refresh()
    assert read_data.call_count == calls


async def test_recovery_restores_the_interval(hass, setup_demo):
    """After a successful poll the normal interval is back."""
    coordinator = setup_demo.runtime_data
    with patch(READ_DATA, side_effect=MyGekkoTooManyRequests("429")):
        await coordinator.async_refresh()
    assert coordinator.update_interval > coordinator.base_interval

    coordinator._backoff_until = 0
    await coordinator.async_refresh()
    assert coordinator.last_update_success
    assert coordinator.api_state == coordinator_module.API_STATE_OK
    assert coordinator.rate_limited_until is None
    assert coordinator.update_interval == timedelta(seconds=30)


async def test_errors_keep_the_state_for_a_while(hass, setup_demo, freezer):
    """A failing poll keeps the last state, a lasting outage becomes visible."""
    coordinator = setup_demo.runtime_data
    with patch(READ_DATA, side_effect=TimeoutError):
        await coordinator.async_refresh()
        assert coordinator.last_update_success
        assert hass.states.get("light.kitchen").state == "on"
        assert coordinator.api_state == coordinator_module.API_STATE_ERROR

        freezer.tick(coordinator_module.ERROR_GRACE)
        await coordinator.async_refresh()
    assert not coordinator.last_update_success
    assert "Timeout" in str(coordinator.last_exception)
    assert hass.states.get("light.kitchen").state == "unavailable"
    # the connection state stays visible
    assert hass.states.get("sensor.mygekko_demo_api_status").state == "error"

    await coordinator.async_refresh()
    assert hass.states.get("light.kitchen").state == "on"


async def test_persistent_rate_limit_creates_a_repair_issue(hass, setup_demo, freezer):
    """A rate limit that does not go away is reported, and cleared on recovery."""
    coordinator = setup_demo.runtime_data
    registry = ir.async_get(hass)
    issue_id = f"rate_limited_{setup_demo.entry_id}"

    with patch(READ_DATA, side_effect=MyGekkoTooManyRequests("429")):
        await coordinator.async_refresh()
        assert registry.async_get_issue(DOMAIN, issue_id) is None

        freezer.tick(coordinator_module.RATE_LIMIT_ISSUE_AFTER)
        coordinator._backoff_until = 0
        await coordinator.async_refresh()
    assert coordinator.last_update_success
    issue = registry.async_get_issue(DOMAIN, issue_id)
    assert issue is not None
    assert issue.translation_key == "rate_limited"

    coordinator._backoff_until = 0
    await coordinator.async_refresh()
    assert registry.async_get_issue(DOMAIN, issue_id) is None


async def test_restart_uses_the_saved_state(hass, setup_demo):
    """After a restart during a rate limit the saved state is shown, no request is sent."""
    coordinator = setup_demo.runtime_data
    with patch(READ_DATA, side_effect=MyGekkoTooManyRequests("429")):
        await coordinator.async_refresh()
    saved = coordinator._cache_data()

    await hass.config_entries.async_unload(setup_demo.entry_id)
    with patch(
        "homeassistant.helpers.storage.Store.async_load", return_value=saved
    ), patch(READ_DATA) as read_data:
        await hass.config_entries.async_setup(setup_demo.entry_id)
        await hass.async_block_till_done()
    assert read_data.call_count == 0
    assert setup_demo.runtime_data.api_state == coordinator_module.API_STATE_RATE_LIMITED
    assert hass.states.get("light.kitchen").state == "on"


async def test_startup_error_uses_the_saved_state(hass, setup_demo):
    """MyGekko not reachable at startup: the saved state is used."""
    saved = setup_demo.runtime_data._cache_data()
    saved["rate_limited_until"] = None
    await hass.config_entries.async_unload(setup_demo.entry_id)
    with patch(
        "homeassistant.helpers.storage.Store.async_load", return_value=saved
    ), patch(READ_DATA, side_effect=MyGekkoTooManyRequests("429")):
        await hass.config_entries.async_setup(setup_demo.entry_id)
        await hass.async_block_till_done()
    assert hass.states.get("light.kitchen").state == "on"
    assert setup_demo.runtime_data.is_backing_off


async def test_failed_write_pauses_the_polls(hass, setup_demo):
    """A command rejected with HTTP 429 also pauses the polls."""
    coordinator = setup_demo.runtime_data
    setup_demo.write.side_effect = MyGekkoTooManyRequests("429")
    await hass.services.async_call(
        "light", "turn_off", {"entity_id": "light.kitchen"}, blocking=True
    )
    assert coordinator.is_backing_off
    assert coordinator._queued
    coordinator.async_cancel_queued()
    assert hass.states.get("light.kitchen").state == "on"


async def test_configured_interval_is_the_base_interval(hass):
    """The poll interval of the options is used."""
    entry = MockConfigEntry(
        domain=DOMAIN,
        version=3,
        data=DEMO_CONFIG,
        options={"scan_interval": 120},
        unique_id="demo-interval",
    )
    entry.add_to_hass(hass)
    await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()
    assert entry.runtime_data.update_interval == timedelta(seconds=120)


async def test_backoff_never_polls_faster_than_configured(hass):
    """With a long configured interval a rate limit does not shorten it."""
    entry = MockConfigEntry(
        domain=DOMAIN,
        version=3,
        data=DEMO_CONFIG,
        options={"scan_interval": 600},
        unique_id="slow",
    )
    entry.add_to_hass(hass)
    await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()
    coordinator = entry.runtime_data
    with patch(READ_DATA, side_effect=MyGekkoTooManyRequests("429")):
        await coordinator.async_refresh()
    assert coordinator.update_interval >= timedelta(seconds=600)


async def test_single_rate_limit_at_startup_creates_no_issue(hass):
    """The repair issue is for a rate limit that persists, not for the first one."""
    entry = MockConfigEntry(domain=DOMAIN, version=3, data=DEMO_CONFIG, unique_id="s")
    entry.add_to_hass(hass)
    with patch(READ_DATA, side_effect=MyGekkoTooManyRequests("429")):
        await hass.config_entries.async_setup(entry.entry_id)
    assert ir.async_get(hass).async_get_issue(DOMAIN, f"rate_limited_{entry.entry_id}") is None


async def test_rejected_requests_ask_for_login_after_a_few_times(hass):
    """A rejection is tolerated twice, the third one starts the re-authentication."""
    # the flow handler is registered when Home Assistant loads the config flow
    from custom_components.mygekko import config_flow  # noqa: F401

    entry = MockConfigEntry(
        domain=DOMAIN, version=3, data=CLOUD_CONFIG, unique_id="cloud_A1B2C3"
    )
    entry.add_to_hass(hass)
    with patch(
        "custom_components.mygekko.api.MyGekkoHttpClient._fetch_resources",
        return_value=_demo("api_var_demo_data.json"),
    ), patch(
        "custom_components.mygekko.api.MyGekkoHttpClient._fetch_status",
        return_value=_demo("api_var_status_demo_data.json"),
    ):
        await hass.config_entries.async_setup(entry.entry_id)
        await hass.async_block_till_done()
    coordinator = entry.runtime_data

    with patch(
        "custom_components.mygekko.api.MyGekkoHttpClient.read_data",
        side_effect=MyGekkoForbidden("403"),
    ):
        for _ in range(coordinator_module.MAX_AUTH_FAILURES - 1):
            await coordinator.async_refresh()
            assert coordinator.api_state == coordinator_module.API_STATE_ERROR
            assert not hass.config_entries.flow.async_progress_by_handler(DOMAIN)
        await coordinator.async_refresh()
    await hass.async_block_till_done()
    flows = hass.config_entries.flow.async_progress_by_handler(DOMAIN)
    assert [flow["context"]["source"] for flow in flows] == ["reauth"]


async def test_retried_setup_waits_for_the_pause(hass):
    """A rate limit at the first start: the retried setup sends no request until the pause ends."""
    entry = MockConfigEntry(domain=DOMAIN, version=3, data=DEMO_CONFIG, unique_id="p")
    entry.add_to_hass(hass)
    with patch(READ_DATA, side_effect=MyGekkoTooManyRequests("429")) as read_data:
        await hass.config_entries.async_setup(entry.entry_id)
        await hass.config_entries.async_unload(entry.entry_id)
        await hass.config_entries.async_setup(entry.entry_id)
    assert read_data.call_count == 1
