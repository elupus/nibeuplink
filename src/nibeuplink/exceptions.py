"""Exceptions used for nibeuplink"""
from typing import List, Dict, Any

ERROR_CODES = {
    -2: ('NO_CHANGE', 'Parameter value is the same as the current value.'),
    -1: ('NO_ERROR', 'Not an error, indicates success.'),
    0: ('UNKNOWN_ERROR', 'Unknown error occured.'),
    1: ('FORMAT_ERROR', 'Input format error.'),
    2: ('UNKNOWN_SYSTEM', 'Unknown system.'),
    3: ('ALREADY_CONNECTED', 'User is already connected to the system.'),
    4: ('NOT_ALLOWED_AS_SERVICE_USER', 'A service user is trying to do something he/she is not allowed to.'),
    5: ('NEEDS_RECONNECT', 'System needs a reconnect.'),
    6: ('NOT_ALLOWED_TO_RECONNECT', 'System is not allowed to be reconnected by this particular user.'),
    7: ('NOT_FOUND', 'The searched resource was not found.'),
    8: ('NOT_POSSIBLE', 'Could not accomplish the requested action.'),
    9: ('UNKNOWN_SYSTEM_UNIT', 'System unit requested was not found.'),
    10: ('UNKNOWN_HEAT_SYSTEM', 'Heat system was not found.'),
    11: ('NOT_ALLOWED_ON_SYSTEM', 'User is not allowed to do task on selected system.'),
    12: ('NO_PREMIUM_ON_SYSTEM', 'The system lacks premium subscriptions needed to access this function.'),
    13: ('TOO_MANY', 'Too many objects was requested.'),
    14: ('INVALID', 'Invalid.'),
    15: ('OUT_OF_RANGE', 'Parameter value is out of range.'),
    16: ('NOT_SETABLE', 'Parameter is not setable.'),
    17: ('NO_METADATA', 'No metadata for parameter id found.'),
    18: ('UNKNOWN_PARAMETER', 'Unknown parameter id.'),
    19: ('OAUTH_AUTHORIZATION_FAILED', 'OAuth Authorization Failed.'),
    20: ('OAUTH_INVALID_SCOPE', 'OAuth, insufficient scopes for resource.'),
    21: ('OAUTH_INVALID_ROLES', 'OAuth, user is missing role required to access resource.'),
    22: ('OAUTH_NOT_ALLOWED_CLIENT', 'OAuth, client is not allowed to access resource.'),
    23: ('UNKNOWN_CLIENT', 'Client connecting is unknown.'),
    24: ('INVALID_CLIENT_GROUP', 'Invalid client group.'),
    25: ('NOT_ALLOWED_AS_DEMO_USER', 'Not allowed as demo user.'),
    26: ('SYSTEM_OFFLINE', 'The system cannot be reached.'),
    27: ('INVALID_VOUCHER_TYPE', 'Invalid voucher type.'),
    28: ('RATE_LIMIT', 'Rate limit. Too many requests.'),
    29: ('NOT_AVAILABLE', 'Resource not available for user.'),
    30: ('INVALID_VOUCHER_SERIAL_NUMBER', 'Serial number not valid for voucher.'),
    31: ('CANT_BE_REGISTERED', 'Resource can\'t be registered.'),
    32: ('REGISTRATION_UNAVAILABLE', 'Registration is unavailable.'),
}

class UplinkException(Exception):
    pass


class UplinkResponseException(UplinkException):
    def __init__(self,
                 code: int,
                 data: Dict[str, Any]):
        self.code = code
        self.data = data
        desc = ERROR_CODES.get(code)
        if desc:
            self.message = desc[1]
            self.name = desc[0]
        else:
            self.message = 'Unknown error {}'.format(code)
            self.name = 'UNKNOWN_CODE'
        super().__init__("{}: {}\n{}".format(
            self.name,
            self.message,
            self.data))
