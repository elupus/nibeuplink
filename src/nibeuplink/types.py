"""Structures representing data"""
from typing import (
    Optional,
    List,
)

import attr

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
    name = attr.ib()
    return_temp = attr.ib()                 # BT3
    supply_temp = attr.ib()                 # BT2
    calc_supply_temp_heat = attr.ib()       # CSTH
    offset_cool = attr.ib()                 # OC
    room_temp = attr.ib()                   # BT50
    room_setpoint_heat = attr.ib()          # RSH
    room_setpoint_cool = attr.ib()          # RSC
    use_room_sensor = attr.ib()             # URS
    active_accessory = attr.ib()            # AA
    external_adjustment_active = attr.ib()  # EAA
    calc_supply_temp_cool = attr.ib()       # CSTC
    offset_heat = attr.ib()                 # OH
    heat_curve = attr.ib()                  # HC
    min_supply = attr.ib()                  # MIS
    max_supply = attr.ib()                  # MAS
    extra_heat_pump = attr.ib()              # EHP


@attr.s
class HotWaterSystem(object):
    name = attr.ib()
    hot_water_charging = attr.ib()            # BT6
    hot_water_top = attr.ib()                 # BT7
    hot_water_comfort_mode = attr.ib()
    hot_water_production = attr.ib()          # Active or not
    periodic_hot_water = attr.ib()
    stop_temperature_water_normal = attr.ib()
    start_temperature_water_normal = attr.ib()
    stop_temperature_water_luxary = attr.ib()
    start_temperature_water_luxary = attr.ib()
    stop_temperature_water_economy = attr.ib()
    start_temperature_water_economy = attr.ib()
    total_hot_water_compressor_time = attr.ib()
    hot_water_boost = attr.ib()


@attr.s
class VentilationSystem(object):
    name = attr.ib()
    fan_speed = attr.ib()
    exhaust_air = attr.ib()  # BT20
    extract_air = attr.ib()  # BT21
    exhaust_speed_normal = attr.ib()
    exhaust_speed_1 = attr.ib()
    exhaust_speed_2 = attr.ib()
    exhaust_speed_3 = attr.ib()
    exhaust_speed_4 = attr.ib()
    ventilation_boost = attr.ib()