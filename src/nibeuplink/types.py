"""Structures representing data"""
from typing import (
    Optional,
    List,
)

import attr

from .typing import ParameterId


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
class ClimateSystem(object):
    name = attr.ib(type=str)
    return_temp: Optional[ParameterId] = attr.ib()  # BT3
    supply_temp: Optional[ParameterId] = attr.ib()  # BT2
    calc_supply_temp_heat: Optional[ParameterId] = attr.ib()  # CSTH
    offset_cool: Optional[ParameterId] = attr.ib()  # OC
    room_temp: Optional[ParameterId] = attr.ib()  # BT50
    room_setpoint_heat: Optional[ParameterId] = attr.ib()  # RSH
    room_setpoint_cool: Optional[ParameterId] = attr.ib()  # RSC
    use_room_sensor: Optional[ParameterId] = attr.ib()  # URS
    active_accessory: Optional[ParameterId] = attr.ib()  # AA
    external_adjustment_active: Optional[ParameterId] = attr.ib()  # EAA
    calc_supply_temp_cool: Optional[ParameterId] = attr.ib()  # CSTC
    offset_heat: Optional[ParameterId] = attr.ib()  # OH
    heat_curve: Optional[ParameterId] = attr.ib()  # HC
    min_supply: Optional[ParameterId] = attr.ib()  # MIS
    max_supply: Optional[ParameterId] = attr.ib()  # MAS
    extra_heat_pump: Optional[ParameterId] = attr.ib()  # EHP


@attr.s
class HotWaterSystem(object):
    name = attr.ib(type=str)
    hot_water_charging: Optional[ParameterId] = attr.ib()  # BT6
    hot_water_top: Optional[ParameterId] = attr.ib()  # BT7
    hot_water_comfort_mode: Optional[ParameterId] = attr.ib()
    hot_water_production: Optional[ParameterId] = attr.ib()  # Active or not
    periodic_hot_water: Optional[ParameterId] = attr.ib()
    stop_temperature_water_normal: Optional[ParameterId] = attr.ib()
    start_temperature_water_normal: Optional[ParameterId] = attr.ib()
    stop_temperature_water_luxary: Optional[ParameterId] = attr.ib()
    start_temperature_water_luxary: Optional[ParameterId] = attr.ib()
    stop_temperature_water_economy: Optional[ParameterId] = attr.ib()
    start_temperature_water_economy: Optional[ParameterId] = attr.ib()
    total_hot_water_compressor_time: Optional[ParameterId] = attr.ib()
    hot_water_boost: Optional[ParameterId] = attr.ib()


@attr.s
class VentilationSystem(object):
    name = attr.ib(type=str)
    fan_speed: Optional[ParameterId] = attr.ib()
    exhaust_air: Optional[ParameterId] = attr.ib()  # BT20
    extract_air: Optional[ParameterId] = attr.ib()  # BT21
    exhaust_speed_normal: Optional[ParameterId] = attr.ib()
    exhaust_speed_1: Optional[ParameterId] = attr.ib()
    exhaust_speed_2: Optional[ParameterId] = attr.ib()
    exhaust_speed_3: Optional[ParameterId] = attr.ib()
    exhaust_speed_4: Optional[ParameterId] = attr.ib()
    ventilation_boost: Optional[ParameterId] = attr.ib()
