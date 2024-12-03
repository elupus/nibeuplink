********************************
Nibe Uplink Communciation Module
********************************

Deprecation
===========

.. warning::

    Nibe is shutting down nibeuplink.com which this integration is dependent upon. This project is therefor deprecated. Upgrade your heatpump and swith to myuplink solution, use built in modbus server on S-series pumps or add a nibegw device like https://github.com/elupus/esphome-nibe to use the native support inside home assistant instead.


Module
======

The module is an asyncio driven interface to nibe uplink public API. It is throttled to one http request every 4 seconds so
try to make the most of your requests by batching requests.

Status
______
.. image:: https://github.com/elupus/nibeuplink/actions/workflows/python-package.yml/badge.svg
    :target: https://github.com/elupus/nibeuplink/actions/workflows/python-package.yml

.. image:: https://codecov.io/gh/elupus/nibeuplink/branch/master/graph/badge.svg?token=WZy5CcdYom
    :target: https://codecov.io/gh/elupus/nibeuplink
    

Example
_______

.. code-block:: python


    def token_read():
        return None

    def token_write(token):
        pass

    async def run():
        async with nibeuplink.Uplink(client_id         = 'XXX',
                                     client_secret     = 'YYY',
                                     redirect_uri      = 'ZZZ',
                                     access_data       = token_read(),
                                     access_data_write = token_write,
                                     scope             = 'READSYSTEM') as uplink:

            if not uplink.access_data:
                auth_uri = uplink.get_authorize_url()
                print(auth_uri)
                result = input('Enter full redirect url: ')
                await uplink.get_access_token(uplink.get_code_from_url(result))

            # Request all systems
            print(uplink.get_systems())


            # Request data for specific system
            print(uplink.get_system(12345))

            # Request data for parameters. Note request them in paralell using gather semantics
            # that way, the module with batch up the requests into a single request to api 
            print(await asyncio.gather(uplink.get_parameter(12345, 11111),
                                       uplink.get_parameter(12345, 22222)))




    loop = asyncio.get_event_loop()
    loop.run_until_complete (run())




Console
=======

The module contains a commandline utility to test and request data from Nibe Uplink called ``nibeuplink``, it will store token information in a file in the current directory called nibeuplink.json

Example
_______

Help for utility

.. code-block:: bash

    nibeuplink -h

Request all systems

.. code-block:: bash

    nibeuplink --client_id 'XXX' --client_secret 'YYY' --redirect_uri 'ZZZ'


Request data for specific system

.. code-block:: bash

    nibeuplink --client_id 'XXX' --client_secret 'YYY' --redirect_uri 'ZZZ' --system 12345

Request data for parameters

.. code-block:: bash

    nibeuplink --client_id 'XXX' --client_secret 'YYY' --redirect_uri 'ZZZ' --system 12345 --parameter 11111 22222
