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


@attr.s(auto_attribs=True)
class ClimateSystem:
    name: str
    return_temp: Optional[ParameterId]  # BT3
    supply_temp: Optional[ParameterId]  # BT2
    calc_supply_temp_heat: Optional[ParameterId]  # CSTH
    offset_cool: Optional[ParameterId]  # OC
    room_temp: Optional[ParameterId]  # BT50
    room_setpoint_heat: Optional[ParameterId]  # RSH
    room_setpoint_cool: Optional[ParameterId]  # RSC
    use_room_sensor: Optional[ParameterId] # URS
    active_accessory: Optional[ParameterId]  # AA
    external_adjustment_active: Optional[ParameterId]  # EAA
    calc_supply_temp_cool: Optional[ParameterId]  # CSTC
    offset_heat: Optional[ParameterId]  # OH
    heat_curve: Optional[ParameterId]  # HC
    min_supply: Optional[ParameterId]  # MIS
    max_supply: Optional[ParameterId]  # MAS
    extra_heat_pump: Optional[ParameterId]  # EHP


@attr.s(auto_attribs=True)
class HotWaterSystem:
    name: str
    hot_water_charging: Optional[ParameterId]  # BT6
    hot_water_top: Optional[ParameterId]  # BT7
    hot_water_comfort_mode: Optional[ParameterId]
    hot_water_production: Optional[ParameterId]  # Active or not
    periodic_hot_water: Optional[ParameterId]
    stop_temperature_water_normal: Optional[ParameterId]
    start_temperature_water_normal: Optional[ParameterId]
    stop_temperature_water_luxary: Optional[ParameterId]
    start_temperature_water_luxary: Optional[ParameterId]
    stop_temperature_water_economy: Optional[ParameterId]
    start_temperature_water_economy: Optional[ParameterId]
    total_hot_water_compressor_time: Optional[ParameterId]
    hot_water_boost: Optional[ParameterId]


@attr.s(auto_attribs=True)
class VentilationSystem:
    name: str
    fan_speed: Optional[ParameterId]
    exhaust_air: Optional[ParameterId]  # BT20
    extract_air: Optional[ParameterId]  # BT21
    exhaust_speed_normal: Optional[ParameterId]
    exhaust_speed_1: Optional[ParameterId]
    exhaust_speed_2: Optional[ParameterId]
    exhaust_speed_3: Optional[ParameterId]
    exhaust_speed_4: Optional[ParameterId]
    ventilation_boost: Optional[ParameterId]
