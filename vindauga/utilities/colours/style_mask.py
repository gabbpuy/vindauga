# -*- coding: utf-8 -*-
from __future__ import annotations

from enum import IntFlag


class StyleMask(IntFlag):
    NONE = 0
    Bold = 0x001
    Italic = 0x002
    Underline = 0x004
    Blink = 0x008
    Reverse = 0x010
    Strike = 0x20
    NoShadow = 0x200
