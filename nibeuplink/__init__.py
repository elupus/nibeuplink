import logging
import sys
import os
from itertools import islice
import asyncio
import aiohttp
import uuid

from urllib.parse import urlencode, urljoin, urlsplit, parse_qs, parse_qsl


_LOGGER = logging.getLogger(__name__)

MAX_REQUEST_PARAMETERS   = 15
MIN_REQUEST_DELAY        = 4
SCOPE               = 'READSYSTEM'
BASE_URL            = 'https://api.nibeuplink.com'
TOKEN_URL           = '%s/oauth/token' % BASE_URL
AUTH_URL            = '%s/oauth/authorize' % BASE_URL

def chunks(data, SIZE):
    it = iter(data)
    for i in range(0, len(data), SIZE):
        yield {k:data[k] for k in islice(it, SIZE)}

class BearerAuth(aiohttp.BasicAuth):
    def __init__(self, access_token):
        self.access_token = access_token

    def encode(self):
        return "Bearer {}".format(self.access_token)

class System():
    def __init__(self, uplink, system_id):
        self.uplink     = uplink
        self.system_id  = system_id
        self.parameters = {}
        self.categories = {}
        self.data       = None

class Parameter():
    def __init__(self, uplink, system_id, parameter_id):
        self.uplink       = uplink
        self.system_id    = system_id
        self.parameter_id = parameter_id
        self.data         = None

    def __repr__(self):
        return 'system_id: {} parameter_id: {} data: {}'.format(self.system_id, self.parameter_id, self.data)

class Category():
    def __init__(self, uplink, system_id, category_id):
        self.uplink        = uplink
        self.system_id     = system_id
        self.category_id   = category_id
        self.name          = ''
        self.parameter_ids = []

class Uplink():

    def __init__(self, client_id, client_secret, redirect_uri, access_data, access_data_write):

        self.redirect_uri      = redirect_uri
        self.client_id         = client_id
        self.access_data       = access_data
        self.access_data_write = access_data_write
        self.state             = None
        self.lock              = asyncio.Lock()

        if self.access_data:
            self.auth = BearerAuth(self.access_data['access_token'])
        else:
            self.auth = None

        headers = {
                'Accept'       : 'application/json',
        }

        self.session           = aiohttp.ClientSession(headers = headers, auth = aiohttp.BasicAuth(client_id, client_secret))
        self.systems           = {}
        self.sleep             = None

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
            'scope'         : SCOPE,
            'state'         : self.state,
        }

        return AUTH_URL + '?' + urlencode(params)

    def get_code_from_url(self, url):
        query = parse_qs(urlsplit(url).query)
        if 'state' in query and query['state'][0] != self.state and False:
            raise ValueError('Invalid state in url {} expected {}'.format(query['state'], self.state))
        return query['code'][0]

    async def get(self, uri, params = {}):
        async with self.lock:

            # Throttle requests to API
            if self.sleep:
                await self.sleep
            self.sleep = asyncio.sleep(MIN_REQUEST_DELAY)


            headers = {}
            url = '%s/api/v1/%s' % (BASE_URL, uri)
            async with self.session.get(url, params=params, headers=headers, auth = self.auth) as response:
                data = await response.json()
                _LOGGER.debug(response)

                if 400 <= response.status:
                    await self.refresh_access_token()
                    data = await self.get(uri, params)

                return data

    async def update(self):
        await self.update_systems()
        for system_id in self.systems.keys():
            await self.update_categories(system_id)
            await self.update_parameters(system_id)

    async def update_systems(self):
        _LOGGER.debug("Requesting systems")
        data = await self.get('systems')
        for s in data['objects']:
            system = self.get_system(s['systemId'])
            system.data = s

    async def update_categories(self, system_id):
        _LOGGER.debug("Requesting categories on system {}".format(system_id))

        system = self.get_system(system_id)
        data   = await self.get('systems/{}/serviceinfo/categories'.format(system_id),
                                {'parameters' : 'True'})

        for c in data:
            category = self.get_category(system_id, c['categoryId'])
            category.name = c['name']
            category.parameter_ids = [ p['parameterId'] for p in c['parameters'] ]
            for p in c['parameters']:
                parameter = self.get_parameter(system_id, p['parameterId'])
                parameter.data = p

    async def update_parameters(self, system_id):
        system = self.get_system(system_id)
        for parameters in chunks(system.parameters, MAX_REQUEST_PARAMETERS):
            _LOGGER.debug("Requesting parmeters {}".format(parameters))
            data = await self.get(
                        'systems/{}/parameters'.format(system.system_id),
                        { 'parameterIds' : ','.join([str(x) for x in parameters.keys()]) }
                   )

            for parameter in data:
                p = self.get_parameter(system.system_id, parameter['parameterId'])
                p.data = data

    def get_category(self, system_id, category_id):
        system   = self.get_system(system_id)
        category = None

        if category_id in system.categories:
            category = system.categories[category_id]
        else:
            category = Category(self, system_id, category_id)
            system.categories[category_id] = category

        return category

    def get_system(self, system_id):
        system = None
        if system_id in self.systems:
            system = self.systems[system_id]
        else:
            system = System(self, system_id)
            self.systems[system_id] = system
        return system

    def get_parameter(self, system_id, parameter_id):
        system    = self.get_system(system_id)
        parameter = None

        if parameter_id in system.parameters:
            parameter = system.parameters[parameter_id]
        else:
            parameter = Parameter(self, system_id, parameter_id)
            system.parameters[parameter_id] = parameter

        return parameter