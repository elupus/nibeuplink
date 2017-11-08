import logging
import sys
import os
from itertools import islice
import asyncio
import aiohttp
import uuid
import multidict
from datetime import datetime, timedelta

from urllib.parse import urlencode, urljoin, urlsplit, parse_qs, parse_qsl


_LOGGER = logging.getLogger(__name__)

MAX_REQUEST_PARAMETERS   = 15
MIN_REQUEST_DELAY        = 4
BASE_URL            = 'https://api.nibeuplink.com'
TOKEN_URL           = '%s/oauth/token' % BASE_URL
AUTH_URL            = '%s/oauth/authorize' % BASE_URL

def chunks(data, SIZE):
    it = iter(data)
    for i in range(0, len(data), SIZE):
        yield {k:data[k] for k in islice(it, SIZE)}

def chunk_pop(data, SIZE):
    count = len(data)
    if count > SIZE:
        count = SIZE

    res = data[0:count]
    del data[0:count]
    return res


class BearerAuth(aiohttp.BasicAuth):
    def __init__(self, access_token):
        self.access_token = access_token

    def encode(self):
        return "Bearer {}".format(self.access_token)

class ParameterRequest:
    def __init__(self, parameter_id):
        self.parameter_id = parameter_id
        self.data         = None
        self.done         = False


class Uplink():

    def __init__(self, client_id, client_secret, redirect_uri, access_data, access_data_write, scope = ['READSYSTEM']):

        self.redirect_uri      = redirect_uri
        self.client_id         = client_id
        self.access_data       = access_data
        self.access_data_write = access_data_write
        self.state             = None
        self.scope             = scope
        self.lock              = asyncio.Lock()

        if self.access_data:
            self.auth = BearerAuth(self.access_data['access_token'])
        else:
            self.auth = None

        headers = {
                'Accept'      : 'application/json',
                'Content-Type': 'application/x-www-form-urlencoded;charset=UTF-8'
        }

        self.session           = aiohttp.ClientSession(headers = headers, auth = aiohttp.BasicAuth(client_id, client_secret))
        self.requests          = {}
        self.timestamp         = datetime.now()

    def __del__(self):
        self.close()

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        self.close()

    def close(self):
        self.session.close()

    def handle_access_token(self, data):
        if 'access_token' not in data:
            raise ValueError('Error in reply {}'.format(data))

        self.access_data = data
        if self.access_data_write:
            self.access_data_write(data)
        self.auth = BearerAuth(self.access_data['access_token'])

    async def get_access_token(self, code):
        payload = {
            'grant_type'   : 'authorization_code',
            'code'         : code,
            'redirect_uri' : self.redirect_uri,
        }

        async with self.session.post(TOKEN_URL, data=payload) as response:
            response.raise_for_status()
            self.handle_access_token(await response.json())


    async def refresh_access_token(self):
        payload = {
            'grant_type'    : 'refresh_token',
            'refresh_token' : self.access_data['refresh_token'],
        }

        async with self.session.post(TOKEN_URL, data=payload) as response:
            response.raise_for_status()
            self.handle_access_token(await response.json())

    def get_authorize_url(self):
        self.state = uuid.uuid4().hex

        params = {
            'response_type' : 'code',
            'client_id'     : self.client_id,
            'redirect_uri'  : self.redirect_uri,
            'scope'         : ' '.join(self.scope),
            'state'         : self.state,
        }

        return AUTH_URL + '?' + urlencode(params)

    def get_code_from_url(self, url):
        query = parse_qs(urlsplit(url).query)
        if 'state' in query and query['state'][0] != self.state and False:
            raise ValueError('Invalid state in url {} expected {}'.format(query['state'], self.state))
        return query['code'][0]


    # Throttle requests to API to once every MIN_REQUEST_DELAY
    async def throttle(self):
        timestamp = datetime.now()

        delay = (self.timestamp - timestamp).total_seconds()
        if delay > 0:
            await asyncio.sleep(delay)
        self.timestamp = timestamp + timedelta(seconds = MIN_REQUEST_DELAY)

    async def get(self, url, params = {}):
        async with self.lock:
            await self.throttle()
            return await self._get_internal(url, params)

    async def request(self, fun):

        response = await fun()
        try:
            if response.status == 401:
                _LOGGER.debug(response)
                _LOGGER.info("Attempting to refresh token due to error in request")
                await self.refresh_access_token()
                response.close()
                response = await fun()

            if 'json' in response.headers.get('CONTENT-TYPE'):
                data = await response.json()
            else:
                data = await response.text()

            if response.status >= 400:
                _LOGGER.debug(data)

            response.raise_for_status()

            return data

        finally:
            response.close()

    async def _get_internal(self, url, params = {}):
        headers = {}
        url = '%s/api/v1/%s' % (BASE_URL, url)

        return await self.request(lambda:
            self.session.get(url, params=params, headers=headers, auth = self.auth)
        )


    async def get_parameter(self, system_id, parameter_id):

        request = ParameterRequest(parameter_id)
        if system_id not in self.requests:
            self.requests[system_id] = []
        self.requests[system_id].append(request)

        # yield to any other runnable that want to add requests
        await asyncio.sleep(0)

        while True:
            async with self.lock:

                # check if we are already finished, by somebody elses request
                if request.done:
                    break

                if len(self.requests[system_id]) == 0:
                    break

                # Throttle requests to API, during this new requests can be added
                await self.throttle()


                # chop of as many requests from start as possible
                requests = chunk_pop(self.requests[system_id], MAX_REQUEST_PARAMETERS)

                for r in requests:
                    r.done = True

                _LOGGER.debug("Requesting parameters {}".format([str(x.parameter_id) for x in requests]))
                params = [('parameterIds', str(x.parameter_id)) for x in requests]
                data = await self._get_internal(
                            'systems/{}/parameters'.format(system_id),
                            params = params
                       )
                lookup = { p['parameterId']: p for p in data }

                for r in requests:
                    if r.parameter_id in lookup:
                        r.data = lookup[r.parameter_id]

        return request.data

    async def set_parameter(self, system_id, parameter_id, value):
        url  = '{}/api/v1/systems/{}/parameters'.format(BASE_URL, system_id)
        headers = {
            'Accept'      : 'application/json',
            'Content-Type': 'application/json;charset=UTF-8'
        }

        data = {
            'settings': {
                str(parameter_id): str(value)
            }
        }

        return await self.request(lambda:
            self.session.put(url, json=data, headers=headers, auth = self.auth)
        )


    async def get_system(self, system_id):
        _LOGGER.debug("Requesting system {}".format(system_id))
        data = await self.get('systems/{}'.format(system_id))
        return data


    async def get_systems(self):
        _LOGGER.debug("Requesting systems")
        data = await self.get('systems')
        return data['objects']

    async def get_category(self, system_id, category_id):
        _LOGGER.debug("Requesting category {} on system {}".format(category_id, system_id))
        data   = await self.get('systems/{}/serviceinfo/categories/{}'.format(system_id, category_id))
        return data

    async def get_categories(self, system_id, parameters):
        _LOGGER.debug("Requesting categories on system {}".format(system_id))

        data   = await self.get('systems/{}/serviceinfo/categories'.format(system_id),
                                {'parameters' : str(parameters)})
        return data

    async def get_status(self, system_id):
        _LOGGER.debug("Requesting status on system {}".format(system_id))
        return await self.get('systems/{}/status/system'.format(system_id))

    async def get_units(self, system_id):
        _LOGGER.debug("Requesting units on system {}".format(system_id))
        return await self.get('systems/{}/units'.format(system_id))

    async def get_unit_status(self, system_id, unit_id):
        _LOGGER.debug("Requesting unit {} on system {}".format(unit_id, system_id))
        return await self.get('systems/{}/status/systemUnit/{}'.format(system_id, unit_id))

    async def get_notifications(self, system_id):
        _LOGGER.debug("Requesting notifications on system {}".format(system_id))
        return await self.get('systems/{}/notifications'.format(system_id))