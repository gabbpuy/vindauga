# -*- coding: utf-8 -*-
import array
import logging
from functools import partial

# The underlying datatype - 'L' gives 16 bits for unicode plus 8 for attributes / colours
BufferArray = partial(array.array, 'L')

logger = logging.getLogger('vindauga.types.draw_buffer')

# Max width of a line. This is a 1K line, that seems a reasonable width...
LINE_WIDTH = 1024


class DrawBuffer:
    """
    A buffer into which the widgets draw themselves.

    Uses `array` objects to represent the buffer with the colors and attributes set.
    """
    __slots__ = ('_data',)

    CHAR_WIDTH = 16
    ATTRIBUTE_MASK = 0xFF0000
    CHAR_MASK = 0xFFFF

    def __init__(self, filled=False):
        if not filled:
            self._data = BufferArray()
        else:
            self._data = BufferArray([0x00] * LINE_WIDTH)

    def moveBuf(self, indent: int, source, attr: int, count: int):
        if not attr:
            attrs = (c & self.ATTRIBUTE_MASK for c in self._data[indent:indent + count])
            self._data[indent:indent + count] = BufferArray(c | a for c, a in zip(source[:count], attrs))
        else:
            attr = (attr & 0xFF) << self.CHAR_WIDTH
            self._data[indent: indent + count] = BufferArray((ord(c) | attr for c in source[:count]))

    def moveChar(self, indent: int, c, attr: int, count: int):
        if attr and c:
            attr = (attr & 0xFF) << self.CHAR_WIDTH
            self._data[indent: indent + count] = BufferArray([ord(c) | attr] * count)
        elif attr:
            attr = (attr & 0xFF) << self.CHAR_WIDTH
            for i in range(indent, indent + count):
                self._data[i] = (self._data[i] & self.CHAR_MASK) | attr
        else:
            self._data[indent: indent + count] = BufferArray([ord(c)] * count)

    def moveStr(self, indent: int, strn: str, attr: int):
        if isinstance(attr, str):
            attr = ord(attr)
        attr = ((attr or 0) & 0xFF) << self.CHAR_WIDTH
        self._data[indent: indent + len(strn)] = BufferArray((ord(c) | attr for c in strn))

    def moveCStr(self, indent: int, strn: str, attrs: int):
        """
        Move a string with colors
        TODO: change attrs to a tuple

        :param indent: offset into the buffer
        :param strn: string to move
        :param attrs: 8 bit colors as a 16 bit number
        """
        # "~" highlights chunks. so break into chunks
        parts = strn.split('~')
        i = int(indent)
        attributes = [attrs & 0xFF, (attrs & 0xFF00) >> 8]
        for b, part in enumerate(parts):
            if not part:
                continue
            attr = (attributes[b % 2]) << self.CHAR_WIDTH
            pLen = len(part)
            self._data[i: i + pLen] = BufferArray((ord(c) | attr for c in part))
            i += pLen

    def putAttribute(self, indent: int, attr: int):
        self._data[indent] &= self.CHAR_MASK
        self._data[indent] |= (attr << self.CHAR_WIDTH)

    def putChar(self, indent: int, c: str):
        self._data[indent] &= self.ATTRIBUTE_MASK
        self._data[indent] |= ord(c)

    def putCharOnly(self, indent: int, c: str):
        self._data[indent] = ord(c)

    def __getitem__(self, *args):
        return self._data.__getitem__(*args)

    def __setitem__(self, *args):
        try:
            return self._data.__setitem__(*args)
        except OverflowError:
            logger.exception('Set Item Failed')
            raise

    def __setslice__(self, *args):
        return self._data.__setslice__(*args)

    def __delitem__(self, *args):
        return self._data.__delitem__(*args)

    def __len__(self) -> int:
        return len(self._data)
