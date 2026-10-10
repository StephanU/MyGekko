"""Tests for the MyGekko API client."""
import asyncio
import json

import aiohttp
import pytest
import pytest_asyncio
from aiohttp import web
from aiohttp.test_utils import TestServer
from custom_components.mygekko import api
from custom_components.mygekko.api import client as client_module
from custom_components.mygekko.api.store import ResourceStore

DEMO_DIR = "custom_components/mygekko/api/demo/"


def _load(name):
    with open(DEMO_DIR + name, encoding="utf-8") as file:
        return json.load(file)


@pytest_asyncio.fixture
async def server():
    """Run a fake MyGekko whose behavior can be switched per test."""
    state = {"mode": "ok", "calls": [], "resources": _load("api_var_demo_data.json")}

    async def var(request):
        state["calls"].append(request.path)
        if state["mode"] == "429":
            return web.json_response({"reason": "Too Many Requests"}, status=429)
        if state["mode"] == "html":
            return web.Response(text="<html>", status=200)
        if state["mode"] == "hang":
            await asyncio.sleep(30)
        return web.json_response(state["resources"])

    async def status(request):
        state["calls"].append(request.path)
        if state["mode"] == "429":
            return web.json_response({}, status=429)
        return web.json_response(_load("api_var_status_demo_data.json"))

    async def command(request):
        state["calls"].append(f"{request.path}?{request.query_string}")
        return web.Response(text="ok")

    app = web.Application()
    app.router.add_get("/api/v1/var", var)
    app.router.add_get("/api/v1/var/status", status)
    app.router.add_get(r"/api/v1/var/{tail:.*}/scmd/set", command)
    test_server = TestServer(app)
    await test_server.start_server()
    yield test_server, state
    await test_server.close()


def _client(session, test_server):
    return api.MyGekkoHttpClient(
        session,
        "127.0.0.1",
        {"username": "u", "password": "p"},
        scheme="http",
        port=test_server.port,
    )


@pytest.mark.asyncio
async def test_demo_client_reads_devices():
    """The demo client provides all device types."""
    demo = api.MyGekkoDemoModeClient()
    await demo.read_data()
    assert demo.get_lights()
    assert demo.get_clocks()
    assert demo.get_energy_managers()
    assert demo.get_globals_network()["gekkoname"]


@pytest.mark.asyncio
async def test_resources_are_read_once(server):
    """Only the status is polled after the first read."""
    test_server, state = server
    async with aiohttp.ClientSession() as session:
        gekko = _client(session, test_server)
        await gekko.read_data()
        await gekko.read_data()
    assert state["calls"].count("/api/v1/var") == 1
    assert state["calls"].count("/api/v1/var/status") == 2
    assert gekko.get_lights()


@pytest.mark.asyncio
async def test_resources_are_read_again_for_new_devices(server):
    """A device that appears in the status triggers a refresh of the names."""
    test_server, state = server
    async with aiohttp.ClientSession() as session:
        gekko = _client(session, test_server)
        await gekko.read_data()
        del gekko.store._devices["lights"]["item0"]["name"]
        await gekko.read_data()
        assert state["calls"].count("/api/v1/var") == 2
        # a device that stays unnamed does not trigger a refresh on every poll
        state["resources"]["lights"].pop("item1")
        await gekko.read_data()
        calls = state["calls"].count("/api/v1/var")
        await gekko.read_data()
        await gekko.read_data()
    assert state["calls"].count("/api/v1/var") == calls


@pytest.mark.asyncio
async def test_rate_limit_raises(server):
    """HTTP 429 becomes MyGekkoTooManyRequests."""
    test_server, state = server
    state["mode"] = "429"
    async with aiohttp.ClientSession() as session:
        with pytest.raises(api.MyGekkoTooManyRequests):
            await _client(session, test_server).read_data()


@pytest.mark.asyncio
async def test_invalid_json_raises(server):
    """A response that is no JSON is an error and not a silent success."""
    test_server, state = server
    async with aiohttp.ClientSession() as session:
        gekko = _client(session, test_server)
        await gekko.read_data()
        state["mode"] = "html"
        gekko._resources_read_at = None
        with pytest.raises(api.MyGekkoError):
            await gekko.read_data()


@pytest.mark.asyncio
async def test_timeout(server, monkeypatch):
    """A hanging device ends in a timeout."""
    test_server, state = server
    state["mode"] = "hang"
    monkeypatch.setattr(
        client_module, "REQUEST_TIMEOUT", aiohttp.ClientTimeout(total=0.5)
    )
    async with aiohttp.ClientSession() as session:
        with pytest.raises(TimeoutError):
            await _client(session, test_server).read_data()


@pytest.mark.asyncio
async def test_commands(server):
    """Commands are sent to the scmd/set endpoint."""
    test_server, state = server
    async with aiohttp.ClientSession() as session:
        gekko = _client(session, test_server)
        await gekko.read_data()
        light = gekko.get_lights()[0]
        await light.set_state(api.LightState.ON)
        await light.set_brightness(40)
        await light.set_rgb_color((1, 2, 3))
        await gekko.get_vents()[0].set_working_level(api.VentWorkingLevel.OFF)
    commands = [call for call in state["calls"] if "scmd" in call]
    assert commands[0].endswith("/scmd/set?username=u&password=p&value=1")
    assert commands[1].endswith("value=D40")
    assert commands[2].endswith(f"value=C{(1 << 16) + (2 << 8) + 3}")
    assert commands[3].endswith("value=-1")


def test_tolerant_parsing():
    """Missing, short or invalid values never raise."""
    store = ResourceStore()
    store.update_resources({"lights": {"item0": {"name": "L"}, "group0": {"name": "G"}}})
    store.update_status(
        {
            "lights": {
                "item0": {"sumstate": {"value": "1;x"}},
                "group0": {"sumstate": {"value": "0;5"}},
            },
            "roomtemps": {"item9": {"sumstate": None}},
        }
    )
    gekko = api.MyGekkoDemoModeClient()
    gekko.store = store
    light, group = gekko.get_lights()
    assert light.state == api.LightState.ON
    assert light.brightness is None
    assert group.state == api.LightState.OFF
    # an invalid value is still a reported value, so the feature is detected
    assert light.supported_features == [
        api.enums.LightFeature.ON_OFF,
        api.enums.LightFeature.DIMMABLE,
    ]
