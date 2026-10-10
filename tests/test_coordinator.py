"""Tests for the polling behavior of the coordinator."""
from datetime import timedelta
from unittest.mock import patch

from custom_components.mygekko import coordinator as coordinator_module
from custom_components.mygekko.api import MyGekkoTooManyRequests

READ_DATA = "custom_components.mygekko.api.MyGekkoDemoModeClient.read_data"


async def test_rate_limit_skips_polls_and_keeps_entities_available(hass, setup_demo):
    """HTTP 429 skips the poll, the entities keep their values."""
    coordinator = setup_demo.runtime_data
    light = hass.states.get("light.kitchen")
    assert light.state == "on"

    with patch(READ_DATA, side_effect=MyGekkoTooManyRequests("429")):
        for skipped in range(1, coordinator_module.MAX_SKIPPED_POLLS + 1):
            coordinator._backoff_until = 0
            await coordinator.async_refresh()
            assert coordinator.last_update_success
            assert hass.states.get("light.kitchen").state == "on"
            assert coordinator._skipped_polls == skipped

        # the interval grows, but never beyond the maximum
        assert coordinator.update_interval == coordinator_module.MAX_BACKOFF_INTERVAL

        # the rate limit persists: now the problem becomes visible
        coordinator._backoff_until = 0
        await coordinator.async_refresh()
        assert not coordinator.last_update_success


async def test_refresh_is_dropped_during_backoff(hass, setup_demo):
    """No request is sent while the rate limit backoff is active."""
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
    assert coordinator.update_interval > coordinator_module.SCAN_INTERVAL

    coordinator._backoff_until = 0
    await coordinator.async_refresh()
    assert coordinator.last_update_success
    assert coordinator.update_interval == coordinator_module.SCAN_INTERVAL
    assert coordinator._skipped_polls == 0
    assert coordinator.update_interval == timedelta(seconds=30)


async def test_errors_become_update_failed_with_message(hass, setup_demo):
    """Other errors mark the update as failed with a readable message."""
    coordinator = setup_demo.runtime_data
    with patch(READ_DATA, side_effect=TimeoutError):
        await coordinator.async_refresh()
    assert not coordinator.last_update_success
    assert "Timeout" in str(coordinator.last_exception)
