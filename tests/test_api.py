"""Tests for MyGekko api."""
import pytest
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from PyMyGekko import MyGekkoApiClient


@pytest.mark.asyncio
async def test_api(hass, aioclient_mock, caplog):
    """Test API calls."""

    # To test the api submodule, we first create an instance of our API client
    api = MyGekkoApiClient("test", "test", "test", async_get_clientsession(hass))

    # Use aioclient_mock which is provided by `pytest_homeassistant_custom_components`
    # to mock responses to aiohttp requests. In this case we are telling the mock to
    # return {"test": "test"} when a `GET` call is made to the specified URL. We then
    # call `get_blinds` which will make that `GET` request.
    aioclient_mock.get(
        "https://live.my-gekko.com/api/v1/var?username=test&key=test&gekkoid=test",
        json={
            "blinds": {
                "item0": {
                    "name": "Wohnen Terrasse",
                    "page": "...",
                    "sumstate": {
                        "value": "state[-2=Hold_down|-1=Down|0=Stop|1=Up|2=Hold_up]; position[%]; angle[°]; sum[0=Ok|1=ManualOff|2=ManualOn|3=Locked|4=Alarm]; slatRotationArea[°]",
                        "type": "STRING",
                        "permission": "READ",
                        "index": 150000,
                    },
                    "scmd": {
                        "value": "-2|-1|0|1|2|T|P55.4|S32.4 (Hold_down|Down|Stop|Up|Hold_up|Toggle|Position|Angle)",
                        "type": "STRING",
                        "permission": "WRITE",
                        "index": 150070,
                    },
                }
            }
        },
    )
    aioclient_mock.get(
        "https://live.my-gekko.com/api/v1/var/status?username=test&key=test&gekkoid=test",
        json={"blinds": {"item0": {"sumstate": {"value": "0;100.00;;0;90"}}}},
    )
    await api.read_data()
    assert len(api.get_blinds()) == 1
