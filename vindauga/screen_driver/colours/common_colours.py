# -*- coding: utf-8 -*-
from __future__ import annotations

from .colour_rgb import ColourRGB


class CommonColours:
    BLACK = ColourRGB(0, 0, 0)
    WHITE = ColourRGB(255, 255, 255)
    RED = ColourRGB(255, 0, 0)
    GREEN = ColourRGB(0, 255, 0)
    BLUE = ColourRGB(0, 0, 255)
    YELLOW = ColourRGB(255, 255, 0)
    CYAN = ColourRGB(0, 255, 255)
    MAGENTA = ColourRGB(255, 0, 255)
    GRAY = ColourRGB(128, 128, 128)
    DARK_GRAY = ColourRGB(64, 64, 64)
    LIGHT_GRAY = ColourRGB(192, 192, 192)
