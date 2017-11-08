import logging
import sys
import os
import pickle
from itertools import islice

from requests_oauthlib import OAuth2Session

_LOGGER = logging.getLogger(__name__)

MAX_REQUEST_PARAMETERS   = 15

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
        self.update_systems()
        for system_id in self.systems.keys():
            self.update_categories(system_id)
            #self.update_parameters(system_id)

    def update_systems(self):
        _LOGGER.debug("Requesting systems")
        data = self.get('systems')
        for s in data['objects']:
            system = self.get_system(s['systemId'])
            system.data = s

    def update_categories(self, system_id):
        _LOGGER.debug("Requesting categories on system {}".format(system_id))

        system = self.get_system(system_id)
        data   = self.get('systems/{}/serviceinfo/categories'.format(system_id),
                          {'parameters' : 'True'})

        for c in data:
            category = self.get_category(system_id, c['categoryId'])
            category.name = c['name']
            category.parameter_ids = [ p['parameterId'] for p in c['parameters'] ]
            for p in c['parameters']:
                parameter = self.get_parameter(system_id, p['parameterId'])
                parameter.data = p

    def update_parameters(self, system_id):
        system = self.get_system(system_id)
        for parameters in chunks(system.parameters, MAX_REQUEST_PARAMETERS):
            _LOGGER.debug("Requesting parmeters {}".format(parmeters))
            data = self.get(
                        'systems/{}/parameters'.format(system.system_id),
                        { 'parameterIds' : parameters.keys() }
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