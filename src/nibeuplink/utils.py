"""Utilities for component."""
from itertools import islice


def chunks(data, SIZE):
    it = iter(data)
    for _ in range(0, len(data), SIZE):
        yield {k: data[k] for k in islice(it, SIZE)}


def chunk_pop(data, SIZE):
    count = len(data)
    if count > SIZE:
        count = SIZE

    res = data[0:count]
    del data[0:count]
    return res
