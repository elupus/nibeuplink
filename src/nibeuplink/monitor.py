"""Helpers to monitor state."""
import asyncio
import logging
from typing import Callable, Dict, Tuple, List

from .const import MAX_REQUEST_PARAMETERS
from .utils import cyclic_tuple
from .typing import ParameterSet, SystemId, ParameterId, Parameter
from .uplink import Uplink

_LOGGER = logging.getLogger(__name__)

Callback = Callable[[SystemId, ParameterSet], None]

class Monitor():
    def __init__(self,
                 uplink: Uplink,
                 chunks: int = MAX_REQUEST_PARAMETERS):
        self._uplink = uplink
        self._callbacks = []  # type: List[Callback]
        self._parameters = []  # type: List[Tuple[SystemId, ParameterId]]
        self._iterator = cyclic_tuple(self._parameters, chunks)

    def add_callback(self, callback):
        self._callbacks.append(callback)

    def del_callback(self, callback):
        self._callbacks.remove(callback)

    def add(self, system_id: SystemId, parameter_id: ParameterId):
        key = (system_id, parameter_id)
        self._parameters.append(key)

    def remove(self, system_id: SystemId, parameter_id: ParameterId):
        key = (system_id, parameter_id)
        self._parameters.remove(key)

    def call_callbacks(self, system_id: SystemId, parameters: List[Parameter]):
        parameter_set = {} #  type: ParameterSet

        for parameter in parameters:
            if not parameter:
                _LOGGER.debug("Parameter not found for system %s", system_id)
                continue

            parameter_set[parameter['name']] = parameter

        for callback in self._callbacks:
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
