"""Structures representing data"""
from typing import (
    Optional,
    List,
)

import attr

from .typing import (
    ParameterId
)

@attr.s
class Parameter(object):
    parameterId = attr.ib()
    name = attr.ib()
    title = attr.ib()
    designation = attr.ib()
    unit = attr.ib()
    displayValue = attr.ib()
    rawValue = attr.ib()


@attr.s
class ParameterExtended(Parameter):
    value = attr.ib()


@attr.s
class SmartHomeSystem(object):
    name = attr.ib(type=str)


@attr.s
class Thermostat(object):
    smartHomeSystem = attr.ib(type=SmartHomeSystem)
    name = attr.ib(type=str)
    climateSystems = attr.ib(default=None, type=Optional[List[int]])
    currentTemperature = attr.ib(default=None, type=Optional[str])
    targetTemperature = attr.ib(default=None, type=Optional[str])


@attr.s
class SetThermostatModel(object):
    externalId = attr.ib(type=int)
    name = attr.ib(type=str)
    actualTemp = attr.ib(default=None, type=Optional[int]) # Multiplied by 10
    targetTemp = attr.ib(default=None, type=Optional[int]) # Multiplied by 10
    valvePosition = attr.ib(default=None, type=Optional[int])
    climateSystems = attr.ib(default=None, type=Optional[List[int]])

@attr.s
class ClimateSystem(object):
    name = attr.ib(type=str)
    return_temp = attr.ib(type=ParameterId)                 # BT3
    supply_temp = attr.ib(type=ParameterId)                 # BT2
    calc_supply_temp_heat = attr.ib(type=ParameterId)       # CSTH
    offset_cool = attr.ib(type=ParameterId)                 # OC
    room_temp = attr.ib(type=ParameterId)                   # BT50
    room_setpoint_heat = attr.ib(type=ParameterId)          # RSH
    room_setpoint_cool = attr.ib(type=ParameterId)          # RSC
    use_room_sensor = attr.ib(type=ParameterId)             # URS
    active_accessory = attr.ib(type=ParameterId)            # AA
    external_adjustment_active = attr.ib(type=ParameterId)  # EAA
    calc_supply_temp_cool = attr.ib(type=ParameterId)       # CSTC
    offset_heat = attr.ib(type=ParameterId)                 # OH
    heat_curve = attr.ib(type=ParameterId)                  # HC
    min_supply = attr.ib(type=ParameterId)                  # MIS
    max_supply = attr.ib(type=ParameterId)                  # MAS
    extra_heat_pump = attr.ib(type=ParameterId)              # EHP


@attr.s
class HotWaterSystem(object):
    name = attr.ib(type=str)
    hot_water_charging = attr.ib(type=ParameterId)            # BT6
    hot_water_top = attr.ib(type=ParameterId)                 # BT7
    hot_water_comfort_mode = attr.ib(type=ParameterId)
    hot_water_production = attr.ib(type=ParameterId)          # Active or not
    periodic_hot_water = attr.ib(type=ParameterId)
    stop_temperature_water_normal = attr.ib(type=ParameterId)
    start_temperature_water_normal = attr.ib(type=ParameterId)
    stop_temperature_water_luxary = attr.ib(type=ParameterId)
    start_temperature_water_luxary = attr.ib(type=ParameterId)
    stop_temperature_water_economy = attr.ib(type=ParameterId)
    start_temperature_water_economy = attr.ib(type=ParameterId)
    total_hot_water_compressor_time = attr.ib(type=ParameterId)
    hot_water_boost = attr.ib(type=ParameterId)


@attr.s
class VentilationSystem(object):
    name = attr.ib(type=str)
    fan_speed = attr.ib(type=ParameterId)
    exhaust_air = attr.ib(type=ParameterId)  # BT20
    extract_air = attr.ib(type=ParameterId)  # BT21
    exhaust_speed_normal = attr.ib(type=ParameterId)
    exhaust_speed_1 = attr.ib(type=ParameterId)
    exhaust_speed_2 = attr.ib(type=ParameterId)
    exhaust_speed_3 = attr.ib(type=ParameterId)
    exhaust_speed_4 = attr.ib(type=ParameterId)
    ventilation_boost = attr.ib(type=ParameterId)