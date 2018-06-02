import logging
import asyncio
import socket
import ssl
from functools import wraps
from urllib.parse import urlencode, urljoin, urlsplit, urlunsplit, parse_qs, parse_qsl

import aiohttp
from aiohttp            import web
from aiohttp.resolver   import DefaultResolver
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
                'error'            : self.error,
                'error_description': self.description
            }
            return web.json_response(data = data, status = self.status)
    return wrapper


class Uplink:
    def __init__(self, loop):
        self.loop    = loop
        self.app     = web.Application(loop=loop)
        self.app.router.add_routes([
            web.post('/oauth/token', self.on_oauth_token),
            web.post('/oauth/authorize', self.on_oauth_authorize),
            web.get('/api/v1/systems/{systemId}/notifications', self.on_notifications),
        ])
        self.handler  = None
        self.server   = None
        self.base     = None
        self.redirect = None
        self.systems  = {}


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
        data = await request.post()
        if data['grant_type'] == 'authorization_code':
            data = {
                'access_token' : 'dummyaccesstoken',
                'expires_in'   : 300,
                'refresh_token': 'dummyrefreshtoken',
                'scopes'       : 'READSYSTEM',
                'token_type'   : 'bearer',
            }
            return web.json_response(data = data)

        elif data['grant_type'] == 'refresh_token':
            raise Exception("not implemented")
        else:
            raise JsonError(400, "invalid_request", 'unknown grant_type: {}'.format(data['grant_type']))
    
    @oauth_error_response
    async def on_oauth_authorize(self, request):
        data = await request.post()
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

    def add_parameter(self, systemid, parameter):
        self.systems[systemid] = {}

    async def on_notifications(self, request):
        systemId = request.match_info['systemId']
        return web.json_response(
            {
              "page": 1,
              "itemsPerPage": 2,
              "numItems": 1,
              "objects": [
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
                  },
                ]
              }
          )
