# -*- coding: utf-8 -*-
from __future__ import annotations


class ColourXTerm:
    def __init__(self, colour_index: int):
        self.colour_index = colour_index & 0xFF

    def __int__(self):
        return self.colour_index

    def __eq__(self, other: ColourXTerm | int):
        if isinstance(other, ColourXTerm):
            return self.colour_index == other.colour_index
        return self.colour_index == other

    def __lt__(self, other: ColourXTerm | int):
        if isinstance(other, ColourXTerm):
            return self.colour_index < other.colour_index
        return self.colour_index < other

    def __gt__(self, other: ColourXTerm | int):
        if isinstance(other, ColourXTerm):
            return self.colour_index > other.colour_index
        return self.colour_index > other

    def __le__(self, other: ColourXTerm | int):
        if isinstance(other, ColourXTerm):
            return self.colour_index <= other.colour_index
        return self.colour_index <= other

    def __ge__(self, other: ColourXTerm | int):
        if isinstance(other, ColourXTerm):
            return self.colour_index >= other.colour_index
        return self.colour_index >= other
