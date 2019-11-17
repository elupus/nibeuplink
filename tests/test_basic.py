import logging
import pytest
import nibeuplink
import asyncio
import fake_uplink
from datetime import datetime, timedelta

logging.basicConfig(level=logging.DEBUG)


DEFAULT_CLIENT_ID = "12345"
DEFAULT_CLIENT_SECRET = "4567"
DEFAULT_SCOPE = ["A", "B", "C"]
DEFAULT_CODE = "789"

DEFAULT_SYSTEMID = 123456


def fin_async(loop, coro):
    def fun():
        loop.run_until_complete(coro())

    return fun


@pytest.mark.asyncio
@pytest.fixture
async def default_uplink(loop, request):
    def access_write(data):
        pass

    server = fake_uplink.Uplink(loop)

    request.addfinalizer(fin_async(loop, server.stop))

    await server.start()

    uplink = nibeuplink.Uplink(
        DEFAULT_CLIENT_ID,
        DEFAULT_CLIENT_SECRET,
        server.redirect,
        None,
        access_write,
        scope=DEFAULT_SCOPE,
        base=server.base,
    )

    request.addfinalizer(fin_async(loop, uplink.close))

    # Override the default throttling to 0 to speed up tests
    uplink.THROTTLE = timedelta(seconds=0)
    return uplink, server


@pytest.mark.asyncio
@pytest.fixture
async def uplink_with_data(loop, default_uplink):

    default_uplink[1].add_system(DEFAULT_SYSTEMID)

    default_uplink[1].add_parameter(
        DEFAULT_SYSTEMID,
        {
            "parameterId": 100,
            "displayValue": "100 Unit",
            "name": "100",
            "title": "Paramter Title",
            "unit": "Unit",
            "designation": "Designation",
            "rawValue": 100,
        },
    )

    default_uplink[1].add_parameter(
        DEFAULT_SYSTEMID,
        {
            "parameterId": 120,
            "displayValue": "120 Units",
            "name": "onehundredtwenty",
            "title": "One Hundred Twenty",
            "unit": "Units",
            "designation": "Designation",
            "rawValue": 250,
        },
    )

    default_uplink[1].add_parameter(
        DEFAULT_SYSTEMID,
        {
            "parameterId": 120,
            "displayValue": "120 Units",
            "name": "120",
            "title": "One Hundred Twenty",
            "unit": "Units",
            "designation": "Designation",
            "rawValue": 250,
        },
    )

    # Make sure we have a token
    await default_uplink[0].get_access_token(DEFAULT_CODE)

    return default_uplink[0], default_uplink[1]


@pytest.mark.asyncio
async def test_status(default_uplink):
    assert not default_uplink[0].access_data


@pytest.mark.asyncio
async def test_get_authorize_url(default_uplink):
    from urllib.parse import urlsplit, parse_qs

    o = urlsplit(default_uplink[0].get_authorize_url())
    q = parse_qs(o.query)

    assert q["response_type"] == ["code"]
    assert q["client_id"] == [DEFAULT_CLIENT_ID]
    assert q["redirect_uri"] == [default_uplink[1].redirect]
    assert q["scope"] == [" ".join(DEFAULT_SCOPE)]


@pytest.mark.asyncio
async def test_get_code_from_url(default_uplink):
    from urllib.parse import urlsplit, parse_qs

    o = urlsplit(default_uplink[0].get_authorize_url())
    q = parse_qs(o.query)

    # valid state
    url = "{}?state={}&code={}".format(
        default_uplink[1].redirect, q["state"][0], DEFAULT_CODE
    )
    assert DEFAULT_CODE == default_uplink[0].get_code_from_url(url)

    # no state
    url = "{}?code={}".format(default_uplink[1].redirect, DEFAULT_CODE)
    assert DEFAULT_CODE == default_uplink[0].get_code_from_url(url)

    # invalid state
    url = "{}?state={}&code={}".format(default_uplink[1].redirect, "junk", DEFAULT_CODE)
    with pytest.raises(ValueError):
        default_uplink[0].get_code_from_url(url)


@pytest.mark.asyncio
async def test_get_get_access_token(default_uplink):
    await default_uplink[0].get_access_token("code_sample")


@pytest.mark.asyncio
async def test_auth_flow(default_uplink):
    url = default_uplink[0].get_authorize_url()
    redirect = await default_uplink[0].session.post(url, allow_redirects=False)
    assert redirect.status == 302
    assert redirect.headers["Location"].startswith(default_uplink[1].redirect)


@pytest.mark.asyncio
async def test_notifications(default_uplink):
    await default_uplink[0].get_access_token("goodcode")

    default_uplink[1].add_system(DEFAULT_SYSTEMID)
    default_uplink[1].add_notification(
        DEFAULT_SYSTEMID,
        {
            "notificationId": 1,
            "systemUnitId": 3,
            "moduleName": "sample string 4",
            "occuredAt": "2017-12-26T10:38:06Z",
            "stoppedAt": "2017-12-26T10:38:06Z",
            "wasReset": True,
            "resetPossible": True,
            "aidmodePossible": True,
            "info": {
                "alarmNumber": 1,
                "type": "ALARM",
                "title": "sample string 2",
                "description": "sample string 3",
            },
            "comments": [
                {
                    "authorName": "sample string 1",
                    "authorAvatar": {
                        "name": None,
                        "sizes": [
                            {
                                "width": 35,
                                "height": 35,
                                "url": "https://secure.gravatar.com/avatar/8f1b5a0edd19674db68799f1e7aed3e4?s=35&d=mm",
                            },
                            {
                                "width": 50,
                                "height": 50,
                                "url": "https://secure.gravatar.com/avatar/8f1b5a0edd19674db68799f1e7aed3e4?s=50&d=mm",
                            },
                        ],
                    },
                    "creationDate": "2017-12-26T10:38:06Z",
                    "text": "sample string 3",
                },
                {
                    "authorName": "sample string 1",
                    "authorAvatar": {
                        "name": None,
                        "sizes": [
                            {
                                "width": 35,
                                "height": 35,
                                "url": "https://secure.gravatar.com/avatar/8f1b5a0edd19674db68799f1e7aed3e4?s=35&d=mm",
                            },
                            {
                                "width": 50,
                                "height": 50,
                                "url": "https://secure.gravatar.com/avatar/8f1b5a0edd19674db68799f1e7aed3e4?s=50&d=mm",
                            },
                        ],
                    },
                    "creationDate": "2017-12-26T10:38:06Z",
                    "text": "sample string 3",
                },
            ],
        },
    )
    notifications = await default_uplink[0].get_notifications(DEFAULT_SYSTEMID)
    assert notifications[0]["systemUnitId"] == 3


@pytest.mark.asyncio
async def test_token_refresh(uplink_with_data):
    uplink = uplink_with_data[0]
    server = uplink_with_data[1]
    parameter = await uplink.get_parameter(DEFAULT_SYSTEMID, 100)
    assert parameter["displayValue"] == "100 Unit"

    on_oauth_token = server.requests["on_oauth_token"]
    server.expire_tokens()

    parameter = await uplink.get_parameter(DEFAULT_SYSTEMID, 100)
    assert parameter["displayValue"] == "100 Unit"
    assert server.requests["on_oauth_token"] == on_oauth_token + 1


@pytest.mark.asyncio
async def test_get_parameter(uplink_with_data):
    uplink = uplink_with_data[0]

    parameter = await uplink.get_parameter(DEFAULT_SYSTEMID, 100)

    assert parameter["displayValue"] == "100 Unit"

    parameter = await uplink.get_parameter(DEFAULT_SYSTEMID, 120)

    assert parameter["displayValue"] == "120 Units"

    parameter = await uplink.get_parameter(DEFAULT_SYSTEMID, "onehundredtwenty")

    assert parameter["displayValue"] == "120 Units"


@pytest.mark.asyncio
async def test_put_parameter(uplink_with_data):
    uplink = uplink_with_data[0]

    status = await uplink.put_parameter(DEFAULT_SYSTEMID, 100, "hello")

    assert status == "DONE"


@pytest.mark.asyncio
async def test_parameters_unit(uplink_with_data):
    uplink = uplink_with_data[0]

    parameter = await uplink.get_parameter(DEFAULT_SYSTEMID, 100)

    assert parameter["displayValue"] == "100 Unit"
    assert parameter["unit"] == "Unit"
    assert parameter["value"] == 100.0


@pytest.mark.asyncio
@pytest.mark.parametrize("count", [1, 15, 16])
async def test_parameters(default_uplink, count):
    uplink = default_uplink[0]
    server = default_uplink[1]

    await uplink.get_access_token("goodcode")

    server.add_system(DEFAULT_SYSTEMID)
    parameterids = range(100, 100 + count)

    data = [
        {
            "parameterId": index,
            "displayValue": "{}".format(index),
            "name": str(index),
            "title": "Paramter Title",
            "unit": "Unit",
            "designation": "Designation",
            "rawValue": index,
        }
        for index in parameterids
    ]

    for d in data:
        server.add_parameter(DEFAULT_SYSTEMID, d)

    requests = [
        uplink.get_parameter(DEFAULT_SYSTEMID, parameterid)
        for parameterid in parameterids
    ]

    parameters = await asyncio.gather(*requests)

    # Check that we get values back
    for index in range(1, len(parameterids)):
        assert parameters[index]["displayValue"] == data[index]["displayValue"]

    # Check that we don't issue more requests than we need
    assert server.requests["on_get_parameters"] == int((len(parameterids) + 14) / 15)


@pytest.mark.asyncio
async def test_throttle_initial():
    """No inital delay"""
    start = datetime.now()
    throttle = nibeuplink.uplink.Throttle(timedelta(seconds=1))
    async with throttle:
        pass
    assert (datetime.now() - start) < timedelta(seconds=1)


@pytest.mark.asyncio
async def test_throttle_time_from_finish():
    """Time counted from end of with block (assumes no inital)"""
    start = datetime.now()
    throttle = nibeuplink.uplink.Throttle(timedelta(seconds=1))
    async with throttle:
        await asyncio.sleep(1)
    async with throttle:
        pass
    now = datetime.now()
    assert (now - start) > timedelta(seconds=2)
    assert (now - start) < timedelta(seconds=3)
