import logging
import sys
import os
import pickle

from requests_oauthlib import OAuth2Session

_LOGGER = logging.getLogger(__name__)

SCOPE               = [ 'READSYSTEM' ]

BASE                = 'https://api.nibeuplink.com'
TOKEN_URL           = '%s/oauth/token' % BASE
AUTH_URL            = '%s/oauth/authorize' % BASE

os.environ['OAUTHLIB_INSECURE_TRANSPORT'] = '1'

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



class Uplink():

    def __init__(self, session):
        self.session         = session





