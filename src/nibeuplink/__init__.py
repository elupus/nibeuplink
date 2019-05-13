import asyncio
import logging
from typing import Dict

from .const import (
    MAX_REQUEST_PARAMETERS,
    PARAM_HOTWATER_SYSTEMS,
    PARAM_CLIMATE_SYSTEMS,
    PARAM_COMPRESSOR_FREQUENCY,
    PARAM_PUMP_SPEED_HEATING_MEDIUM,
    PARAM_STATUS_COOLING,
    PARAM_VENTILATION_SYSTEMS,
    SMARTHOME_MODES,
)
from .typing import StatusItemIcon
from .types import (
    Thermostat,
    SetThermostatModel,
    VentilationSystem,
    ClimateSystem,
    HotWaterSystem,
    SmartHomeSystem,
)

from .monitor import Monitor
from .uplink import Uplink

_LOGGER = logging.getLogger(__name__)

async def get_active_climate(uplink: Uplink, system_id: int) -> Dict[str, ClimateSystem]:
    active = {}
    async def check(key: str, value: ClimateSystem):
        if value.active_accessory is None:
            active[key] = value

        available = await uplink.get_parameter(
            system_id,
            value.active_accessory)

        _LOGGER.debug("Climate %s:%s active_accessory: %s", system_id, key, available)
        if available and available['rawValue'] == 1:
            active[key] = value

    await asyncio.gather(*[
        check(key, value)
        for key, value in PARAM_CLIMATE_SYSTEMS.items()
    ])

    return active


async def get_active_hotwater(uplink: Uplink, system_id: int) -> Dict[str, HotWaterSystem]:
    active = {}
    async def check(key: str, value: HotWaterSystem):
        if value.hot_water_production is None:
            active[key] = value

        available = await uplink.get_parameter(
            system_id,
            value.hot_water_production)

        _LOGGER.debug("Hotwater %s:%s hot_water_production: %s", system_id, key, available)
        if available and available['rawValue'] == 1:
            active[key] = value

    await asyncio.gather(*[
        check(key, value)
        for key, value in PARAM_HOTWATER_SYSTEMS.items()
    ])

    return active


async def get_active_ventilations(uplink: Uplink, system_id: int) -> Dict[str, VentilationSystem]:
    active = {}
    async def check(key: str, value: VentilationSystem):
        available = await uplink.get_parameter(
            system_id,
            value.fan_speed)

        _LOGGER.debug("Ventilation %s:%s fan_speed: %s", system_id, key, available)
        if available and available['rawValue'] != -32768:
            active[key] = value

    await asyncio.gather(*[
        check(key, value)
        for key, value in PARAM_VENTILATION_SYSTEMS.items()
    ])

    return active
