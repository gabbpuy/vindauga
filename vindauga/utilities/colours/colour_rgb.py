# -*- coding: utf-8 -*-
from __future__ import annotations
import sys


class ColourRGB:
    def __init__(self, r: int, g: int, b: int):
        if sys.byteorder == 'little':
            self.rgb = (r << 16) | (g << 8) | b
        else:
            self.rgb = (b << 24) | (g << 16) | r

    @classmethod
    def from_int(cls, colour: int) -> ColourRGB:
        c = cls(0, 0, 0)
        c.rgb = colour
        return c

    @property
    def r(self):
        if sys.byteorder == 'little':
            return (self.rgb >> 16) & 0xFF
        else:
            return (self.rgb >> 8) & 0xFF

    @property
    def g(self):
        if sys.byteorder == 'little':
            return (self.rgb >> 8) & 0xFF
        else:
            return (self.rgb >> 16) & 0xFF

    @property
    def b(self):
        if sys.byteorder == 'little':
            return self.rgb & 0xFF
        else:
            return (self.rgb >> 24) & 0xFF

    def __int__(self):
        return self.rgb

    def __iter__(self):
        yield self.r
        yield self.g
        yield self.b
