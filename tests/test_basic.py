import pytest
import nibeuplink
import asyncio


DEFAULT_CLIENT_ID     = '12345'
DEFAULT_CLIENT_SECRET = '4567'
DEFAULT_REDIRECT_URI  = 'uri:some%20long%20uri'
DEFAULT_SCOPE         = ['A', 'B', 'C']
DEFAULT_CODE          = '789'

@pytest.fixture
async def default_uplink():
    def access_write(self, data):
        pass

    async with nibeuplink.Uplink(DEFAULT_CLIENT_ID,
                           DEFAULT_CLIENT_SECRET,
                           DEFAULT_REDIRECT_URI,
                           None,
                           access_write,
                           scope = DEFAULT_SCOPE) as uplink:
        yield uplink

@pytest.mark.asyncio
async def test_status(default_uplink):
    assert not default_uplink.access_data

@pytest.mark.asyncio
async def test_get_authorize_url(default_uplink):
    from urllib.parse import (urlsplit, parse_qs)

    o = urlsplit(default_uplink.get_authorize_url())
    q = parse_qs(o.query)

    assert q['response_type'] == ['code']
    assert q['client_id']     == [DEFAULT_CLIENT_ID]
    assert q['redirect_uri']  == [DEFAULT_REDIRECT_URI]
    assert q['scope']         == [' '.join(DEFAULT_SCOPE)]

@pytest.mark.asyncio
async def test_get_code_from_url(default_uplink):
    from urllib.parse import (urlsplit, parse_qs)
    o = urlsplit(default_uplink.get_authorize_url())
    q = parse_qs(o.query)


    # valid state
    url = "{}?state={}&code={}".format(DEFAULT_REDIRECT_URI, q['state'][0], DEFAULT_CODE)
    assert DEFAULT_CODE == default_uplink.get_code_from_url(url)

    # no state
    url = "{}?code={}".format(DEFAULT_REDIRECT_URI, DEFAULT_CODE)
    assert DEFAULT_CODE == default_uplink.get_code_from_url(url)

    # invalid state
    url = "{}?state={}&code={}".format(DEFAULT_REDIRECT_URI, "junk", DEFAULT_CODE)
    with pytest.raises(ValueError):
        default_uplink.get_code_from_url(url)

