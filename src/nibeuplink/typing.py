from typing import Dict, NewType, Any, Union

Identifier = NewType('Identifier', Union[str, int])
Parameter = NewType('Parameter', Dict[str, Any])
StatusItemIcon = NewType('StatusItemIcon', Dict[str, Any])
