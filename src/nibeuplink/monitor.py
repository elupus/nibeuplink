"""Helpers to monitor state."""
import asyncio
import logging
from typing import Callable

from .const import MAX_REQUEST_PARAMETERS
from .utils import cyclic_tuple
from .typing import ParameterSet

_LOGGER = logging.getLogger(__name__)

class Monitor():
    def __init__(self,
                 uplink: 'Uplink',
                 chunks: int = MAX_REQUEST_PARAMETERS):
        self._uplink = uplink
        self._callbacks = {}
        self._iterator = cyclic_tuple(self._callbacks, chunks)

    def add(self, system_id: int, parameter_id: str, callback: Callable[[ParameterSet], None]):
        key = (system_id, parameter_id)
        self._callbacks.setdefault(
            key, []).append(callback)

    def remove(self, callback: Callable[[ParameterSet], None]):
        to_remove = []
        for key, value in self._callbacks.items():
            if callback in value:
                if len(value) == 1:
                    to_remove.append(key)
                else:
                    value.remove(callback)
        for key in to_remove:
            del self._callbacks[key]

    def call_callbacks(self, system_id, parameters):
        parameter_set = {}
        callbacks = []

        for parameter in parameters:
            if not parameter:
                _LOGGER.debug("Parameter not found for system %s", system_id)
                continue

            parameter_set[parameter['name']] = parameter
            callbacks.extend(self._callbacks.get((system_id, parameter['name']), []))

        for callback in callbacks:
            callback(system_id, parameter_set)

    async def run_once(self):
        system_id, parameter_ids = next(self._iterator)
        if not system_id:
            return

        parameters = await asyncio.gather(*[
            self._uplink.get_parameter(system_id, parameter_id)
            for parameter_id in parameter_ids
        ])

        self.call_callbacks(system_id, parameters)

    async def run(self):
        while True:
            asyncio.sleep(4.5)
            await self.run_once()
