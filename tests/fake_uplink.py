import logging
from functools import wraps
from urllib.parse import urlencode, urlsplit, urlunsplit
from collections import (defaultdict, namedtuple)

import aiohttp
from aiohttp import web
from aiohttp.web_exceptions import HTTPUnauthorized
from aiohttp.test_utils import unused_port

_LOGGER = logging.getLogger(__name__)


class JsonError(Exception):
    def __init__(self, status, error, description):
        self.status      = status
        self.error       = error
        self.description = description
        super.__init__("{}: {}".format(error, description))


def oauth_error_response(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except JsonError as e:
            data = {
                'error'            : e.error,
                'error_description': e.description
            }
            return web.json_response(data = data, status = e.status)
    return wrapper


System = namedtuple('System', ['parameters', 'notifications'])


class Uplink:
    def __init__(self, loop):
        self.loop    = loop
        self.app     = web.Application()
        self.app.router.add_routes([
            web.post('/oauth/token', self.on_oauth_token),
            web.post('/oauth/authorize', self.on_oauth_authorize),
            web.get('/api/v1/systems/{systemId}/notifications', self.on_notifications),
            web.get('/api/v1/systems/{systemId}/parameters', self.on_get_parameters),
            web.put('/api/v1/systems/{systemId}/parameters', self.on_put_parameters),
        ])
        self.handler  = None
        self.server   = None
        self.base     = None
        self.redirect = None
        self.systems  = {}
        self.requests = defaultdict(int)
        self.tokens   = {}
        self.counter  = 0

    def get_counted(self, prefix):
        self.counter = self.counter + 1
        return '{}_{}'.format(prefix, self.counter)

    def requests_update(self, fun):
        _LOGGER.debug(fun)
        self.requests[fun] = self.requests[fun] + 1

    async def start(self):
        print("Starting fake uplink")
        port = unused_port()
        host = '127.0.0.1'

        self.handler  = self.app.make_handler()
        self.server   = await self.loop.create_server(self.handler,
                                                      host,
                                                      port)
        self.base     = 'http://{}:{}'.format(host, port)
        self.redirect = '{}/redirect'.format(self.base)

    async def stop(self):
        _LOGGER.info("Stopping fake uplink")
        self.server.close()
        await self.server.wait_closed()
        await self.app.shutdown()
        await self.handler.shutdown()

    @oauth_error_response
    async def on_oauth_token(self, request):
        self.requests_update('on_oauth_token')
        data = await request.post()
        if data['grant_type'] == 'authorization_code':
            token = self.get_counted('dummyaccesstoken')
            self.tokens[token] = True
            data = {
                'access_token' : token,
                'expires_in'   : 300,
                'refresh_token': 'dummyrefreshtoken',
                'scopes'       : 'READSYSTEM',
                'token_type'   : 'bearer',
            }
            return web.json_response(data = data)

        elif data['grant_type'] == 'refresh_token':
            if data['refresh_token'] == 'dummyrefreshtoken':
                token = self.get_counted('dummyaccesstoken')
                self.tokens[token] = True

                data = {
                    'access_token' : token,
                    'expires_in'   : 300,
                    'refresh_token': 'dummyrefreshtoken',
                    'scopes'       : 'READSYSTEM',
                    'token_type'   : 'bearer',
                }
                return web.json_response(data = data)
            else:
                raise Exception("unexpected refresh token")
        else:
            raise JsonError(400, "invalid_request", 'unknown grant_type: {}'.format(data['grant_type']))

    @oauth_error_response
    async def on_oauth_authorize(self, request):
        self.requests_update('on_oauth_authorize')

        await request.post()
        query = request.query
        _LOGGER.info(query)
        assert 'redirect_uri'  in query
        assert 'response_type' in query
        assert 'scope'         in query
        assert 'state'         in query

        url = list(urlsplit(query['redirect_uri']))
        url[3] = urlencode({
            'state': query['state'],
            'code' : 'dummycode',
        })

        return aiohttp.web.HTTPFound(urlunsplit(url))

    def expire_tokens(self):
        for t in self.tokens:
            self.tokens[t] = False

    def add_system(self, systemid):
        self.systems[systemid] = System({}, {})

    def add_parameter(self, systemid, parameter):
        self.systems[systemid].parameters[parameter['name']] = parameter

    def add_notification(self, systemid, notification):
        self.systems[systemid].notifications[notification['notificationId']] = notification

    async def check_auth(self, request):
        auth = request.headers.get('AUTHORIZATION')

        if not auth.startswith('Bearer '):
            raise HTTPUnauthorized()
        token = auth[7:]
        if token not in self.tokens:
            raise HTTPUnauthorized()

        if not self.tokens[token]:
            raise HTTPUnauthorized()

    async def on_notifications(self, request):
        self.requests_update('on_notifications')

        await self.check_auth(request)

        systemid = int(request.match_info['systemId'])
        notifications = self.systems[systemid].notifications

        return web.json_response({
            "page": 1,
            "itemsPerPage": 2,
            "numItems": len(notifications),
            "objects": list(notifications.values())
        })

    async def on_get_parameters(self, request):
        self.requests_update('on_get_parameters')

        await self.check_auth(request)

        systemid    = int(request.match_info['systemId'])
        parameters  = request.query.getall('parameterIds')
        return web.json_response(
            [self.systems[systemid].parameters[str(p)] for p in parameters]
        )

    async def on_put_parameters(self, request):
        self.requests_update('on_put_parameters')

        await self.check_auth(request)

        systemid = int(request.match_info['systemId'])
        data = await request.json()
        response = []

        for key, value in data['settings'].items():
            response.append({
                'status'   : 'DONE',
                'parameter': self.systems[systemid].parameters[str(key)]
            })

        return web.json_response(response)
