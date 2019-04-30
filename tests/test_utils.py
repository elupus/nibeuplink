from nibeuplink.utils import cyclic_tuple
import pytest

def test_cyclic_tuple():
    data = {
        (1, 'a'): None,
        (1, 'b'): None,
        (2, 'a'): None,
        (1, 'c'): None,
        (2, 'b'): None,
        (1, 'd'): None,
    }

    cyclic = cyclic_tuple(data.keys(), 3)
    assert next(cyclic) == (1, {'a', 'b', 'c'})
    assert next(cyclic) == (2, {'a', 'b'})
    assert next(cyclic) == (1, {'d', 'a', 'b'})
    assert next(cyclic) == (2, {'a', 'b'})


def test_cyclic_all_aligned():
    data = {
        (1, 'a'): None,
        (1, 'b'): None,
        (1, 'c'): None,
    }

    cyclic = cyclic_tuple(data.keys(), 3)
    assert next(cyclic) == (1, {'a', 'b', 'c'})
    assert next(cyclic) == (1, {'a', 'b', 'c'})

def test_cyclic_empty():
    data = {}
    cyclic = cyclic_tuple(data.keys(), 3)
    assert next(cyclic) == (None, None)
    assert next(cyclic) == (None, None)
