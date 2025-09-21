# -*- coding: utf-8 -*-
from enum import IntEnum


class Display(IntEnum):
    smBW80 = 0x0002
    smCO80 = 0x0003
    smMono = 0x0007
    smFont8x8 = 0x0100
    smColor256 = 0x200
    smColorHigh = 0x400
    smUpdate = 0x8000
