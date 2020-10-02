import aiohttp
import logging
import uuid

from datetime import datetime, timedelta
from urllib.parse import urlencode, urlsplit, parse_qs

from .exceptions import UplinkResponseException, UplinkException


_LOGGER = logging.getLogger(__name__)


async def raise_for_status(response):
    if 400 <= response.status:
        e = aiohttp.ClientResponseError(
            response.request_info,
            response.history,
            code=response.status,
            headers=response.headers,
        )

        if "json" in response.headers.get("CONTENT-TYPE", ""):
            data = await response.json()
            e.message = str(data)
            raise UplinkResponseException(data.get("errorCode"), data) from e

        else:
            data = await response.text()
            raise UplinkException(data) from e


class BearerAuth(aiohttp.BasicAuth):
    def __init__(self, access_token):
        self.access_token = access_token

    def encode(self):
        return "Bearer {}".format(self.access_token)


class UplinkSession:
    def __init__(
        self,
        client_id,
        client_secret,
        redirect_uri,
        access_data=None,
        access_data_write=None,
        base="https://api.nibeuplink.com",
        scope=["READSYSTEM"],
    ):
        self.redirect_uri = redirect_uri
        self.client_id = client_id
        self.client_secret = client_secret
        self.access_data_write = access_data_write
        self.access_data = None
        self.session = None
        self.scope = scope
        self.base = base

        # check that the access scope is enough, otherwise ignore
        if access_data:
            if set(scope).issubset(set(access_data["scope"].split(" "))):
                self.access_data = access_data
            else:
                _LOGGER.info(
                    "Ignoring access data due to changed scope {}".format(scope)
                )

    async def __aenter__(self):
        await self.open()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.close()

    async def open(self):

        headers = {
            "Accept": "application/json",
            "Content-Type": "application/x-www-form-urlencoded;charset=UTF-8",
        }

        self.session = aiohttp.ClientSession(
            headers=headers, auth=aiohttp.BasicAuth(self.client_id, self.client_secret)
        )

        if self.access_data:
            await self.refresh_access_token()

    async def close(self):
        if self.session:
            await self.session.close()
            self.session = None

    def _handle_access_token(self, data):
        if "access_token" not in data:
            raise ValueError("Error in reply {}".format(data))

        if "expires_in" in data:
            _LOGGER.debug("Token will expire in %s seconds", data["expires_in"])
            expires = datetime.now() + timedelta(seconds=data["expires_in"])
        else:
            expires = None

        data["access_token_expires"] = expires.isoformat()

        self.access_data = data
        if self.access_data_write:
            self.access_data_write(data)

    async def _get_auth(self):
        if self.access_data:
            return BearerAuth(self.access_data["access_token"])
        else:
            return None

    async def get_access_token(self, code):
        payload = {
            "grant_type": "authorization_code",
            "code": code,
            "redirect_uri": self.redirect_uri,
        }

        async with self.session.post(
            "{}/oauth/token".format(self.base), data=payload
        ) as response:
            await raise_for_status(response)
            self._handle_access_token(await response.json())

    async def refresh_access_token(self):
        if not self.access_data or "refresh_token" not in self.access_data:
            _LOGGER.warning("No refresh token available for refresh")
            return

        _LOGGER.debug(
            "Refreshing access token with refresh token %s",
            self.access_data["refresh_token"],
        )
        payload = {
            "grant_type": "refresh_token",
            "refresh_token": self.access_data["refresh_token"],
        }

        async with self.session.post(
            "{}/oauth/token".format(self.base), data=payload
        ) as response:
            await raise_for_status(response)
            self._handle_access_token(await response.json())

    def get_authorize_url(self, state=None):
        if not state:
            state = uuid.uuid4().hex
        self.state = state

        params = {
            "response_type": "code",
            "client_id": self.client_id,
            "redirect_uri": self.redirect_uri,
            "scope": " ".join(self.scope),
            "state": state,
        }

        return "{}/oauth/authorize?{}".format(self.base, urlencode(params))

    def get_code_from_url(self, url):
        query = parse_qs(urlsplit(url).query)
        if "state" in query and query["state"][0] != self.state:
            raise ValueError(
                "Invalid state in url {} expected {}".format(query["state"], self.state)
            )
        return query["code"][0]

    async def request(self, *args, **kw):
        response = await self.session.request(*args, auth=await self._get_auth(), **kw)
        try:
            if response.status == 401:
                _LOGGER.debug(response)
                _LOGGER.info("Attempting to refresh token due to error in request")
                await self.refresh_access_token()
                response.close()
                response = await self.session.request(
                    *args, auth=await self._get_auth(), **kw
                )

            await raise_for_status(response)

            if "json" in response.headers.get("CONTENT-TYPE", ""):
                data = await response.json()
            else:
                data = await response.text()

            return data

        finally:
            response.close()
