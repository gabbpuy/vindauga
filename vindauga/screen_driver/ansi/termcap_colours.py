# -*- coding: utf-8 -*-
from enum import Enum, auto


class TermCapColours(Enum):
    NoColour = auto()
    Indexed8 = auto()
    Indexed16 = auto()
    Indexed256 = auto()
    Direct = auto()
