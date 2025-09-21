# -*- coding: utf-8 -*-
from __future__ import annotations

from .colour_rgb import ColourRGB

# Standard BIOS/RGBI 16-color palette (CGA/EGA/VGA compatible)
BIOS_PALETTE = [
    ColourRGB(0, 0, 0),  # 0: Black
    ColourRGB(128, 0, 0),  # 1: Dark Red
    ColourRGB(0, 128, 0),  # 2: Dark Green
    ColourRGB(128, 128, 0),  # 3: Dark Yellow/Brown
    ColourRGB(0, 0, 128),  # 4: Dark Blue
    ColourRGB(128, 0, 128),  # 5: Dark Magenta
    ColourRGB(0, 128, 128),  # 6: Dark Cyan
    ColourRGB(192, 192, 192),  # 7: Light Gray
    ColourRGB(128, 128, 128),  # 8: Dark Gray
    ColourRGB(255, 0, 0),  # 9: Bright Red
    ColourRGB(0, 255, 0),  # 10: Bright Green
    ColourRGB(255, 255, 0),  # 11: Bright Yellow
    ColourRGB(0, 0, 255),  # 12: Bright Blue
    ColourRGB(255, 0, 255),  # 13: Bright Magenta
    ColourRGB(0, 255, 255),  # 14: Bright Cyan
    ColourRGB(255, 255, 255),  # 15: White
]


def get_bios_rgb(index: int) -> ColourRGB:
    """
    Get RGB values for a BIOS color index (0-15).

    :param index: BIOS color index.
    """
    if 0 <= index < len(BIOS_PALETTE):
        return BIOS_PALETTE[index]
    return BIOS_PALETTE[0]  # Default to black


def get_xterm256_rgb(index: int) -> ColourRGB:
    """
    Get RGB values for an XTerm 256-color index.

    :param index: XTerm 256-color index.
    """
    if index < 16:
        # Standard BIOS colors
        return get_bios_rgb(index)
    elif index < 232:
        # 216-color 6x6x6 cube
        index -= 16
        r = index // 36
        g = (index % 36) // 6
        b = index % 6

        # Convert 0-5 to 0-255 using XTerm's formula
        def scale_component(c: int) -> int:
            return 0 if c == 0 else 55 + c * 40

        return ColourRGB(scale_component(r), scale_component(g), scale_component(b))
    else:
        # 24 grayscale colors
        gray_level = 8 + (index - 232) * 10
        return ColourRGB(gray_level, gray_level, gray_level)
