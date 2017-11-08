import logging
import sys
import os
import pickle
from itertools import islice

from requests_oauthlib import OAuth2Session

_LOGGER = logging.getLogger(__name__)

SCOPE               = [ 'READSYSTEM' ]

BASE_URL            = 'https://api.nibeuplink.com'
TOKEN_URL           = '%s/oauth/token' % BASE_URL
AUTH_URL            = '%s/oauth/authorize' % BASE_URL

os.environ['OAUTHLIB_INSECURE_TRANSPORT'] = '1'

def chunks(data, SIZE):
    it = iter(data)
    for i in range(0, len(data), SIZE):
        yield {k:data[k] for k in islice(it, SIZE)}

class OAuth2(OAuth2Session):
    def __init__(self, client_id, client_secret, redirect_uri, token, token_updater):
        self.client_secret = client_secret

        extra = {
            'client_id'    : client_id,
            'client_secret': client_secret,
        }

        super().__init__(
            client_id            = client_id,
            redirect_uri         = redirect_uri,
            auto_refresh_url     = TOKEN_URL,
            auto_refresh_kwargs  = extra,
            scope                = SCOPE,
            token                = token,
            token_updater        = token_updater)

    def authorization_url(self):
        return super().authorization_url(AUTH_URL)

    def fetch_token(self, authorization_response):
        token = super().fetch_token(
            TOKEN_URL,
            client_secret          = self.client_secret,
            authorization_response = authorization_response)
        self.token_updater(token)
        return token


class System():
    def __init__(self, uplink, system_id):
        self.uplink     = uplink
        self.system_id  = system_id
        self.parameters = {}
        self.data       = None

class Parameter():
    def __init__(self, uplink, system_id, parameter_id):
        self.uplink       = uplink
        self.system_id    = system_id
        self.parameter_id = parameter_id
        self.data         = None

class Uplink():

    def __init__(self, session):
        self.session    = session
        self.systems    = {}

    def get(self, uri, params = {}):
        if not self.session.authorized:
            return None

        headers = {}
        url = '%s/api/v1/%s' % (BASE_URL, uri)
        data = self.session.get(url, params=params, headers=headers).json()
        _LOGGER.debug(data)
        return data

    def update(self):
        for system_id in self.systems.keys():
            self.update_parameters(system_id)

    def update_parameters(self, system_id):
            system = self.get_system(system_id)
            for parameters in chunks(system.parameters, MAX_REQUEST_PARAMETERS):
                _LOGGER.debug(parameters)

                data = self.get(
                            'systems/{}/parameters'.format(system.system_id),
                            { 'parameterIds' : parameters.keys() }
                       )

                for parameter in data:
                    p = self.get_parameter(system.system_id, parameter['parameterId'])
                    p.data = data

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