"""Tests for the commands sent by the platforms."""
import pytest
from homeassistant.exceptions import HomeAssistantError

from custom_components.mygekko import coordinator as coordinator_module
from custom_components.mygekko.api import MyGekkoTooManyRequests


async def _call(hass, domain, service, entity_id, **data):
    await hass.services.async_call(
        domain, service, {"entity_id": entity_id, **data}, blocking=True
    )
    await hass.async_block_till_done()


def _sent(entry):
    """Return the (path, value) pairs of the commands that were sent."""
    return [call.args for call in entry.write.call_args_list]


@pytest.mark.parametrize(
    ("domain", "service", "entity_id", "data", "value"),
    [
        ("light", "turn_on", "light.bedroom", {}, "1"),
        ("light", "turn_off", "light.kitchen", {}, "0"),
        ("light", "turn_on", "light.living_room", {"brightness": 128}, "D50"),
        ("cover", "open_cover", "cover.bedroom", {}, "2"),
        ("cover", "close_cover", "cover.bedroom", {}, "-2"),
        ("cover", "stop_cover", "cover.bedroom", {}, "0"),
        ("cover", "set_cover_position", "cover.bedroom", {"position": 30}, "P70.0"),
        ("cover", "set_cover_tilt_position", "cover.bedroom", {"tilt_position": 40}, "S60.0"),
        ("switch", "turn_off", "switch.wallbox_garage_charging", {}, "-1"),
        ("switch", "turn_on", "switch.wallbox_garage_charging", {}, "1"),
        ("climate", "set_temperature", "climate.bedroom", {"temperature": 21.5}, "S21.5"),
        ("climate", "set_preset_mode", "climate.bedroom", {"preset_mode": "comfort"}, "M8"),
        ("select", "select_option", "select.ventilation_level", {"option": "0"}, "-1"),
        ("select", "select_option", "select.ventilation_level", {"option": "3"}, "3"),
        ("select", "select_option", "select.schiebeturen", {"option": "off"}, "0"),
        ("water_heater", "turn_off", "water_heater.hot_water_boiler", {}, "0"),
        ("water_heater", "set_temperature", "water_heater.hot_water_boiler", {"temperature": 50}, "T50.0"),
        ("scene", "turn_on", "scene.mygekko_demo_heating_on", {}, "1"),
        ("button", "press", "button.all_switch_on", {}, "1"),
        ("button", "press", "button.all_switch_off", {}, "0"),
    ],
)
async def test_service_sends_command(hass, setup_demo, domain, service, entity_id, data, value):
    """Every service sends the expected value to MyGekko."""
    await _call(hass, domain, service, entity_id, **data)
    assert len(_sent(setup_demo)) == 1
    assert _sent(setup_demo)[0][1] == value


async def test_rgb_color_command(hass, setup_demo):
    """RGB colors are sent as decimal color."""
    registry = hass.states.async_all("light")
    rgb = [s.entity_id for s in registry if "rgb_color" in s.attributes.get("supported_color_modes", [])]
    if not rgb:
        pytest.skip("no RGB light in the demo data")
    await _call(hass, "light", "turn_on", rgb[0], rgb_color=[1, 2, 3])
    assert _sent(setup_demo)[0][1] == f"C{(1 << 16) + (2 << 8) + 3}"


async def test_rate_limited_command_is_retried_then_reported(hass, setup_demo):
    """A rate limited command is retried and finally reported to the user."""
    setup_demo.write.side_effect = MyGekkoTooManyRequests("429")
    with pytest.raises(HomeAssistantError, match="rate limit"):
        await _call(hass, "light", "turn_on", "light.bedroom")
    assert setup_demo.write.call_count == coordinator_module.WRITE_RETRIES


async def test_command_recovers_after_one_rate_limit(hass, setup_demo):
    """One 429 is absorbed by the retry."""
    setup_demo.write.side_effect = [MyGekkoTooManyRequests("429"), None]
    await _call(hass, "light", "turn_on", "light.bedroom")
    assert setup_demo.write.call_count == 2


async def test_commands_are_sent_one_after_another(hass, setup_demo):
    """Concurrent commands never run in parallel."""
    import asyncio

    running = 0
    peak = 0

    async def slow_write(*_args):
        nonlocal running, peak
        running += 1
        peak = max(peak, running)
        await asyncio.sleep(0.01)
        running -= 1

    setup_demo.write.side_effect = slow_write
    await asyncio.gather(
        _call(hass, "light", "turn_on", "light.bedroom"),
        _call(hass, "light", "turn_off", "light.kitchen"),
        _call(hass, "switch", "turn_off", "switch.wallbox_garage_charging"),
    )
    assert peak == 1


async def test_presets_have_readable_ids(hass, setup_demo):
    """The working modes are offered as off, comfort, reduced, manual and standby."""
    state = hass.states.get("climate.living_room")
    assert state.attributes["preset_modes"] == [
        "off", "comfort", "reduced", "manual", "standby",
    ]
    assert state.attributes["preset_mode"] == "comfort"


async def test_no_deprecation_warnings_of_the_integration(hass, setup_demo, caplog):
    """The integration uses the temperature API that matches the installed version."""
    await hass.async_block_till_done()
    deprecations = [
        record.getMessage()
        for record in caplog.records
        if "custom_components.mygekko" in record.getMessage()
        and "deprecated" in record.getMessage()
    ]
    assert not deprecations
