"""Utilities for component."""
from itertools import islice
from typing import Iterable, Tuple, Any, Deque
from collections import deque

def cyclic_tuple(data: Iterable[Tuple[Any, Any]],
                 step: int):
    """Chunked cyclic iterator over a data set.

    Data will be returned in chunks up to `step`
    size. First tuple iterator will be used as
    grouping of chunks, and method will peek
    ahead in iterator to find `step` values
    to return.

    If `step` values are not found before hitting
    already returned value, peeking will be stopped
    """
    pending = deque()  # type: Deque[Tuple[Any, Any]]

    def postpone(pair):
        if pair in pending:
            pending.remove(pair)

    while True:
        if pending:
            curr = pending.popleft()
        else:
            curr = (None, None)

        keep = []
        grab = {curr[1]}
        while pending:
            val = pending.popleft()
            if curr[0] == val[0]:
                if val[1] in grab:
                    keep.append(val)
                    break
                grab.add(val[1])
            else:
                keep.append(val)
            if len(grab) >= step:
                break

        pending.extendleft(reversed(keep))
        postponed = yield curr[0], grab

        if len(pending) < len(data):
            pending.extend(data)

        if postponed:
            postpone(postponed)
            yield


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
