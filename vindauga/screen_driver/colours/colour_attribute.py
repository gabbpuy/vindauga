# -*- coding: utf-8 -*-
from __future__ import annotations

from functools import singledispatch
import logging

from .attribute_pair import AttributePair
from .colour_bios import ColourBIOS
from .desired_colour import DesiredColour, ColourType
from .palettes import get_bios_rgb, get_xterm256_rgb
from .style_mask import StyleMask

logger = logging.getLogger(__name__)


class ColourAttribute:
    __slots__ = ('_style', '_fg', '_bg')

    def __init__(self, bios: int | None = None):
        self._style: StyleMask = StyleMask.NONE
        self._fg: int = 0
        self._bg: int = 0

    def __repr__(self):
        return f'<ColourAttribute: fg={self._fg}, bg={self._bg}, style={self._style}>'

    @classmethod
    def from_bios(cls, bios: ColourBIOS | int) -> ColourAttribute:
        if isinstance(bios, cls):
            return bios  # Already ColourAttribute
        elif isinstance(bios, AttributePair):
            return bios.attrs[0]  # Use first (normal) attribute
        elif isinstance(bios, int):
            bios_int = bios
        else:
            bios_int = int(bios)
        attr = cls()
        attr._style = StyleMask.NONE  # BIOS format doesn't include style
        
        fg_value = bios_int & 0x0F
        bg_value = (bios_int & 0xF0) >> 4
        
        # Create DesiredColour directly from color indices (0-15)
        fg_desired = DesiredColour()
        fg_desired._data = (fg_value & 0xF) | (ColourType.BIOS << 24)
        
        bg_desired = DesiredColour()
        bg_desired._data = (bg_value & 0xF) | (ColourType.BIOS << 24)
        
        attr._fg = fg_desired.bit_cast
        attr._bg = bg_desired.bit_cast
        
        return attr

    @classmethod
    def from_colour_attribute(cls, attributes: ColourAttribute) -> ColourAttribute:
        attr = cls()
        attr._style = attributes._style
        attr._fg = attributes._fg
        attr._bg = attributes._bg
        return attr

    @classmethod
    def from_desired_colors(cls, fg: DesiredColour, bg: DesiredColour, style: int | StyleMask = 0):
        c = cls()
        c._style = StyleMask(style)
        c._fg = fg.bit_cast
        c._bg = bg.bit_cast
        return c

    def is_bios(self) -> bool:
        return get_fore(self).is_bios and get_back(self).is_bios and not get_style(self)

    def as_bios(self) -> int:
        """
        Get as BIOS attribute if possible, otherwise return default.
        """
        if not self.is_bios():
            return 0x07  # Default white on black
        return int(get_fore(self).as_bios()) | (int(get_back(self).as_bios()) << 4)

    def to_bios(self) -> int:
        """
        Convert any color attribute to BIOS format.
        """
        fg = get_fore(self)
        bg = get_back(self)
        fg_bios = int(fg.to_bios(True))
        bg_bios = int(bg.to_bios(False))
        return fg_bios | (bg_bios << 4)

    def to_rgb(self) -> tuple[DesiredColour, DesiredColour]:
        """
        Convert colors to RGB format, returning (fg, bg) tuple.
        """

        fg = get_fore(self)
        bg = get_back(self)

        # Convert foreground
        if fg.is_rgb():
            fg_rgb = fg.as_rgb()
        elif fg.is_bios():
            bios_idx = int(fg.as_bios())
            fg_rgb = get_bios_rgb(bios_idx)
        elif fg.is_xterm():
            xterm_idx = int(fg.as_xterm())
            fg_rgb = get_xterm256_rgb(xterm_idx)
        else:  # Default
            fg_rgb = get_bios_rgb(7)  # White

        # Convert background
        if bg.is_rgb():
            bg_rgb = bg.as_rgb()
        elif bg.is_bios():
            bios_idx = int(bg.as_bios())
            bg_rgb = get_bios_rgb(bios_idx)
        elif bg.is_xterm():
            xterm_idx = int(bg.as_xterm())
            bg_rgb = get_xterm256_rgb(xterm_idx)
        else:  # Default
            bg_rgb = get_bios_rgb(0)  # Black

        return DesiredColour.from_rgb(fg_rgb), DesiredColour.from_rgb(bg_rgb)

    def supports_rgb(self) -> bool:
        """
        Check if this attribute uses RGB colors.
        """
        fg = get_fore(self)
        bg = get_back(self)
        return fg.is_rgb() or bg.is_rgb()

    def __eq__(self, other: ColourAttribute | int):
        if isinstance(other, ColourAttribute):
            return self._fg == other._fg and self._bg == other._bg and self._style == other._style
        return self == ColourAttribute.from_bios(other)

    def __ior__(self, other: ColourAttribute | int):
        # It doesn't do bitwise OR, it's an assignment operation
        if isinstance(other, ColourAttribute):
            self._fg = other._fg
            self._bg = other._bg
            self._style = other._style
        else:
            # Handle integer operand - treat as BIOS color value and assign
            other_attr = ColourAttribute.from_bios(other)
            self._fg = other_attr._fg
            self._bg = other_attr._bg
            self._style = other_attr._style
        return self

    def __int__(self) -> int:
        return self.as_bios()


@singledispatch
def get_fore(attr) -> DesiredColour:
    ...


@get_fore.register(ColourAttribute)
def _get_fore(attr: ColourAttribute) -> DesiredColour:
    return DesiredColour(attr._fg)


@get_fore.register(AttributePair)
def _get_fore(attr: AttributePair) -> DesiredColour:
    return get_fore(attr.attrs[0])


@singledispatch
def get_back(attr) -> DesiredColour:
    ...


@get_back.register(ColourAttribute)
def _get_back(attr: ColourAttribute) -> DesiredColour:
    return DesiredColour(attr._bg)


@get_back.register(AttributePair)
def _get_back(attr: AttributePair) -> DesiredColour:
    return get_back(attr.attrs[0])


@singledispatch
def get_style(attr) -> StyleMask:
    ...


@get_style.register(ColourAttribute)
def _get_style(attr: ColourAttribute) -> StyleMask:
    return attr._style


@get_style.register(AttributePair)
def _get_style(attr: AttributePair) -> StyleMask:
    return get_style(attr.attrs[0])


def set_fore(attr: ColourAttribute, colour: DesiredColour):
    attr._fg = colour.bit_cast


def set_back(attr: ColourAttribute, colour: DesiredColour):
    attr._bg = colour.bit_cast


def set_style(attr: ColourAttribute, style: StyleMask | int):
    attr._style = StyleMask(style)


def reverse_attribute(attr: ColourAttribute) -> ColourAttribute:
    fg = get_fore(attr)
    bg = get_back(attr)
    if fg.is_default() or bg.is_default():
        set_style(attr, get_style(attr) ^ StyleMask.Reverse)
    else:
        set_fore(attr, bg)
        set_back(attr, fg)
    return attr
