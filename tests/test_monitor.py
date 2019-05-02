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
async def uplink_mock():
    uplink = asynctest.Mock(nibeuplink.Uplink('', '', ''))

    def get_parameter(system_id, parameter_id):
        return PARAMETERS[parameter_id]

    uplink.get_parameter.side_effect = get_parameter
    yield uplink

@pytest.mark.asyncio
async def test_monitor_1(uplink_mock):
    monitor = nibeuplink.Monitor(uplink_mock)

    callback_a = asynctest.Mock()
    monitor.add(1, 'a', callback_a)

    await monitor.run_once()

    callback_a.assert_called_once_with(1, {'a': PARAMETERS['a']})

@pytest.mark.asyncio
async def test_monitor_multiple_on_same_parameter(uplink_mock):
    monitor = nibeuplink.Monitor(uplink_mock)

    callback_a1 = asynctest.Mock()
    monitor.add(1, 'a', callback_a1)

    callback_a2 = asynctest.Mock()
    monitor.add(1, 'a', callback_a2)

    await monitor.run_once()

    callback_a1.assert_called_once_with(1, {'a': PARAMETERS['a']})
    callback_a2.assert_called_once_with(1, {'a': PARAMETERS['a']})

@pytest.mark.asyncio
async def test_monitor_multiple_systems(uplink_mock):
    monitor = nibeuplink.Monitor(uplink_mock)

    callback_a1 = asynctest.Mock()
    monitor.add(1, 'a', callback_a1)

    callback_b2 = asynctest.Mock()
    monitor.add(2, 'b', callback_b2)

    await monitor.run_once()

    callback_a1.assert_called_once_with(1, {'a': PARAMETERS['a']})
    callback_b2.assert_not_called()

    await monitor.run_once()
    callback_b2.assert_called_once_with(2, {'b': PARAMETERS['b']})



@pytest.mark.asyncio
async def test_monitor_removed_callback_one(uplink_mock):
    monitor = nibeuplink.Monitor(uplink_mock)

    callback_a1 = asynctest.Mock()
    monitor.add(1, 'a', callback_a1)

    callback_b2 = asynctest.Mock()
    monitor.add(2, 'b', callback_b2)

    await monitor.run_once()

    callback_a1.assert_called_once_with(1, {'a': PARAMETERS['a']})
    callback_b2.assert_not_called()

    monitor.remove(callback_b2)

    await monitor.run_once()
    callback_b2.assert_not_called()


@pytest.mark.asyncio
async def test_monitor_removed_callback_all(uplink_mock):
    monitor = nibeuplink.Monitor(uplink_mock)

    callback_a1 = asynctest.Mock()
    monitor.add(1, 'a', callback_a1)

    callback_a2 = asynctest.Mock()
    monitor.add(1, 'a', callback_a2)

    monitor.remove(callback_a1)
    monitor.remove(callback_a2)

    await monitor.run_once()

    uplink_mock.get_parameter.assert_not_called()
    callback_a1.assert_not_called()
    callback_a2.assert_not_called()
