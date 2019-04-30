from .types import (
    HotWaterSystem,
    ClimateSystem,
    VentilationSystem
)

MAX_REQUEST_PARAMETERS = 15

PARAM_HOTWATER_SYSTEMS = {
    '1': HotWaterSystem('Hot Water',
                        40014,
                        40013,
                        47041,
                        47387,
                        47050,
                        47048,
                        47044,
                        47047,
                        47043,
                        47049,
                        47045,
                        43424,
                        'hot_water_boost'),
    'DEW': HotWaterSystem('Hot Water (DEW)',
                        40077,
                        40078,
                        47041,
                        47555,
                        47050,
                        47048,
                        47044,
                        47047,
                        47043,
                        47049,
                        47045,
                        43424,
                        'hot_water_boost'),
    'SCA': HotWaterSystem('Hot Water (SCA)',
                        40077,
                        40078,
                        47041,
                        49224,
                        47050,
                        47048,
                        47044,
                        47047,
                        47043,
                        47049,
                        47045,
                        43424,
                        'hot_water_boost'),
    'AHPS': HotWaterSystem('Hot Water (AHPS)',
                        40077,
                        40078,
                        47041,
                        48641,
                        47050,
                        47048,
                        47044,
                        47047,
                        47043,
                        47049,
                        47045,
                        43424,
                        'hot_water_boost')
}

PARAM_CLIMATE_SYSTEMS = {
    #                        BT3    BT2    CSTH   OC     BT50   RSH    RSC    URS    AA     EAA    CSTC   OH     HC     MIS    MAS    HP      # noqa: 501
    '1': ClimateSystem('S1', 40012, 40008, 43009, 48739, 40033, 47398, 48785, 47394, None , 43161, 44270, 47011, 47007, 47015, 47016, None),  # noqa: 501
    '2': ClimateSystem('S2', 40129, 40007, 43008, 48738, 40032, 47397, 48784, 47393, 47302, 43160, 44269, 47010, 47006, 47014, 47017, 44746), # noqa: 501
    '3': ClimateSystem('S3', 40128, 40006, 43007, 48737, 40031, 47396, 48783, 47392, 47303, 43159, 44268, 47009, 47005, 47013, 47018, 44745), # noqa: 501
    '4': ClimateSystem('S4', 40127, 40005, 43006, 48736, 40030, 47395, 48782, 47391, 47304, 43158, 44267, 47008, 47004, 47012, 47019, 44744), # noqa: 501
}

PARAM_VENTILATION_SYSTEMS = {
    '1': VentilationSystem('Ventilation',
                           10001,
                           40025,
                           40026,
                           47265,
                           47264,
                           47263,
                           47262,
                           47261,
                           'ventilation_boost')
}

PARAM_PUMP_SPEED_HEATING_MEDIUM = 43437
PARAM_COMPRESSOR_FREQUENCY = 43136
PARAM_STATUS_COOLING = 43024

SMARTHOME_MODES = {
    0: 'DEFAULT_OPERATION',
    1: 'AWAY_FROM_HOME',
    2: 'VACATION',
}
