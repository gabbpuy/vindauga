# -*- coding: utf-8 -*-
from __future__ import annotations

from .colour_attribute import ColourAttribute
from .colour_bios import ColourBIOS
from .colour_rgb import ColourRGB
from .colour_xterm import ColourXTerm
from .conversions import RGB_toXTerm16, RGB_toXTerm256
from .desired_colour import DesiredColour
from .style_mask import StyleMask


def create_attribute(fg_colour: int | str | ColourRGB = None, bg_colour: int | str | ColourRGB = None,
                     style: int | StyleMask = StyleMask.NONE) -> ColourAttribute:
    """
    Create a ColourAttribute from various color inputs.

    :param fg_colour: foreground color
    :param bg_colour: background color
    :param style: style of colour
    :return: ColourAttribute
    """

    def _parse_colour(colour) -> DesiredColour:
        if colour is None:
            return DesiredColour()  # Default
        elif isinstance(colour, int):
            if 0 <= colour <= 15:
                return DesiredColour.from_bios(ColourBIOS(colour))
            elif 0 <= colour <= 255:
                return DesiredColour.from_xterm(ColourXTerm(colour))
            else:
                # Treat as RGB integer
                r = (colour >> 16) & 0xFF
                g = (colour >> 8) & 0xFF
                b = colour & 0xFF
                return DesiredColour.from_rgb(ColourRGB(r, g, b))
        elif isinstance(colour, str):
            # Parse hex color strings like "#FF0000" or "FF0000"
            hex_str = colour.lstrip('#')
            if len(hex_str) == 6:
                r = int(hex_str[0:2], 16)
                g = int(hex_str[2:4], 16)
                b = int(hex_str[4:6], 16)
                return DesiredColour.from_rgb(ColourRGB(r, g, b))
            else:
                raise ValueError(f'Invalid hex color format: {colour}')
        elif isinstance(colour, ColourRGB):
            return DesiredColour.from_rgb(colour)
        else:
            raise TypeError(f'Unsupported color type: {type(colour)}')

    fg = _parse_colour(fg_colour)
    bg = _parse_colour(bg_colour)

    return ColourAttribute.from_desired_colors(fg, bg, style)


def rgb_to_hex(rgb: ColourRGB) -> str:
    """
    Convert RGB color to hex string.

    :param rgb: RGB color to convert.
    """
    return f'#{rgb.r:02X}{rgb.g:02X}{rgb.b:02X}'


def hex_to_rgb(hex_str: str) -> ColourRGB:
    """
    Convert hex string to RGB color.

    :param hex_str: Hex string to convert.
    """
    hex_str = hex_str.lstrip('#')
    if len(hex_str) != 6:
        raise ValueError(f'Invalid hex color format: {hex_str}')

    r = int(hex_str[0:2], 16)
    g = int(hex_str[2:4], 16)
    b = int(hex_str[4:6], 16)
    return ColourRGB(r, g, b)


def get_colour_distance(colour1: ColourRGB, colour2: ColourRGB) -> float:
    """
    Calculate Euclidean distance between two RGB colors.

    :param colour1: RGB color to compare.
    :param colour2: RGB color to compare.
    """
    dr = colour1.r - colour2.r
    dg = colour1.g - colour2.g
    db = colour1.b - colour2.b
    return (dr * dr + dg * dg + db * db) ** 0.5


def find_best_palette_match(rgb: ColourRGB, palette_size: int = 16) -> int:
    """
    Find the best matching colour index in a palette.

    :param rgb: RGB color to compare.
    :param palette_size: Size of palette to use.
    """
    if palette_size == 16:
        return RGB_toXTerm16(rgb.r, rgb.g, rgb.b)
    elif palette_size == 256:
        return RGB_toXTerm256(rgb)
    else:
        raise ValueError(f'Unsupported palette size: {palette_size}')


def create_gradient(start_rgb: ColourRGB, end_rgb: ColourRGB, steps: int) -> list[ColourRGB]:
    """
    Create a gradient between two RGB colours.

    :param start_rgb: RGB colour to start from.
    :param end_rgb: RGB colour to end from.
    :param steps: Number of steps.
    """
    if steps < 2:
        return [start_rgb]

    gradient = []
    for i in range(steps):
        t = i / (steps - 1)  # Interpolation factor 0.0 to 1.0

        r = int(start_rgb.r * (1 - t) + end_rgb.r * t)
        g = int(start_rgb.g * (1 - t) + end_rgb.g * t)
        b = int(start_rgb.b * (1 - t) + end_rgb.b * t)

        gradient.append(ColourRGB(r, g, b))

    return gradient


def blend_colours(colour1: ColourRGB, colour2: ColourRGB, alpha: float) -> ColourRGB:
    """
    Blend two RGB colors with given alpha (0.0 = color1, 1.0 = color2).

    :param colour1: RGB color to blend.
    :param colour2: RGB color to blend.
    :param alpha: Blend alpha value.
    """
    alpha = max(0.0, min(1.0, alpha))  # Clamp to [0,1]

    r = int(colour1.r * (1 - alpha) + colour2.r * alpha)
    g = int(colour1.g * (1 - alpha) + colour2.g * alpha)
    b = int(colour1.b * (1 - alpha) + colour2.b * alpha)

    return ColourRGB(r, g, b)


# Pre-defined attribute combinations for common use cases
def make_normal() -> ColourAttribute:
    """
    Create normal text attribute (light gray on black).
    """
    return create_attribute(7, 0)  # Light gray on black


def make_reverse() -> ColourAttribute:
    """
    Create reverse video attribute (black on light gray).
    """
    return create_attribute(0, 7)  # Black on light gray


def make_highlight() -> ColourAttribute:
    """
    Create highlighted attribute (bright white on blue).
    """
    return create_attribute(15, 1)  # Bright white on blue


def make_error() -> ColourAttribute:
    """
    Create error attribute (bright red on black).
    """
    return create_attribute(12, 0)  # Bright red on black


def make_warning() -> ColourAttribute:
    """
    Create warning attribute (bright yellow on black).
    """
    return create_attribute(14, 0)  # Bright yellow on black
