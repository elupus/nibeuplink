"""Handler for uplink."""
import attr
import logging
import asyncio
import aiohttp
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Union, cast

from .utils import chunks, chunk_pop
from .typing import (
    CategoryType, ParameterType, StatusItemIcon,
    ParameterId,
    Thermostat,
    SetThermostatModel,
    System,
    SystemUnit,
)
from .const import MAX_REQUEST_PARAMETERS

_LOGGER = logging.getLogger(__name__)


class ParameterRequest:
    def __init__(self, parameter_id: str):
        self.parameter_id = parameter_id
        self.data: Optional[ParameterType] = None
        self.done = False


class Throttle:
    """
    Throttling requests to API.

    Works by awaiting our turn then executing the request,
    and scheduling next request at a delay after the previous
    request completed.
    """

    def __init__(self, delay):
        self._delay = delay
        self._timestamp = datetime.now()

    async def __aenter__(self):
        timestamp = datetime.now()
        delay = (self._timestamp - timestamp).total_seconds()
        if delay > 0:
            _LOGGER.debug("Delaying request by %s seconds due to throttle", delay)
            await asyncio.sleep(delay)
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        self._timestamp = datetime.now() + self._delay


class Uplink:
    def __init__(
        self, session, loop=None, base="https://api.nibeuplink.com", throttle=4.5
    ):

        self.state = None
        self.lock = asyncio.Lock()
        self.throttle = Throttle(timedelta(seconds=throttle))
        self.session = session
        self.loop = loop
        self.base = base
        self.requests: Dict[int, List[ParameterRequest]] = {}

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.close()

    async def close(self):
        """Close uplink and clear any outstanding requests"""
        async with self.lock:
            for requests in self.requests.values():
                while requests:
                    requests.pop().done = True

    async def get(self, url, *args, **kwargs):
        return await self.session.request(
            "GET", f"{self.base}/api/v1/{url}", *args, **kwargs
        )

    async def put(self, url, *args, **kwargs):
        return await self.session.request(
            "PUT", f"{self.base}/api/v1/{url}", *args, **kwargs
        )

    async def post(self, url, *args, **kwargs):
        return await self.session.request(
            "POST", f"{self.base}/api/v1/{url}", *args, **kwargs
        )

    async def get_parameter_raw(self, system_id: int, parameter_id: ParameterId) -> Optional[ParameterType]:

        request = ParameterRequest(str(parameter_id))
        if system_id not in self.requests:
            self.requests[system_id] = []
        self.requests[system_id].append(request)

        # yield to any other runnable that want to add requests
        await asyncio.sleep(0)

        while True:
            async with self.lock:

                # check if we are already finished, by somebody elses request
                if request.done:
                    break

                if len(self.requests[system_id]) == 0:
                    break

                async with self.throttle:
                    # chop of as many requests from start as possible
                    requests = chunk_pop(
                        self.requests[system_id], MAX_REQUEST_PARAMETERS
                    )

                    _LOGGER.debug(
                        "Requesting parameters {}".format(
                            [str(x.parameter_id) for x in requests]
                        )
                    )

                    data = await self.get(
                        f"systems/{system_id}/parameters",
                        params=[
                            ("parameterIds", str(x.parameter_id)) for x in requests
                        ],
                        headers={},
                    )

                lookup = {p["name"]: p for p in data}

                for r in requests:
                    r.done = True
                    if r.parameter_id in lookup:
                        r.data = lookup[r.parameter_id]

        return request.data

    def add_parameter_extensions(self, data: Optional[ParameterType]):
        if data:
            if data["displayValue"].endswith(data["unit"]) and len(data["unit"]):
                value: Union[str, float] = data["displayValue"][: -len(data["unit"])]

                try:
                    value = float(value)
                except ValueError:
                    pass

                data["value"] = value
            elif data["displayValue"] == "--":
                data["value"] = None
            else:
                data["value"] = data["displayValue"]

    async def get_parameter(self, system_id: int, parameter_id: ParameterId):
        data = await self.get_parameter_raw(system_id, parameter_id)
        self.add_parameter_extensions(data)
        return data

    async def put_parameter(
        self, system_id: int, parameter_id: ParameterId, value: Any
    ):
        headers = {
            "Accept": "application/json",
            "Content-Type": "application/json;charset=UTF-8",
        }

        data = {"settings": {str(parameter_id): value}}
        async with self.lock, self.throttle:
            result = await self.put(
                f"systems/{system_id}/parameters", json=data, headers=headers,
            )
        return result[0]["status"]

    async def get_system(self, system_id: int) -> System:
        _LOGGER.debug("Requesting system {}".format(system_id))
        async with self.lock, self.throttle:
            return cast(System, await self.get(f"systems/{system_id}"))

    async def get_systems(self) -> List[System]:
        _LOGGER.debug("Requesting systems")
        async with self.lock, self.throttle:
            data = await self.get("systems")
            return cast(List[System], data["objects"])

    async def get_category_raw(
        self, system_id: int, category_id: str, unit_id: int = 0
    ) -> List[ParameterType]:
        _LOGGER.debug(
            "Requesting category {} on system {}".format(category_id, system_id)
        )
        async with self.lock, self.throttle:
            return await self.get(
                f"systems/{system_id}/serviceinfo/categories/{category_id}",
                {"systemUnitId": unit_id},
            )

    async def get_category(self, system_id: int, category_id: str, unit_id: int = 0) -> List[ParameterType]:
        data = await self.get_category_raw(system_id, category_id, unit_id)
        for param in data:
            self.add_parameter_extensions(param)
        return data

    async def get_categories(self, system_id: int, parameters: bool, unit_id: int = 0) -> List[CategoryType]:
        _LOGGER.debug("Requesting categories on system {}".format(system_id))

        async with self.lock, self.throttle:
            data: List[CategoryType] = await self.get(
                f"systems/{system_id}/serviceinfo/categories",
                params={"parameters": str(parameters), "systemUnitId": unit_id},
            )
        for category in data:
            if category["parameters"]:
                for param in category["parameters"]:
                    self.add_parameter_extensions(param)
        return data

    async def get_status_raw(self, system_id: int):
        _LOGGER.debug("Requesting status on system {}".format(system_id))
        async with self.lock, self.throttle:
            return await self.get(f"systems/{system_id}/status/system")

    async def get_status(self, system_id: int) -> List[StatusItemIcon]:
        data = await self.get_status_raw(system_id)
        for status in data:
            if status["parameters"]:
                for param in status["parameters"]:
                    self.add_parameter_extensions(param)
        return data

    async def get_units(self, system_id: int) -> List[SystemUnit]:
        _LOGGER.debug("Requesting units on system {}".format(system_id))
        async with self.lock, self.throttle:
            return await self.get(f"systems/{system_id}/units")

    async def get_unit_status(self, system_id: int, unit_id: int):
        _LOGGER.debug("Requesting unit {} on system {}".format(unit_id, system_id))
        async with self.lock, self.throttle:
            data = await self.get(f"systems/{system_id}/status/systemUnit/{unit_id}")
        for status in data:
            if status["parameters"]:
                for param in status["parameters"]:
                    self.add_parameter_extensions(param)
        return data

    async def get_notifications(
        self, system_id: int, active: bool = True, notifiction_type: str = "ALARM"
    ):
        _LOGGER.debug("Requesting notifications on system {}".format(system_id))
        params = {
            "active": str(active),
            "itemsPerPage": 100,
            "type": notifiction_type,
        }
        async with self.lock, self.throttle:
            data = await self.get(f"systems/{system_id}/notifications", params=params)
        return data["objects"]

    async def get_smarthome_mode(self, system_id: int) -> str:
        async with self.lock, self.throttle:
            data = await self.get(f"systems/{system_id}/smarthome/mode")
        mode = data["mode"]
        _LOGGER.debug("Get smarthome mode %s", mode)
        return mode

    async def put_smarthome_mode(self, system_id: int, mode: str) -> None:
        headers = {
            "Accept": "application/json",
            "Content-Type": "application/json;charset=UTF-8",
        }

        data = {"mode": mode}
        async with self.lock, self.throttle:
            data = await self.put(
                f"systems/{system_id}/smarthome/mode", json=data, headers=headers,
            )
        _LOGGER.debug("Set smarthome mode %s -> %s", mode, data)

    async def get_smarthome_thermostats(self, system_id: int) -> List[Thermostat]:
        async with self.lock, self.throttle:
            data = await self.get(f"systems/{system_id}/smarthome/thermostats")
        _LOGGER.debug("Get smarthome thermostats %s", data)
        return data

    async def post_smarthome_thermostats(
        self, system_id: int, thermostat: SetThermostatModel
    ) -> None:
        headers = {
            "Accept": "application/json",
            "Content-Type": "application/json;charset=UTF-8",
        }

        _LOGGER.debug("Post smarthome thermostat: %s", thermostat)
        async with self.lock, self.throttle:
            await self.post(
                f"systems/{system_id}/smarthome/thermostats", json=thermostat, headers=headers,
            )
