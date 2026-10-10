"""Tests for devices that are not part of the demo data (cameras, intercom, weather)."""
import json
from unittest.mock import patch

import pytest
from homeassistant.config_entries import ConfigEntryState
from homeassistant.components.camera import async_get_image
from homeassistant.components.camera import CameraEntityFeature
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.mygekko.const import DOMAIN

from .const import DEMO_CONFIG

DEMO = "custom_components/mygekko/api/demo/"


def _load(name):
    with open(DEMO + name, encoding="utf-8") as file:
        return json.load(file)


@pytest.fixture
async def extended_entry(hass):
    """Set up the demo mode with a camera, a door intercom and a weather station."""
    resources = _load("api_var_demo_data.json")
    status = _load("api_var_status_demo_data.json")
    resources["cams"] = {
        "item0": {"name": "Garden", "imagepath": "http://cam.local/garden.jpg"},
        "item1": {
            "name": "Street",
            "imagepath": "https://cam.local/street.jpg",
            "streampath": "rtsp://cam.local/street",
        },
    }
    status["cams"] = {"item0": {"sumstate": {"value": "0"}}, "item1": {"sumstate": {"value": "1"}}}
    resources["door_intercom"] = {
        "item0": {
            "name": "Door",
            "imagepath": "http://door.local/image.jpg",
            "streampath": "rtsp://door.local/stream",
        }
    }
    status["door_intercom"] = {
        "item0": {"sumstate": {"value": "1;0;1;2;01.01.2026 10:00:00"}}
    }
    status["globals"]["meteo"] = {
        "rain": {"value": "60"},
        "temperature": {"value": "21.5"},
        "wind": {"value": "0"},
    }

    entry = MockConfigEntry(domain=DOMAIN, version=3, data=DEMO_CONFIG, unique_id="x")
    entry.add_to_hass(hass)
    with patch(
        "custom_components.mygekko.api.MyGekkoDemoModeClient._fetch_resources",
        return_value=resources,
    ), patch(
        "custom_components.mygekko.api.MyGekkoDemoModeClient._fetch_status",
        return_value=status,
    ):
        await hass.config_entries.async_setup(entry.entry_id)
        await hass.async_block_till_done()
    assert entry.state is ConfigEntryState.LOADED
    return entry


async def test_cameras(hass, extended_entry, aioclient_mock):
    """Cameras provide an image and optionally a stream."""
    aioclient_mock.get("http://cam.local/garden.jpg", content=b"garden")
    aioclient_mock.get("https://cam.local/street.jpg", content=b"street")

    garden = hass.states.get("camera.garden")
    street = hass.states.get("camera.street")
    assert garden is not None
    assert street is not None
    assert not garden.attributes["supported_features"] & CameraEntityFeature.STREAM
    assert street.attributes["supported_features"] & CameraEntityFeature.STREAM

    assert (await async_get_image(hass, "camera.garden")).content == b"garden"
    assert (await async_get_image(hass, "camera.street")).content == b"street"


async def test_camera_image_errors_are_not_fatal(hass, extended_entry, aioclient_mock):
    """A camera that is not reachable returns no image, but no crash."""
    aioclient_mock.get("http://cam.local/garden.jpg", status=500)
    with pytest.raises(Exception, match="Unable to get image"):
        await async_get_image(hass, "camera.garden")


async def test_door_intercom(hass, extended_entry, aioclient_mock):
    """The door intercom provides a camera and sensors."""
    aioclient_mock.get("http://door.local/image.jpg", content=b"door")
    assert (await async_get_image(hass, "camera.door")).content == b"door"
    states = {state.entity_id: state for state in hass.states.async_all("sensor")}
    door = {key: value.state for key, value in states.items() if "door" in key}
    assert door, states.keys()
    assert "2" in door.values() or "ringing" in door.values() or "mute" in door.values()


async def test_weather_sensors_only_for_reported_values(hass, extended_entry):
    """Only the weather values that the station reports become sensors."""
    weather = {
        state.entity_id: state.state
        for state in hass.states.async_all("sensor")
        if state.entity_id.startswith("sensor.weather_")
    }
    assert set(weather) == {
        "sensor.weather_rain",
        "sensor.weather_temperature",
        "sensor.weather_wind",
    }
    assert float(weather["sensor.weather_rain"]) == 1.0  # 60 l/h are 1 l/min
    assert float(weather["sensor.weather_temperature"]) == 21.5
    assert float(weather["sensor.weather_wind"]) == 0.0  # zero is a value, not unknown
