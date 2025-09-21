# -*- coding: utf-8 -*-
from __future__ import annotations

from functools import cached_property

from enum import IntEnum

from .colour_bios import ColourBIOS
from .colour_rgb import ColourRGB
from .colour_xterm import ColourXTerm
from .conversions import RGB_toBIOS, XTerm16toBIOS, XTerm256toXTerm16


class ColourType(IntEnum):
    Default = 0
    BIOS = 1
    RGB = 2
    XTerm = 3


class DesiredColour:
    def __init__(self, data: int = 0):
        self._data = data

    @classmethod
    def from_bios(cls, bios: ColourBIOS):
        c = cls()
        c._data = (int(bios) & 0xF) | (ColourType.BIOS << 24)
        return c

    @classmethod
    def from_rgb(cls, rgb: ColourRGB):
        c = cls()
        c._data = (int(rgb) & 0xFFFFFF) | (ColourType.RGB << 24)
        return c

    @classmethod
    def from_xterm(cls, xterm: ColourXTerm):
        c = cls()
        c._data = int(xterm) | (ColourType.XTerm << 24)
        return c

    @cached_property
    def type(self) -> ColourType:
        # Avoid enum construction overhead by using integer comparison first
        type_int = self._data >> 24
        if type_int == 1:  # ColourType.BIOS
            return ColourType.BIOS
        elif type_int == 2:  # ColourType.RGB
            return ColourType.RGB
        elif type_int == 3:  # ColourType.XTerm
            return ColourType.XTerm
        else:  # 0 - ColourType.Default
            return ColourType.Default

    def is_default(self):
        return (self._data >> 24) == 0

    def is_bios(self):
        return (self._data >> 24) == 1

    def is_rgb(self):
        return (self._data >> 24) == 2

    def is_xterm(self):
        return (self._data >> 24) == 3

    def as_bios(self) -> ColourBIOS:
        return ColourBIOS(self._data)

    def as_rgb(self):
        return ColourRGB.from_int(self._data)

    def as_xterm(self):
        return ColourXTerm(self._data)

    def to_bios(self, is_foreground: bool) -> ColourBIOS:
        if self.type == ColourType.BIOS:
            return self.as_bios()
        elif self.type == ColourType.RGB:
            return RGB_toBIOS(self.as_rgb())
        elif self.type == ColourType.XTerm:
            idx = int(self.as_xterm())
            if idx >= 16:
                idx = XTerm256toXTerm16(idx)
            return XTerm16toBIOS(idx)
        else:
            if is_foreground:
                return ColourBIOS(0x7)
        return ColourBIOS(0x0)

    def __eq__(self, other: DesiredColour):
        return self._data == other._data

    @property
    def bit_cast(self):
        return self._data
