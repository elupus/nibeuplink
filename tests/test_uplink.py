"""Test the uplink class."""
from aioresponses import aioresponses, CallbackResult

from pytest import fixture

from nibeuplink.session import UplinkSession
from nibeuplink.typing import SetThermostatModel
from nibeuplink.uplink import Uplink


MOCK_CLIENT_ID = "1234"
MOCK_CLIENT_SECRET = "5678"
MOCK_REDIRECT_URI = "https://localhost.example:1234/auth"
MOCK_BASE_URL = "https://api.nibeuplink.com"
MOCK_SYSTEMID = 1

MOCK_SYSTEM_1 = {
    "systemId": MOCK_SYSTEMID,
    "name": "sample string 2",
    "productName": "sample string 3",
    "productImage": {
        "name": "sample string 1",
        "sizes": [
            {"width": 1, "height": 2, "url": "sample string 3"},
            {"width": 1, "height": 2, "url": "sample string 3"},
        ],
    },
    "securityLevel": "ADMIN",
    "serialNumber": "sample string 4",
    "lastActivityDate": "2020-09-16T13:15:05Z",
    "connectionStatus": "ONLINE",
    "address": {
        "addressLine1": "sample string 1",
        "addressLine2": "sample string 2",
        "postalCode": "sample string 3",
        "city": "sample string 4",
        "region": "sample string 5",
        "country": "UNKNOWN",
    },
    "hasAlarmed": True,
}


@fixture(name="aioresp")
async def aioresp_fixture(loop):
    with aioresponses() as m:
        yield m


@fixture(name="uplink")
async def uplink_fixture(aioresp: aioresponses):
    async with UplinkSession(
        MOCK_CLIENT_ID, MOCK_CLIENT_SECRET, MOCK_REDIRECT_URI
    ) as session:
        uplink = Uplink(session)
        yield uplink


async def test_get_system(aioresp: aioresponses, uplink: Uplink):
    aioresp.add(
        f"https://api.nibeuplink.com/api/v1/systems/{MOCK_SYSTEMID}",
        method="GET",
        payload=MOCK_SYSTEM_1,
    )
    result = await uplink.get_system(MOCK_SYSTEMID)
    assert result == MOCK_SYSTEM_1


async def test_post_smarthome_thermostats(aioresp: aioresponses, uplink: Uplink):
    def _callback(url, json, **kwargs):
        assert json == {
            "externalId": 1,
            "name": "name1",
            "actualTemp": 30,
            "targetTemp": None,
            "valuePosition": None,
            "climateSystems": [1],
        }
        return CallbackResult(method="POST")

    aioresp.add(
        f"https://api.nibeuplink.com/api/v1/systems/{MOCK_SYSTEMID}/smarthome/thermostats",
        method="POST",
        callback=_callback,
    )

    thermostat = SetThermostatModel(
        externalId=1,
        name="name1",
        actualTemp=30,
        targetTemp=None,
        valuePosition=None,
        climateSystems=[1],
    )
    await uplink.post_smarthome_thermostats(MOCK_SYSTEMID, thermostat)
