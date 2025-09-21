# -*- coding: utf-8 -*-
from enum import IntEnum


class TerminalQuirks(IntEnum):
    NONE = 0
    BoldIsBright = 0x0001
    BlinkIsBright = 0x0002
    NoItalic = 0x0004
    NoUnderline = 0x0008
