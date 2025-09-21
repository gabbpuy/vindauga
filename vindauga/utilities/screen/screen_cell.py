# -*- coding: utf-8 -*-
from __future__ import annotations
import copy

from vindauga.utilities.colours.colour_attribute import ColourAttribute
from vindauga.utilities.colours.colour_bios import ColourBIOS

from .cell_char import CellChar


class ScreenCell:
    __slots__ = ('_ch', 'attr')

    def __init__(self, bios: int | None = None):
        self._ch = CellChar()
        self.attr = ColourAttribute()
        if bios is not None:
            self._ch.move_char(chr(bios & 0xFF))
            self.attr = ColourAttribute.from_bios(ColourBIOS(bios >> 8))

    @property
    def char(self) -> str:
        """
        Get the character in this cell.
        """
        return self._ch.get_char()

    @char.setter
    def char(self, value: str):
        """
        Set the character in this cell.
        """
        self._ch.move_char(value)

    def is_wide(self) -> bool:
        return self._ch.is_wide()

    def __eq__(self, other: ScreenCell) -> bool:
        return other and self._ch == other._ch and self.attr == other.attr

    def __ne__(self, other: ScreenCell) -> bool:
        return not self.__eq__(other)

    def __getitem__(self, index: int) -> str:
        return self._ch[index]


def get_attr(cell: ScreenCell):
    """
    Get the color attribute from a screen cell.
    """
    return cell.attr


def set_attr(cell: ScreenCell, attr):
    """
    Set the color attribute of a screen cell.
    """
    cell.attr = attr


def get_char(cell: ScreenCell) -> str:
    """
    Get the character from a screen cell.
    """
    return cell.char


def set_char(cell: ScreenCell, ch: str):
    """
    Set the character in a screen cell.
    """
    cell.char = ch


def set_cell(cell: ScreenCell, ch: str, attr):
    """
    Set both character and attribute in a screen cell.
    """
    set_char(cell, ch)
    set_attr(cell, attr)
