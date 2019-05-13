"""Handler for uplink."""
import attr
import cattr
import logging
import asyncio
import aiohttp
import uuid
from datetime import datetime, timedelta
from typing import List, Optional, Any

from urllib.parse import urlencode, urlsplit, parse_qs

from .exceptions import UplinkResponseException, UplinkException
from .utils import chunks, chunk_pop
from .typing import (
    StatusItemIcon,
    ParameterId,
)
from .types import (
    Thermostat,
    SetThermostatModel,
)
from .const import (
    MAX_REQUEST_PARAMETERS
)

_LOGGER = logging.getLogger(__name__)


async def raise_for_status(response):
    if 400 <= response.status:
        e = aiohttp.ClientResponseError(
            response.request_info,
            response.history,
            code=response.status,
            headers=response.headers)

        if 'json' in response.headers.get('CONTENT-TYPE', ''):
            data = await response.json()
            e.message = str(data)
            raise UplinkResponseException(
                data.get('errorCode'),
                data) from e

        else:
            data = await response.text()
            raise UplinkException(data) from e

class BearerAuth(aiohttp.BasicAuth):
    def __init__(self, access_token):
        self.access_token = access_token

    def encode(self):
        return "Bearer {}".format(self.access_token)


class ParameterRequest:
    def __init__(self, parameter_id: str):
        self.parameter_id = parameter_id
        self.data         = None
        self.done         = False

class Throttle():
    """
    Throttling requests to API.

    Works by awaiting our turn then executing the request,
    and scheduling next request at a delay after the previous
    request completed.
    """
    def __init__(self, delay):
        self._delay = delay
        self._timestamp = datetime.now()

    async def __aenter__(self):
        timestamp = datetime.now()
        delay = (self._timestamp - timestamp).total_seconds()
        if delay > 0:
            _LOGGER.debug("Delaying request by %s seconds due to throttle", delay)
            await asyncio.sleep(delay)
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        self._timestamp = datetime.now() + self._delay


class Uplink():


    def __init__(self,
                 client_id,
                 client_secret,
                 redirect_uri,
                 access_data = None,
                 access_data_write = None,
                 scope = ['READSYSTEM'],
                 loop = None,
                 base = 'https://api.nibeuplink.com',
                 throttle = 4.5):

        self.redirect_uri      = redirect_uri
        self.client_id         = client_id
        self.access_data_write = access_data_write
        self.state             = None
        self.scope             = scope
        self.lock              = asyncio.Lock()
        self.throttle          = Throttle(timedelta(seconds=throttle))
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

        headers = {
            'Accept'      : 'application/json',
            'Content-Type': 'application/x-www-form-urlencoded;charset=UTF-8'
        }

        self.session           = aiohttp.ClientSession(headers   = headers,
                                                       auth      = aiohttp.BasicAuth(client_id, client_secret))
        self.requests          = {}

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

        if 'expires_in' in data:
            _LOGGER.debug("Token will expire in %s seconds",
                          data['expires_in'])
            expires = datetime.now() + timedelta(seconds=data['expires_in'])
        else:
            expires = None

        data['access_token_expires'] = expires.isoformat()

        self.access_data = data
        if self.access_data_write:
            self.access_data_write(data)

    async def _get_auth(self):
        if self.access_data:
            return BearerAuth(self.access_data['access_token'])
        else:
            return None

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
        if not self.access_data or 'refresh_token' not in self.access_data:
            _LOGGER.warning("No refresh token available for refresh")
            return

        _LOGGER.debug('Refreshing access token with refresh token %s',
                      self.access_data['refresh_token'])
        payload = {
            'grant_type'    : 'refresh_token',
            'refresh_token' : self.access_data['refresh_token'],
        }

        async with self.session.post('{}/oauth/token'.format(self.base),
                                     data=payload) as response:
            await raise_for_status(response)
            self._handle_access_token(await response.json())

    def get_authorize_url(self, state=None):
        if not state:
            state = uuid.uuid4().hex
        self.state = state

        params = {
            'response_type' : 'code',
            'client_id'     : self.client_id,
            'redirect_uri'  : self.redirect_uri,
            'scope'         : ' '.join(self.scope),
            'state'         : state,
        }

        return '{}/oauth/authorize?{}'.format(self.base, urlencode(params))

    def get_code_from_url(self, url):
        query = parse_qs(urlsplit(url).query)
        if 'state' in query and query['state'][0] != self.state:
            raise ValueError('Invalid state in url {} expected {}'.format(query['state'], self.state))
        return query['code'][0]

    async def get(self, url, params = {}):
        async with self.lock:
            async with self.throttle:
                return await self._request(
                    self.session.get,
                    '{}/api/v1/{}'.format(self.base, url),
                    params = params,
                    headers= {},
                )

    async def put(self, url, **kwargs):
        async with self.lock:
            async with self.throttle:
                return await self._request(
                    self.session.put,
                    '{}/api/v1/{}'.format(self.base, url),
                    **kwargs
                )

    async def post(self, url, **kwargs):
        async with self.lock:
            async with self.throttle:
                return await self._request(
                    self.session.post,
                    '{}/api/v1/{}'.format(self.base, url),
                    **kwargs
                )

    async def _request(self, fun, *args, **kw):
        response = await fun(*args,
                             auth=await self._get_auth(),
                             **kw)
        try:
            if response.status == 401:
                _LOGGER.debug(response)
                _LOGGER.info("Attempting to refresh token due to error in request")
                await self.refresh_access_token()
                response.close()
                response = await fun(*args,
                                     auth=await self._get_auth(),
                                     **kw)

            await raise_for_status(response)

            if 'json' in response.headers.get('CONTENT-TYPE', ''):
                data = await response.json()
            else:
                data = await response.text()

            return data

        finally:
            response.close()

    async def get_parameter_raw(self, system_id: int, parameter_id: ParameterId):

        request = ParameterRequest(str(parameter_id))
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

                async with self.throttle:
                    # chop of as many requests from start as possible
                    requests = chunk_pop(self.requests[system_id],
                                        MAX_REQUEST_PARAMETERS)

                    _LOGGER.debug("Requesting parameters {}".format([str(x.parameter_id) for x in requests]))

                    data = await self._request(
                        self.session.get,
                        '{}/api/v1/systems/{}/parameters'.format(self.base, system_id),
                        params  = [('parameterIds', str(x.parameter_id)) for x in requests],
                        headers = {},
                    )

                lookup = {p['name']: p for p in data}

                for r in requests:
                    r.done = True
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

    async def get_parameter(self, system_id: int, parameter_id: ParameterId):
        data = await self.get_parameter_raw(system_id, parameter_id)
        self.add_parameter_extensions(data)
        return data

    async def put_parameter(self, system_id: int, parameter_id: ParameterId, value: Any):
        headers = {
            'Accept'      : 'application/json',
            'Content-Type': 'application/json;charset=UTF-8'
        }

        data = {
            'settings': {
                str(parameter_id): value
            }
        }

        result = await self._request(
            self.session.put,
            '{}/api/v1/systems/{}/parameters'.format(self.base, system_id),
            json    = data,
            headers = headers,
        )
        return result[0]['status']

    async def get_system(self, system_id: int):
        _LOGGER.debug("Requesting system {}".format(system_id))
        return await self.get('systems/{}'.format(system_id))

    async def get_systems(self):
        _LOGGER.debug("Requesting systems")
        data = await self.get('systems')
        return data['objects']

    async def get_category_raw(self,
                               system_id: int,
                               category_id: str,
                               unit_id: int = 0):
        _LOGGER.debug("Requesting category {} on system {}".format(category_id, system_id))
        return await self.get('systems/{}/serviceinfo/categories/{}'.format(system_id, category_id),
                              {'systemUnitId': unit_id})

    async def get_category(self,
                           system_id: int,
                           category_id: str,
                           unit_id: int = 0):
        data = await self.get_category_raw(system_id, category_id, unit_id)
        for param in data:
            self.add_parameter_extensions(param)
        return data

    async def get_categories(self,
                             system_id: int,
                             parameters: bool,
                             unit_id: int = 0):
        _LOGGER.debug("Requesting categories on system {}".format(system_id))

        data = await self.get('systems/{}/serviceinfo/categories'.format(system_id),
                              {'parameters'  : str(parameters),
                               'systemUnitId': unit_id})
        for category in data:
            if category['parameters']:
                for param in category['parameters']:
                    self.add_parameter_extensions(param)
        return data

    async def get_status_raw(self, system_id: int):
        _LOGGER.debug("Requesting status on system {}".format(system_id))
        return await self.get('systems/{}/status/system'.format(system_id))

    async def get_status(self, system_id: int) -> List[StatusItemIcon]:
        data = await self.get_status_raw(system_id)
        for status in data:
            if status['parameters']:
                for param in status['parameters']:
                    self.add_parameter_extensions(param)
        return data

    async def get_units(self, system_id: int):
        _LOGGER.debug("Requesting units on system {}".format(system_id))
        return await self.get('systems/{}/units'.format(system_id))

    async def get_unit_status(self, system_id: int, unit_id: int):
        _LOGGER.debug("Requesting unit {} on system {}".format(unit_id, system_id))
        data = await self.get('systems/{}/status/systemUnit/{}'.format(system_id, unit_id))
        for status in data:
            if status['parameters']:
                for param in status['parameters']:
                    self.add_parameter_extensions(param)
        return data

    async def get_notifications(self,
                                system_id: int,
                                active: bool = True,
                                notifiction_type: str = 'ALARM'):
        _LOGGER.debug("Requesting notifications on system {}".format(system_id))
        params = {
            'active'      : str(active),
            'itemsPerPage': 100,
            'type'        : notifiction_type,
        }
        data = await self.get('systems/{}/notifications'.format(system_id), params=params)
        return data['objects']


    async def get_smarthome_mode(self,
                                 system_id: int) -> str:
        data = await self.get('systems/{}/smarthome/mode'.format(system_id))
        mode = data['mode']
        _LOGGER.debug("Get smarthome mode %s", mode)
        return mode


    async def put_smarthome_mode(self,
                                 system_id: int,
                                 mode: str) -> None:
        headers = {
            'Accept'      : 'application/json',
            'Content-Type': 'application/json;charset=UTF-8'
        }

        data = {
            'mode': mode
        }
        data = await self.put(
            'systems/{}/smarthome/mode'.format(system_id),
            json=data,
            headers=headers)
        _LOGGER.debug("Set smarthome mode %s -> %s", mode, data)


    async def get_smarthome_thermostats(self,
                                        system_id: int) -> List[Thermostat]:
        data = await self.get('systems/{}/smarthome/thermostats'.format(system_id))
        _LOGGER.debug("Get smarthome thermostats %s", data)
        return cattr.structure(data, List[Thermostat])


    async def post_smarthome_thermostats(self,
                                         system_id: int,
                                         thermostat: SetThermostatModel) -> None:
        headers = {
            'Accept'      : 'application/json',
            'Content-Type': 'application/json;charset=UTF-8'
        }

        data = attr.asdict(thermostat)
        _LOGGER.debug("Post smarthome thermostat %s -> %s", thermostat , data)
        await self.post(
            'systems/{}/smarthome/thermostats'.format(system_id),
            json=data,
            headers=headers)
