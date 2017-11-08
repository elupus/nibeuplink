import logging
import sys
import asyncio
from urllib.parse import urldefrag, parse_qs

root = logging.getLogger()
root.setLevel(logging.DEBUG)

ch = logging.StreamHandler(sys.stdout)
ch.setLevel(logging.DEBUG)
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
ch.setFormatter(formatter)
root.addHandler(ch)


import nibeuplink
import argparse
import pickle

_LOGGER = logging.getLogger(__name__)


parser = argparse.ArgumentParser(description='Read data from nibe uplink.')
parser.add_argument('client_id')
parser.add_argument('client_secret')
parser.add_argument('redirect_uri')

args = parser.parse_args()

STORE = 'console.pickle'

def token_read():
    try:
        with open(STORE, 'rb') as myfile:
            return pickle.load(myfile)
    except FileNotFoundError:
        return None
    except:
        _LOGGER.warning('Failed to load previous token: %s' % sys.exc_info()[0])
        return None

def token_write(token):
    with open(STORE, 'wb') as myfile:
        pickle.dump(token, myfile)


async def run():

    _LOGGER.debug(token_read())
    async with nibeuplink.Uplink(client_id         = args.client_id,
                                 client_secret     = args.client_secret,
                                 redirect_uri      = args.redirect_uri,
                                 access_data       = token_read(),
                                 access_data_write = token_write) as uplink:


        if not uplink.access_data:
            auth_uri = uplink.get_authorize_url()
            print(auth_uri)
            result = input('Enter full redirect url: ')
            await uplink.get_access_token(uplink.get_code_from_url(result))

        await uplink.update()

loop = asyncio.get_event_loop()
loop.run_until_complete (run())



#uplink = nibeuplink.Uplink(oauth2)
#uplink.get_parameter(36563, '43424')
#uplink.get_parameter(36563, 47398)
#uplink.update()
#print(uplink.get_parameter(36563, 47398))