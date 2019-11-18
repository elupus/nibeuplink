from typing import Dict, NewType, Any, Union, Optional, List
from typing_extensions import (
    TypedDict
)

SystemId = int
Identifier = Union[str, int]
ParameterId = Identifier
Parameter = Dict[str, Any]
StatusItemIcon = Dict[str, Any]
ParameterSet = Dict[ParameterId, Parameter]
SmartHomeSystem = str


class Thermostat(TypedDict):
    smartHomeSystem: SmartHomeSystem
    name: str
    climateSystems: Optional[List[int]]
    currentTemperature: Optional[str]
    targetTemperature: Optional[str]


class SetThermostatModel(TypedDict):
    externalId: int
    name: str
    actualTemp: Optional[int] # Multiplied by 10
    targetTemp: Optional[int] # Multiplied by 10
    valvePosition: Optional[int]
    climateSystems: Optional[List[int]]
