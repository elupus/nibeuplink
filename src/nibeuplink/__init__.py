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


async def raise_for_status(response):
    if 400 <= response.status:
        raise aiohttp.ClientResponseError(
            response.request_info,
            response.history,
            code=response.status,
            message=await response.text(),
            headers=response.headers)

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

    THROTTLE = timedelta(seconds = 4)

    def __init__(self,
                 client_id,
                 client_secret,
                 redirect_uri,
                 access_data,
                 access_data_write,
                 scope     = ['READSYSTEM'],
                 loop      = None,
                 base      = 'https://api.nibeuplink.com'):

        self.redirect_uri      = redirect_uri
        self.client_id         = client_id
        self.access_data_write = access_data_write
        self.state             = None
        self.scope             = scope
        self.lock              = asyncio.Lock()
        self.session           = None
        self.loop              = loop
        self.base              = base
        self.access_data       = None

        # check that the access scope is enough, otherwise ignore
        if access_data:
            if set(scope).issubset(set(access_data['scope'].split(' '))):
                self.access_data = access_data
            else:
                _LOGGER.info("Ignoring access data due to changed scope {}".format(scope))

        if self.access_data:
            self.auth = BearerAuth(self.access_data['access_token'])
        else:
            self.auth = None

        headers = {
                'Accept'      : 'application/json',
                'Content-Type': 'application/x-www-form-urlencoded;charset=UTF-8'
        }

        self.session           = aiohttp.ClientSession(headers   = headers,
                                                       auth      = aiohttp.BasicAuth(client_id, client_secret))
        self.requests          = {}
        self.timestamp         = datetime.now()

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.close()

    async def close(self):
        if self.session:
            await self.session.close()
            self.session = None

    def _handle_access_token(self, data):
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

        async with self.session.post('{}/oauth/token'.format(self.base),
                                     data=payload) as response:
            await raise_for_status(response)
            self._handle_access_token(await response.json())


    async def refresh_access_token(self):
        payload = {
            'grant_type'    : 'refresh_token',
            'refresh_token' : self.access_data['refresh_token'],
        }

        async with self.session.post('{}/oauth/token'.format(self.base),
                                     data=payload) as response:
            await raise_for_status(response)
            self._handle_access_token(await response.json())

    def get_authorize_url(self):
        self.state = uuid.uuid4().hex

        params = {
            'response_type' : 'code',
            'client_id'     : self.client_id,
            'redirect_uri'  : self.redirect_uri,
            'scope'         : ' '.join(self.scope),
            'state'         : self.state,
        }

        return '{}/oauth/authorize?{}'.format(self.base, urlencode(params))

    def get_code_from_url(self, url):
        query = parse_qs(urlsplit(url).query)
        if 'state' in query and query['state'][0] != self.state:
            raise ValueError('Invalid state in url {} expected {}'.format(query['state'], self.state))
        return query['code'][0]


    # Throttle requests to API to once every MIN_REQUEST_DELAY
    async def _get_throttle(self):
        timestamp = datetime.now()

        delay = (self.timestamp - timestamp).total_seconds()
        if delay > 0:
            await asyncio.sleep(delay)
        self.timestamp = timestamp + self.THROTTLE

    async def get(self, url, params = {}):
        async with self.lock:
            await self._get_throttle()

            return await self._request(
                self.session.get,
                '{}/api/v1/{}'.format(self.base, url),
                params = params,
                headers= {},
            )

    async def _request(self, fun, *args, **kw):

        response = await fun(*args, auth = self.auth, **kw)
        try:
            if response.status == 401:
                _LOGGER.debug(response)
                _LOGGER.info("Attempting to refresh token due to error in request")
                await self.refresh_access_token()
                response.close()
                response = await fun(*args, auth = self.auth, **kw)

            if 'json' in response.headers.get('CONTENT-TYPE'):
                data = await response.json()
            else:
                data = await response.text()

            if response.status >= 400:
                _LOGGER.debug(data)

            await raise_for_status(response)

            return data

        finally:
            response.close()

    async def get_parameter_raw(self, system_id, parameter_id):

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
                await self._get_throttle()


                # chop of as many requests from start as possible
                requests = chunk_pop(self.requests[system_id], MAX_REQUEST_PARAMETERS)

                for r in requests:
                    r.done = True

                _LOGGER.debug("Requesting parameters {}".format([str(x.parameter_id) for x in requests]))

                data = await self._request(
                    self.session.get,
                    '{}/api/v1/systems/{}/parameters'.format(self.base, system_id),
                    params  = [('parameterIds', str(x.parameter_id)) for x in requests],
                    headers = {},
                )


                lookup = { p['parameterId']: p for p in data }

                for r in requests:
                    if r.parameter_id in lookup:
                        r.data = lookup[r.parameter_id]

        return request.data

    def add_parameter_extensions(self, data):
        if data:
            if data['displayValue'].endswith(data['unit']) and len(data['unit']):
                value = data['displayValue'][:-len(data['unit'])]

                try:
                    value = float(value)
                except ValueError:
                    pass

                data['value'] = value
            elif data['displayValue'] == '--':
                data['value'] = None
            else:
                data['value'] = data['displayValue']



    async def get_parameter(self, system_id, parameter_id):
        data = await self.get_parameter_raw(system_id, parameter_id)
        self.add_parameter_extensions(data)
        return data

    async def set_parameter(self, system_id, parameter_id, value):
        headers = {
            'Accept'      : 'application/json',
            'Content-Type': 'application/json;charset=UTF-8'
        }

        data = {
            'settings': {
                str(parameter_id): str(value)
            }
        }

        return await self._request(
            self.session.put,
            '{}/api/v1/systems/{}/parameters'.format(BASE_URL, system_id),
            json    = data,
            headers = headers,
        )

    async def get_system(self, system_id):
        _LOGGER.debug("Requesting system {}".format(system_id))
        return await self.get('systems/{}'.format(system_id))

    async def get_systems(self):
        _LOGGER.debug("Requesting systems")
        data = await self.get('systems')
        return data['objects']

    async def get_category_raw(self, system_id, category_id):
        _LOGGER.debug("Requesting category {} on system {}".format(category_id, system_id))
        return await self.get('systems/{}/serviceinfo/categories/{}'.format(system_id, category_id))

    async def get_category(self, system_id, category_id):
        data = await self.get_category_raw(system_id, category_id)
        for param in data:
            self.add_parameter_extensions(param)
        return data

    async def get_categories(self, system_id, parameters):
        _LOGGER.debug("Requesting categories on system {}".format(system_id))

        return await self.get('systems/{}/serviceinfo/categories'.format(system_id),
                                {'parameters' : str(parameters)})

    async def get_status_raw(self, system_id):
        _LOGGER.debug("Requesting status on system {}".format(system_id))
        return await self.get('systems/{}/status/system'.format(system_id))

    async def get_status(self, system_id):
        data = await self.get_status_raw(system_id)
        for status in data:
            for param in status['parameters']:
                self.add_parameter_extensions(param)
        return data

    async def get_units(self, system_id):
        _LOGGER.debug("Requesting units on system {}".format(system_id))
        return await self.get('systems/{}/units'.format(system_id))

    async def get_unit_status(self, system_id, unit_id):
        _LOGGER.debug("Requesting unit {} on system {}".format(unit_id, system_id))
        return await self.get('systems/{}/status/systemUnit/{}'.format(system_id, unit_id))

    async def get_notifications(self, system_id, active = True, notifiction_type = 'ALARM'):
        _LOGGER.debug("Requesting notifications on system {}".format(system_id))
        params = { 'active'      : str(active),
                   'itemsPerPage': 100,
                   'type'        : notifiction_type,
        }
        data = await self.get('systems/{}/notifications'.format(system_id), params = params)
        return data['objects']
