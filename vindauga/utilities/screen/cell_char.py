# -*- coding: utf-8 -*-
from enum import IntFlag
from functools import singledispatchmethod
import sys


class CellFlags(IntFlag):
    NONE = 0x0
    Wide = 0x1
    Trail = 0x2


class CellChar:
    __slots__ = ('_text', '_text_length', '_flags')

    def __init__(self):
        self._text: list[str] = []
        self._text_length = 0
        self._flags = CellFlags.NONE

    def move_char(self, ch: str):
        if not ch:
            self._text = []
            self._text_length = 0
        else:
            # Store the entire string to support combining characters
            self._text = list(ch)
            self._text_length = len(ch)

    @singledispatchmethod
    def move_multi_byte_char(self, mbc: int, wide: bool = False):
        pass

    @move_multi_byte_char.register
    def _(self, mbc: str, wide: bool = False):
        if 0 < len(mbc) <= 4:
            self._flags |= -int(wide) & CellFlags.Wide
            for i in range(len(mbc)):
                self._text[i] = mbc[i]

    @move_multi_byte_char.register
    def _(self, mbc: int, wide: bool = False):
        self._text = mbc.to_bytes(4)
        self._flags = -int(wide) & CellFlags.Wide

        if sys.byteorder == 'little':
            self._textLength = 1 + (((mbc & 0xFF0000) != 0) + ((mbc & 0xFF00) != 0) + ((mbc & 0xFF) != 0))
        else:
            self._textLength = 1 + (((mbc & 0xFF00) != 0) + ((mbc & 0xFF0000) != 0) + ((mbc & 0xFF000000) != 0))

    def move_wide_char_trail(self):
        self._flags |= CellFlags.Trail
        self._text = []
        self._text_length = 0

    def is_wide(self) -> bool:
        return bool(self._flags & CellFlags.Wide)

    def is_wide_char_trail(self) -> bool:
        return bool(self._flags & CellFlags.Trail)

    def append_zero_width_char(self, mbc: str):
        sz = self.size()
        if len(mbc) < len(self._text) - sz:
            if self._text[0] == '\x00':
                self._text[0] = ' '

            for i in range(len(mbc)):
                self._text[i + sz] = mbc[i]
            self._text_length += len(mbc)

    def get_text(self) -> str:
        return ''.join(self._text[: self._text_length])

    def get_char(self) -> str:
        """
        Get the character representation of this cell.
        """
        if self._text_length == 0:
            return ' '  # Empty cell shows as space
        return self.get_text()

    def size(self) -> int:
        return max(self._text_length, 1)

    def __getitem__(self, item):
        return self._text[item]
