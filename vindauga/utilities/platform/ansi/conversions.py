# -*- coding: utf-8 -*-
import logging
from typing import Callable

from vindauga.utilities.colours.colour_attribute import ColourAttribute, get_style, get_fore, get_back
from vindauga.utilities.colours.conversions import BIOS_to_XTerm16, XTerm256toXTerm16, RGB_toXTerm16
from vindauga.utilities.colours.style_mask import StyleMask
from vindauga.utilities.colours.desired_colour import DesiredColour

from .attribute import TermAttribute
from .colour import TermColour, TermColourTypes
from .quirks import TerminalQuirks
from .termcap import TermCap
from .termcap_colours import TermCapColours
from .writers import write_attributes

logger = logging.getLogger(__name__)

# Pre-compute common enum values as integers to avoid enum operations
_STYLE_ITALIC = int(StyleMask.Italic)
_STYLE_UNDERLINE = int(StyleMask.Underline)


class ColourConversionReturn:
    def __init__(self, colour: TermColour, extra_flags: StyleMask = StyleMask.NONE):
        self.colour: TermColour = colour
        self.extra_style = extra_flags

    def __int__(self):
        val: int = int(self.colour) | int(self.extra_style) << 32
        return val


def convert_no_color(colour: DesiredColour, termcap: TermCap, is_fg: bool) -> ColourConversionReturn:
    cnv = ColourConversionReturn(TermColour(TermColourTypes.NoColor))
    if colour.is_bios():
        bios = int(colour.as_bios())
        if is_fg:
            if bios & 0x8:
                cnv.extra_style |= StyleMask.Bold
            elif bios == 0x1:
                cnv.extra_style |= StyleMask.Underline
        elif (bios & 0x7) == 0x7:
            cnv.extra_style |= StyleMask.Reverse
    return cnv


def convert_indexed16(colour: DesiredColour, termcap: TermCap, is_fg: bool) -> ColourConversionReturn:
    if colour.is_bios():
        idx = BIOS_to_XTerm16(colour.as_bios())
        return ColourConversionReturn(TermColour(TermColourTypes.Indexed, idx))
    elif colour.is_xterm():
        idx = colour.as_xterm()
        if idx >= 16:
            idx = XTerm256toXTerm16(idx)
        return ColourConversionReturn(TermColour(TermColourTypes.Indexed, idx))
    elif colour.is_rgb():
        idx = RGB_toXTerm16(*tuple(colour.as_rgb()))
        return ColourConversionReturn(TermColour(TermColourTypes.Indexed, idx))
    return ColourConversionReturn(TermColour.default())


def convert_indexed8(colour: DesiredColour, termcap: TermCap, is_fg: bool) -> ColourConversionReturn:
    cnv: ColourConversionReturn = convert_indexed16(colour, termcap, is_fg)
    if cnv.colour.type == TermColourTypes.Indexed and cnv.colour.idx >= 8:
        cnv.colour.idx -= 8
        if is_fg:
            if termcap.quirks & TerminalQuirks.BoldIsBright:
                cnv.extra_style |= StyleMask.Bold
            elif termcap.quirks & TerminalQuirks.BlinkIsBright:
                cnv.extra_style |= StyleMask.Blink
    return cnv


def convert_indexed256(colour: DesiredColour, termcap: TermCap, is_fg: bool) -> ColourConversionReturn:
    if colour.is_xterm():
        idx = int(colour.as_xterm())
        return ColourConversionReturn(TermColour(TermColourTypes.Indexed, idx))
    elif colour.is_rgb():
        idx = RGB_toXTerm16(*tuple(colour.as_rgb()))
        return ColourConversionReturn(TermColour(TermColourTypes.Indexed, idx))
    return convert_indexed16(colour, termcap, is_fg)


def convert_direct(colour: DesiredColour, termcap: TermCap, is_fg: bool) -> ColourConversionReturn:
    if colour.is_rgb():
        rgb = colour.as_rgb()
        return ColourConversionReturn(TermColour(TermColourTypes.RGB, rgb))
    return convert_indexed256(colour, termcap, is_fg)


colour_converters: dict[TermCapColours, Callable[[DesiredColour, TermCap, bool], ColourConversionReturn]] = {
    TermCapColours.NoColour: convert_no_color,
    TermCapColours.Indexed8: convert_indexed8,
    TermCapColours.Indexed16: convert_indexed16,
    TermCapColours.Indexed256: convert_indexed256,
    TermCapColours.Direct: convert_direct,
}


def convert_colour(colour: DesiredColour,
                   termcap: TermCap, is_fg: bool) -> tuple[TermColour, StyleMask]:
    cnv = colour_converters[termcap.colours](colour, termcap, is_fg)
    return cnv.colour, cnv.extra_style


def convert_attributes(attribute: ColourAttribute, last_attribute: TermAttribute, termcap: TermCap,
                       buf: str) -> tuple[str, TermAttribute]:
    attr = TermAttribute()
    if isinstance(attribute, int):
        attribute = ColourAttribute.from_bios(attribute)

    # Use integer operations instead of enum operations for performance
    style_int = int(get_style(attribute))
    attr.style = StyleMask(style_int)

    fg_desired = get_fore(attribute)
    bg_desired = get_back(attribute)

    fg, style = convert_colour(fg_desired, termcap, True)
    attr.fg = fg
    style_int |= int(style)

    bg, style = convert_colour(bg_desired, termcap, False)
    attr.bg = bg
    style_int |= int(style)

    # Use integer operations for quirks handling
    quirks_int = int(termcap.quirks)
    if quirks_int & int(TerminalQuirks.NoItalic):
        style_int &= ~_STYLE_ITALIC
    if quirks_int & int(TerminalQuirks.NoUnderline):
        style_int &= ~_STYLE_UNDERLINE

    attr.style = StyleMask(style_int)

    buf += write_attributes(attr, last_attribute)

    return buf, attr
