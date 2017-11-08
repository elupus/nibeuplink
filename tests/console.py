import logging
import sys

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

_LOGGER.debug(token_read())
oauth2 = nibeuplink.OAuth2(args.client_id, args.client_secret, args.redirect_uri, token_read(), token_write)
if not oauth2.authorized:
	auth_uri, state = oauth2.authorization_url()
	print(auth_uri)
	result = input('Enter full redirect url: ')

	token = oauth2.fetch_token(result)
	print(token)


uplink = nibeuplink.Uplink(oauth2)
uplink.get_parameter(36563, '43424')
uplink.get_parameter(36563, '40032')
uplink.update()
print(uplink.get_parameter(36563, '43424'))