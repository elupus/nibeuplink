from typing import Dict, NewType, Any, Union

SystemId = int
Identifier = Union[str, int]
ParameterId = Identifier
Parameter = Dict[str, Any]
StatusItemIcon = Dict[str, Any]
ParameterSet = Dict[ParameterId, Parameter]
