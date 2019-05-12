import logging
import sys
import asyncio
import json
from urllib.parse import urldefrag, parse_qs

import nibeuplink
import argparse
import cattr

_LOGGER = logging.getLogger(__name__)

def pair(arg):
    data = arg.split('=')
    return (data[0], data[1])

def thermostat(arg):
    data = json.loads(arg)
    return cattr.structure(data, nibeuplink.SetThermostatModel)

parser = argparse.ArgumentParser(description='Read data from nibe uplink.')
parser.add_argument('--client_id'    , required=True)
parser.add_argument('--client_secret', required=True)
parser.add_argument('--redirect_uri' , required=True)

parser.add_argument('--system', type=int)
parser.add_argument('--categories', action='store_true')
parser.add_argument('--category', nargs='+')
parser.add_argument('--status', action='store_true')
parser.add_argument('--parameter', nargs='+', type=str)
parser.add_argument('--put_parameter', nargs='+', type=pair)
parser.add_argument('--units', action='store_true')
parser.add_argument('--alarms', action='store_true')
parser.add_argument('--info', action='store_true')
parser.add_argument('--unit', type=int, default=0)
parser.add_argument('--unit_status', action='store_true')
parser.add_argument('--subsystems', action='store_true')
parser.add_argument('--verbose', action='store_true')
parser.add_argument('--smarthome_mode', action='store_true')
parser.add_argument('--put_smarthome_mode', type=str)
parser.add_argument('--smarthome_thermostats', action='store_true')
parser.add_argument('--post_smarthome_thermostats', type=thermostat)

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

def token_write(token):
    with open(STORE, 'w') as myfile:
        json.dump(token,
                  myfile,
                  indent=2)


async def run():

    scope = ['READSYSTEM']
    if args.put_parameter or args.put_smarthome_mode:
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
                todo.extend([uplink.get_categories(args.system, False, args.unit)])

            if args.category:
                todo.extend([uplink.get_category(args.system, p, args.unit) for p in args.category])

            if args.status:
                todo.extend([uplink.get_status(args.system)])

            if args.unit_status:
                todo.extend([uplink.get_unit_status(args.system, args.unit)])

            if args.units:
                todo.extend([uplink.get_units(args.system)])

            if args.alarms:
                todo.extend([uplink.get_notifications(args.system)])

            if args.info:
                todo.extend([uplink.get_notifications(args.system, notifiction_type=1)])

            if args.put_parameter:
                todo.extend([uplink.put_parameter(args.system, p[0], p[1]) for p in args.put_parameter])

            if args.smarthome_mode:
                todo.extend([uplink.get_smarthome_mode(args.system)])

            if args.put_smarthome_mode:
                todo.extend([uplink.put_smarthome_mode(args.system, args.put_smarthome_mode)])

            if args.smarthome_thermostats:
                todo.extend([uplink.get_smarthome_thermostats(args.system)])

            if args.post_smarthome_thermostats:
                todo.extend([uplink.post_smarthome_thermostats(args.system, args.post_smarthome_thermostats)])

            if args.subsystems:
                async def named(coroutine):
                    data = await coroutine
                    return [x.name for x in data.values()]
                todo.extend([
                    named(nibeuplink.get_active_climate(uplink, args.system)),
                    named(nibeuplink.get_active_hotwater(uplink, args.system)),
                    named(nibeuplink.get_active_ventilations(uplink, args.system)),
                ])

            if not len(todo):
                todo.extend([uplink.get_system(args.system)])

        res = await asyncio.gather(*todo)
        for a in res:
            try:
                print(json.dumps(a, indent=1))
            except TypeError:
                print(a)

def main():
    loop = asyncio.get_event_loop()
    loop.run_until_complete (run())

if __name__ == '__main__':
    main()
