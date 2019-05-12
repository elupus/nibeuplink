import pytest
import nibeuplink
import asyncio
import asynctest

PARAMETERS = {
    'a': {'name': 'a'},
    'b': {'name': 'b'},
    'c': {'name': 'c'},
}

@pytest.fixture
@pytest.mark.asyncio
async def uplink_mock(loop):
    uplink = asynctest.Mock(nibeuplink.Uplink('', '', ''))

    def get_parameter(system_id, parameter_id):
        return PARAMETERS[parameter_id]

    uplink.get_parameter.side_effect = get_parameter
    return uplink

@pytest.mark.asyncio
async def test_monitor_1(uplink_mock):
    monitor = nibeuplink.Monitor(uplink_mock)

    callback_a = asynctest.Mock()
    monitor.add_callback(callback_a)
    monitor.add(1, 'a')

    await monitor.run_once()

    callback_a.assert_called_once_with(1, {'a': PARAMETERS['a']})

@pytest.mark.asyncio
async def test_monitor_multiple_systems(uplink_mock):
    monitor = nibeuplink.Monitor(uplink_mock)

    callback = asynctest.Mock()
    monitor.add_callback(callback)

    monitor.add(1, 'a')
    monitor.add(2, 'b')

    await monitor.run_once()
    await monitor.run_once()

    callback.assert_any_call(1, {'a': PARAMETERS['a']})
    callback.assert_any_call(2, {'b': PARAMETERS['b']})



@pytest.mark.asyncio
async def test_monitor_removed_callback_one(uplink_mock):
    monitor = nibeuplink.Monitor(uplink_mock)

    callback_a1 = asynctest.Mock()
    callback_b2 = asynctest.Mock()
    monitor.add_callback(callback_a1)
    monitor.add_callback(callback_b2)

    monitor.add(1, 'a')
    monitor.add(2, 'b')

    await monitor.run_once()

    callback_a1.assert_called_once_with(1, {'a': PARAMETERS['a']})
    callback_b2.assert_called_once_with(1, {'a': PARAMETERS['a']})

    monitor.del_callback(callback_b2)
    callback_a1.reset_mock()
    callback_b2.reset_mock()

    await monitor.run_once()
    callback_a1.assert_called_once_with(2, {'b': PARAMETERS['b']})
    callback_b2.assert_not_called()


@pytest.mark.asyncio
async def test_monitor_removed_callback_all(uplink_mock):
    monitor = nibeuplink.Monitor(uplink_mock)

    callback_a1 = asynctest.Mock()
    callback_a2 = asynctest.Mock()
    monitor.add_callback(callback_a1)
    monitor.add_callback(callback_a2)

    monitor.add(1, 'a')
    monitor.remove(1, 'a')

    monitor.del_callback(callback_a1)
    monitor.del_callback(callback_a2)

    await monitor.run_once()

    uplink_mock.get_parameter.assert_not_called()
    callback_a1.assert_not_called()
    callback_a2.assert_not_called()
