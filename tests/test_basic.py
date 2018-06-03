import logging
import pytest
import nibeuplink
import asyncio
import socket
import aiohttp
from   aiohttp import web
import fake_uplink

logging.basicConfig(level=logging.DEBUG)


DEFAULT_CLIENT_ID     = '12345'
DEFAULT_CLIENT_SECRET = '4567'
DEFAULT_SCOPE         = ['A', 'B', 'C']
DEFAULT_CODE          = '789'

@pytest.mark.asyncio
@pytest.fixture
async def default_uplink(event_loop):
    def access_write(data):
        pass

    server = fake_uplink.Uplink(event_loop)

    await server.start()

    async with nibeuplink.Uplink(DEFAULT_CLIENT_ID,
                           DEFAULT_CLIENT_SECRET,
                           server.redirect,
                           None,
                           access_write,
                           scope = DEFAULT_SCOPE,
                           base  = server.base) as uplink:
        yield uplink, server

    await server.stop()

@pytest.mark.asyncio
async def test_status(default_uplink):
    assert not default_uplink[0].access_data

@pytest.mark.asyncio
async def test_get_authorize_url(default_uplink):
    from urllib.parse import (urlsplit, parse_qs)

    o = urlsplit(default_uplink[0].get_authorize_url())
    q = parse_qs(o.query)

    assert q['response_type'] == ['code']
    assert q['client_id']     == [DEFAULT_CLIENT_ID]
    assert q['redirect_uri']  == [default_uplink[1].redirect]
    assert q['scope']         == [' '.join(DEFAULT_SCOPE)]

@pytest.mark.asyncio
async def test_get_code_from_url(default_uplink):
    from urllib.parse import (urlsplit, parse_qs)
    o = urlsplit(default_uplink[0].get_authorize_url())
    q = parse_qs(o.query)


    # valid state
    url = "{}?state={}&code={}".format(default_uplink[1].redirect, q['state'][0], DEFAULT_CODE)
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
    token = await default_uplink[0].get_access_token('code_sample')


@pytest.mark.asyncio
async def test_auth_flow(default_uplink):
    url = default_uplink[0].get_authorize_url()
    redirect = await default_uplink[0].session.post(url, allow_redirects = False)
    assert redirect.status == 302
    assert redirect.headers['Location'].startswith(default_uplink[1].redirect)

@pytest.mark.asyncio
async def test_notifications(default_uplink):
    default_uplink[1].add_system(123456)
    default_uplink[1].add_notification(123456, {
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
              "description": "sample string 3"
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
                      "url": "https://secure.gravatar.com/avatar/8f1b5a0edd19674db68799f1e7aed3e4?s=35&d=mm"
                    },
                    {
                      "width": 50,
                      "height": 50,
                      "url": "https://secure.gravatar.com/avatar/8f1b5a0edd19674db68799f1e7aed3e4?s=50&d=mm"
                    }
                  ]
                },
                "creationDate": "2017-12-26T10:38:06Z",
                "text": "sample string 3"
              },
              {
                "authorName": "sample string 1",
                "authorAvatar": {
                  "name": None,
                  "sizes": [
                    {
                      "width": 35,
                      "height": 35,
                      "url": "https://secure.gravatar.com/avatar/8f1b5a0edd19674db68799f1e7aed3e4?s=35&d=mm"
                    },
                    {
                      "width": 50,
                      "height": 50,
                      "url": "https://secure.gravatar.com/avatar/8f1b5a0edd19674db68799f1e7aed3e4?s=50&d=mm"
                    }
                  ]
                },
                "creationDate": "2017-12-26T10:38:06Z",
                "text": "sample string 3"
              }
            ]
        }
    )
    notifications = await default_uplink[0].get_notifications(123456)
    assert notifications[0]['systemUnitId'] == 3

@pytest.mark.asyncio
async def test_single_parameter(default_uplink):
    systemid = 123456
    default_uplink[1].add_system(systemid)

    default_uplink[1].add_parameter(systemid, {
            'parameterId' : 100,
            'displayValue': str(100),
            'name' : 'Parameter Name',
            'title': 'Paramter Title',
            'unit': 'Unit',
            'designation': 'Designation',
            'rawValue': 100
        })


    parameter = await default_uplink[0].get_parameter(systemid, 100)

    assert parameter['displayValue'] == '100'

@pytest.mark.asyncio
async def test_parameters_unit(default_uplink):
    systemid = 123456
    default_uplink[1].add_system(systemid)

    default_uplink[1].add_parameter(systemid, {
            'parameterId' : 100,
            'displayValue': '{} Unit'.format(100),
            'name' : 'Parameter Name',
            'title': 'Paramter Title',
            'unit': 'Unit',
            'designation': 'Designation',
            'rawValue': 100
        })


    parameter = await default_uplink[0].get_parameter(systemid, 100)

    assert parameter['displayValue'] == '100 Unit'
    assert parameter['unit'] == 'Unit'
    assert parameter['value'] == 100.0

@pytest.mark.asyncio
@pytest.mark.parametrize('count', [1, 15, 16])
async def test_parameters(default_uplink, count):
    systemid = 123456
    default_uplink[1].add_system(systemid)
    parameterids  = range(100,100+count)

    data = [
        {
            'parameterId' : index,
            'displayValue': '{}'.format(index),
            'name' : 'Parameter Name',
            'title': 'Paramter Title',
            'unit': 'Unit',
            'designation': 'Designation',
            'rawValue': index
        }
        for index in parameterids
    ]

    for d in data:
        default_uplink[1].add_parameter(systemid, d)


    requests = [
        default_uplink[0].get_parameter(systemid, parameterid)
        for parameterid in parameterids
    ]

    parameters = await asyncio.gather(*requests)

    # Check that we get values back
    for index in range(1, len(parameterids)):
        assert parameters[index]['displayValue'] == data[index]['displayValue']

    # Check that we don't issue more requests than we need
    assert default_uplink[1].requests['on_parameters'] == int((len(parameterids) + 14) / 15)
