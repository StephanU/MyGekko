"""Tests for MyGekko api."""
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from PyMyGekko import MyGekkoApiClient


async def test_api(hass, aioclient_mock, caplog):
    """Test API calls."""

    # To test the api submodule, we first create an instance of our API client
    api = MyGekkoApiClient("test", "test", "test", async_get_clientsession(hass))

    # Use aioclient_mock which is provided by `pytest_homeassistant_custom_components`
    # to mock responses to aiohttp requests. In this case we are telling the mock to
    # return {"test": "test"} when a `GET` call is made to the specified URL. We then
    # call `get_blinds` which will make that `GET` request.
    aioclient_mock.get("https://live.my-gekko.com/api/v1/var", json={"test": "test"})
    assert await api.get_blinds() == {"test": "test"}
