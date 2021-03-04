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

SecurityLevel = Dict[str, Any]
ConnectionStatus = Dict[str, Any]
Address = Dict[str, Any]

class System(TypedDict):
    systemId: int
    name: str
    productName: str
    productImage: str
    securityLevel: SecurityLevel
    serialNumber: str
    lastActivityDate: str
    connectionStatus: ConnectionStatus
    address: Optional[Address]
    hasAlarmed: bool

class SystemUnit(TypedDict):
    systemUnitId: int
    name: str
    shortName: str
    product: str
    softwareVersion: str

class SmartHomeSystem(TypedDict):
    name: str


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

class ParameterType(TypedDict, total=False):
    parameterId: int
    Name: str
    title: str
    designation: str
    unit: str
    displayValue: str
    rawValue: int

    ## Extension by library
    value: Union[str, float, None]

class CategoryType(TypedDict, total=False):
    categoryId: int
    name: str
    parameters: List[ParameterType]