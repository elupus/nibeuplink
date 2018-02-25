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

