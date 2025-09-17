# -*- coding: utf-8 -*-


class ColourXTerm:
    def __init__(self, colour_index: int):
        self.colour_index = colour_index & 0xFF

    def __int__(self):
        return self.colour_index
