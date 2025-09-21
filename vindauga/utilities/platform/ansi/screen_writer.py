# -*- coding: utf-8 -*-
import time

import logging

from vindauga.utilities.colours.colour_attribute import ColourAttribute
from vindauga.types.point import Point

from .attribute import TermAttribute
from .colour import TermColour
from .conversions import convert_attributes
from .termcap import TermCap
from .writers import CSI


logger = logging.getLogger(__name__)


class ScreenWriter:
    class Buffer:
        def __init__(self):
            self.__capacity = 0
            self.__data = []  # Use list of strings instead of bytearray

        def __len__(self):
            return len(self.__data)

        @property
        def data(self):
            return ''.join(self.__data)  # Join to string when accessed

        @data.setter
        def data(self, data: str):
            self.__data.clear()
            self.__data.extend(data)  # Store as single string in list

        def clear(self):
            self.__data.clear()

        def push(self, data: str):
            self.__data.append(data)  # Append string directly

        def reserve(self, capacity):
            pass

    def __init__(self, console_ctl, termcap: TermCap):
        self.__buffer = ScreenWriter.Buffer()
        self.__termcap = termcap
        self.__caret_pos: Point = Point(-1, -1)
        self.__con = console_ctl
        self.__last_attribute = TermAttribute(TermColour.default(), TermColour.default())

    def __buf_write_CSI1(self, a: int, f: str):
        self.__buffer.push(CSI)
        self.__buffer.push(str(a))
        self.__buffer.push(f)

    def __buf_write_CSI2(self, a: int, b: int, f: str):
        self.__buffer.push(CSI)
        self.__buffer.push(str(a))
        self.__buffer.push(';')
        self.__buffer.push(str(b))
        self.__buffer.push(f)

    def reset(self):
        self.__buffer.push(CSI + '0m')
        self.__caret_pos = Point(-1, -1)
        self.__last_attribute = TermAttribute(TermColour.default(), TermColour.default())

    def clear_screen(self):
        self.__buffer.push(CSI + '0m' + CSI + '2J')
        self.__last_attribute = TermAttribute(TermColour.default(), TermColour.default())

    def write_cell(self, pos, text, attribute: ColourAttribute, double_width: bool):
        if pos.y != self.__caret_pos.y:
            self.__buf_write_CSI2(pos.y + 1, pos.x + 1, 'H')
        elif pos.x != self.__caret_pos.x:
            self.__buf_write_CSI1(pos.x + 1, 'G')
            
        buf, self.__last_attribute = convert_attributes(attribute, self.__last_attribute, self.__termcap, self.__buffer.data)
        self.__buffer.data = buf  # Update buffer with new data
        self.__buffer.push(text)  # No need to encode text
        self.__caret_pos = Point(pos.x + 1 + int(double_width), pos.y)

    def set_caret_pos(self, pos):
        self.__buf_write_CSI2(pos.y + 1, pos.x + 1, 'H')
        self.__caret_pos = Point(pos.x, pos.y)

    def flush(self):
        # Buffer data is already a string, so no need to decode
        self.__con.write(self.__buffer.data)
        self.__buffer.clear()
