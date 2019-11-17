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

@pytest.fixture(name="server")
async def default_server(loop):
    server = fake_uplink.Uplink(loop)

    await server.start()
    yield server
    await server.stop()


@pytest.fixture(name="session")
async def default_session(loop, request, server):
    def access_write(data):
        pass

    session = nibeuplink.UplinkSession(
        DEFAULT_CLIENT_ID,
        DEFAULT_CLIENT_SECRET,
        server.redirect,
        None,
        access_write,
        scope=DEFAULT_SCOPE,
        base=server.base,
    )
    yield session
    await session.close()


@pytest.fixture(name="uplink")
async def default_uplink(loop, request, session, server):

    uplink = nibeuplink.Uplink(
        session=session,
        base=server.base,
        throttle=0,
    )

    yield uplink


@pytest.fixture
async def uplink_with_data(loop, uplink, server, session):

    server.add_system(DEFAULT_SYSTEMID)

    server.add_parameter(
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

    server.add_parameter(
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

    server.add_parameter(
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
    await session.get_access_token(DEFAULT_CODE)

    return uplink


async def test_status(session):
    assert not session.access_data


async def test_get_authorize_url(session, server):
    from urllib.parse import urlsplit, parse_qs

    o = urlsplit(session.get_authorize_url())
    q = parse_qs(o.query)

    assert q["response_type"] == ["code"]
    assert q["client_id"] == [DEFAULT_CLIENT_ID]
    assert q["redirect_uri"] == [server.redirect]
    assert q["scope"] == [" ".join(DEFAULT_SCOPE)]


async def test_get_code_from_url(session, server):
    from urllib.parse import urlsplit, parse_qs

    o = urlsplit(session.get_authorize_url())
    q = parse_qs(o.query)

    # valid state
    url = "{}?state={}&code={}".format(
        server.redirect, q["state"][0], DEFAULT_CODE
    )
    assert DEFAULT_CODE == session.get_code_from_url(url)

    # no state
    url = "{}?code={}".format(server.redirect, DEFAULT_CODE)
    assert DEFAULT_CODE == session.get_code_from_url(url)

    # invalid state
    url = "{}?state={}&code={}".format(server.redirect, "junk", DEFAULT_CODE)
    with pytest.raises(ValueError):
        session.get_code_from_url(url)


async def test_get_get_access_token(session):
    await session.get_access_token("code_sample")


async def test_auth_flow(session, server):
    url = session.get_authorize_url()
    redirect = await session.session.post(url, allow_redirects=False)
    assert redirect.status == 302
    assert redirect.headers["Location"].startswith(server.redirect)


async def test_notifications(server, session, uplink):
    await session.get_access_token("goodcode")

    server.add_system(DEFAULT_SYSTEMID)
    server.add_notification(
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
    notifications = await uplink.get_notifications(DEFAULT_SYSTEMID)
    assert notifications[0]["systemUnitId"] == 3


async def test_token_refresh(server, uplink_with_data):
    parameter = await uplink_with_data.get_parameter(DEFAULT_SYSTEMID, 100)
    assert parameter["displayValue"] == "100 Unit"

    on_oauth_token = server.requests["on_oauth_token"]
    server.expire_tokens()

    parameter = await uplink_with_data.get_parameter(DEFAULT_SYSTEMID, 100)
    assert parameter["displayValue"] == "100 Unit"
    assert server.requests["on_oauth_token"] == on_oauth_token + 1


async def test_get_parameter(uplink_with_data):

    parameter = await uplink_with_data.get_parameter(DEFAULT_SYSTEMID, 100)

    assert parameter["displayValue"] == "100 Unit"

    parameter = await uplink_with_data.get_parameter(DEFAULT_SYSTEMID, 120)

    assert parameter["displayValue"] == "120 Units"

    parameter = await uplink_with_data.get_parameter(DEFAULT_SYSTEMID, "onehundredtwenty")

    assert parameter["displayValue"] == "120 Units"


async def test_put_parameter(uplink_with_data):
    status = await uplink_with_data.put_parameter(DEFAULT_SYSTEMID, 100, "hello")

    assert status == "DONE"


async def test_parameters_unit(uplink_with_data):

    parameter = await uplink_with_data.get_parameter(DEFAULT_SYSTEMID, 100)

    assert parameter["displayValue"] == "100 Unit"
    assert parameter["unit"] == "Unit"
    assert parameter["value"] == 100.0


@pytest.mark.parametrize("count", [1, 15, 16])
async def test_parameters(session, uplink, server, count):

    await session.get_access_token("goodcode")

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


async def test_throttle_initial():
    """No inital delay"""
    start = datetime.now()
    throttle = nibeuplink.uplink.Throttle(timedelta(seconds=1))
    async with throttle:
        pass
    assert (datetime.now() - start) < timedelta(seconds=1)


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
