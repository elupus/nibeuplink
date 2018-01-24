import unittest
import nibeuplink
import asyncio


class AioTestCase(unittest.TestCase):

    # noinspection PyPep8Naming
    def __init__(self, methodName='runTest', loop=None):
        self.loop = loop or asyncio.get_event_loop()
        self._function_cache = {}
        super(AioTestCase, self).__init__(methodName=methodName)

    def coroutine_function_decorator(self, func):
        def wrapper(*args, **kw):
            return self.loop.run_until_complete(func(*args, **kw))
        return wrapper

    def __getattribute__(self, item):
        attr = object.__getattribute__(self, item)
        if asyncio.iscoroutinefunction(attr):
            if item not in self._function_cache:
                self._function_cache[item] = self.coroutine_function_decorator(attr)
            return self._function_cache[item]
        return attr

DEFAULT_CLIENT_ID     = '12345'
DEFAULT_CLIENT_SECRET = '4567'
DEFAULT_REDIRECT_URI  = 'uri:some%20long%20uri'
DEFAULT_SCOPE         = ['A', 'B', 'C']
DEFAULT_CODE          = '789'

class TestUnauthenticated(AioTestCase):
    uplink = None

    async def setUp(self):
        def access_write(self, data):
            pass

        self.uplink = nibeuplink.Uplink(DEFAULT_CLIENT_ID,
                                        DEFAULT_CLIENT_SECRET,
                                        DEFAULT_REDIRECT_URI,
                                        None,
                                        access_write,
                                        scope = DEFAULT_SCOPE,
                                        loop = self.loop)

    async def tearDown(self):
        await self.uplink.close()
        self.uplink = None

    async def test_status(self):
            self.assertFalse(self.uplink.access_data)

    async def test_get_authorize_url(self):
            from urllib.parse import (urlsplit, parse_qs)

            o = urlsplit(self.uplink.get_authorize_url())
            q = parse_qs(o.query)

            self.assertEqual(q['response_type'], ['code'])
            self.assertEqual(q['client_id'],     [DEFAULT_CLIENT_ID])
            self.assertEqual(q['redirect_uri'],  [DEFAULT_REDIRECT_URI])
            self.assertEqual(q['scope'],         [' '.join(DEFAULT_SCOPE)])

    async def test_get_code_from_url(self):
            from urllib.parse import (urlsplit, parse_qs)
            o = urlsplit(self.uplink.get_authorize_url())
            q = parse_qs(o.query)


            # valid state
            url = "{}?state={}&code={}".format(DEFAULT_REDIRECT_URI, q['state'][0], DEFAULT_CODE)
            self.assertEqual(DEFAULT_CODE, self.uplink.get_code_from_url(url))

            # no state
            url = "{}?code={}".format(DEFAULT_REDIRECT_URI, DEFAULT_CODE)
            self.assertEqual(DEFAULT_CODE, self.uplink.get_code_from_url(url))

            # invalid state
            url = "{}?state={}&code={}".format(DEFAULT_REDIRECT_URI, "junk", DEFAULT_CODE)
            self.assertRaises(ValueError, self.uplink.get_code_from_url, url)


if __name__ == '__main__':
    unittest.main()