import logging
import sys
import asyncio
import json
from urllib.parse import urldefrag, parse_qs

import nibeuplink
import argparse

_LOGGER = logging.getLogger(__name__)

def pair(arg):
    data = arg.split('=')
    return (data[0], data[1])

parser = argparse.ArgumentParser(description='Read data from nibe uplink.')
parser.add_argument('--client_id'    , required=True)
parser.add_argument('--client_secret', required=True)
parser.add_argument('--redirect_uri' , required=True)

parser.add_argument('--system', type=int)
parser.add_argument('--categories', action='store_true')
parser.add_argument('--category', nargs='+')
parser.add_argument('--status', action='store_true')
parser.add_argument('--parameter', nargs='+', type=str)
parser.add_argument('--setparameter', nargs='+', type=pair)
parser.add_argument('--units', action='store_true')
parser.add_argument('--notifications', action='store_true')
parser.add_argument('--unit', nargs='+', type=int)
parser.add_argument('--verbose', action='store_true')

args = parser.parse_args()

if args.verbose:
    root = logging.getLogger()
    root.setLevel(logging.DEBUG)

    ch = logging.StreamHandler(sys.stdout)
    ch.setLevel(logging.DEBUG)
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    ch.setFormatter(formatter)
    root.addHandler(ch)


STORE = 'nibeuplink.json'

def token_read():
    try:
        with open(STORE, 'r') as myfile:
            return json.load(myfile)
    except FileNotFoundError:
        return None
    except:
        _LOGGER.warning('Failed to load previous token: %s' % sys.exc_info()[0])
        return None

def token_write(token):
    with open(STORE, 'w') as myfile:
        json.dump(token, myfile, indent=2)


async def run():


    scope = ['READSYSTEM']
    if args.setparameter:
        scope.append('WRITESYSTEM')

    async with nibeuplink.Uplink(client_id         = args.client_id,
                                 client_secret     = args.client_secret,
                                 redirect_uri      = args.redirect_uri,
                                 access_data       = token_read(),
                                 access_data_write = token_write,
                                 scope             = scope) as uplink:


        if not uplink.access_data:
            auth_uri = uplink.get_authorize_url()
            print(auth_uri)
            result = input('Enter full redirect url: ')
            await uplink.get_access_token(uplink.get_code_from_url(result))

        todo = []
        if not args.system:
            todo.extend([uplink.get_systems()])
        else:

            if args.parameter:
                todo.extend([uplink.get_parameter(args.system, p) for p in args.parameter])

            if args.categories:
                todo.extend([uplink.get_categories(args.system, False)])

            if args.category:
                todo.extend([uplink.get_category(args.system, p) for p in args.category])

            if args.status:
                todo.extend([uplink.get_status(args.system)])

            if args.units:
                todo.extend([uplink.get_units(args.system)])

            if args.unit:
                todo.extend([uplink.get_unit_status(args.system, p) for p in args.unit])

            if args.notifications:
                todo.extend([uplink.get_notifications(args.system)])

            if args.setparameter:
                todo.extend([uplink.set_parameter(args.system, p[0], p[1]) for p in args.setparameter])

            if not len(todo):
                todo.extend([uplink.get_system(args.system)])

        res = await asyncio.gather(*todo)
        print(json.dumps(res, indent=1))



def main():
    loop = asyncio.get_event_loop()
    loop.run_until_complete (run())

