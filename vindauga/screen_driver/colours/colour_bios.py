# -*- coding: utf-8 -*-
class ColourBIOS:
    def __init__(self, bios: int):
        self.bright = (bios >> 3) & 0x1
        self.r = (bios >> 2) & 0x1
        self.g = (bios >> 1) & 0x1
        self.b = bios & 0x1

    def __int__(self):
        return (self.bright << 3) | (self.r << 2) | (self.g << 1) | self.b
