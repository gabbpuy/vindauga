# -*- coding: utf8 -*-
import itertools


def formatLine(r):
    r = list(r)
    l1 = ' '.join(f'{c:02x}' for c in r)
    l2 = ''.join(chr(c) if 32 <= c < 127 else '.' for c in r)
    return l1, l2


def hexDump(data):
    size, over = divmod(len(data), 16)
    if over:
        size += 1

    offsets = range(0, size * 16, 16)
    for o in offsets:
        row = itertools.islice(data, o, o + 16)
        yield '{:010X}: {:48} {:16}'.format(o, *formatLine(row))
