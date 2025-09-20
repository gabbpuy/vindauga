# -*- coding: utf-8 -*-
from __future__ import annotations
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .colour_attribute import ColourAttribute


class AttributePair:
    __slots__ = ('_attrs',)

    def __init__(self, bios: int | None = None, pair: tuple[ColourAttribute, ColourAttribute] | None = None):
        from .colour_attribute import ColourAttribute
        if bios is not None:
            self._attrs: tuple[ColourAttribute, ColourAttribute] = (
                ColourAttribute.from_bios(bios & 0xFF),
                ColourAttribute.from_bios((bios >> 8) & 0xFF)
            )
        elif pair is not None:
            self._attrs: tuple[ColourAttribute, ColourAttribute] = pair[:]

    def __repr__(self):
        return f'<AttributePair low={self._attrs[0]} high={self._attrs[1]}>'

    def __int__(self) -> int:
        return self.as_bios()

    def __rshift__(self, shift):
        if shift == 8:
            return self._attrs[1]
        return self.as_bios() >> shift

    def __lshift__(self, shift):
        return self.as_bios() << shift

    def __ior__(self, other: int | ColourAttribute):
        from .colour_attribute import ColourAttribute
        if isinstance(other, int):
            other = ColourAttribute.from_bios(other & 0xFF)
        self._attrs = (other, self._attrs[1])
        return self

    def __and__(self, other: int):
        """
        Bitwise AND with 0xFF returns the low attribute (first element)
        """
        if other == 0xFF:
            return self._attrs[0]
        return self.as_bios() & other

    def __getitem__(self, item):
        return self._attrs[item]

    def __eq__(self, other):
        if isinstance(other, AttributePair):
            return self._attrs[0] == other._attrs[0] and self._attrs[1] == other._attrs[1]
        elif isinstance(other, int):
            return self.as_bios() == other
        return False

    def __ne__(self, other):
        return not self.__eq__(other)

    def __bool__(self):
        """
        Support truth testing - AttributePair is True if it has non-zero attributes
        """
        return bool(self._attrs[0]) or bool(self._attrs[1])

    def __hash__(self):
        return hash((self._attrs[0], self._attrs[1]))

    def __le__(self, other):
        if isinstance(other, int):
            return int(self) <= other
        return self <= other

    def __ge__(self, other):
        if isinstance(other, int):
            return int(self) >= other
        return self >= other

    def __lt__(self, other):
        if isinstance(other, int):
            return int(self) < other
        return self < other

    def __gt__(self, other):
        if isinstance(other, int):
            return int(self) > other
        return self > other

    @property
    def attrs(self) -> tuple[ColourAttribute, ColourAttribute]:
        return self._attrs
    
    def as_colour_attribute(self):
        """
        Get first (normal) attribute as ColourAttribute for DrawBuffer compatibility
        """
        return self._attrs[0]
    
    def as_bios(self) -> int:
        return self._attrs[0].as_bios() | (self._attrs[1].as_bios() << 8)
