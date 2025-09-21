# -*- coding: utf-8 -*-
from __future__ import annotations
import logging

from vindauga.utilities.colours.attribute_pair import AttributePair
from vindauga.utilities.colours.colour_attribute import ColourAttribute
from vindauga.utilities.screen.screen_cell import ScreenCell, set_cell, set_attr, set_char
from vindauga.utilities.text.text import Text

from .screen import Screen

logger = logging.getLogger(__name__)

LINE_WIDTH = 1024


class DrawBuffer:

    def __init__(self):
        """
        Initialize with specified width.
        """
        self.width = 8 + max(Screen.screen.screenWidth, Screen.screen.screenHeight, 80)
        self.data = [ScreenCell() for _ in range(self.width)]

    def _normalize_attribute(self, attr):
        """
        Convert int/AttributePair to ColourAttribute
        """
        if isinstance(attr, AttributePair):
            return attr.attrs[0]  # Use first (normal) attribute
        elif isinstance(attr, int):
            return ColourAttribute.from_bios(attr)
        elif attr is None:
            return None
        return attr

    def moveChar(self, indent: int, char: str, attr: ColourAttribute | AttributePair, count: int) -> int:
        """
        Fill buffer cells with a character.
        """
        actual_count = min(count, max(self.width - indent, 0))
        attr = self._normalize_attribute(attr)

        if attr:
            if char:
                for i in range(actual_count):
                    cell = ScreenCell()
                    set_cell(cell, char, attr)
                    self.data[indent + i] = cell
            else:
                # Only attr - set attributes only
                for i in range(actual_count):
                    set_attr(self.data[indent + i], attr)
        else:
            # Only char - set characters only
            for i in range(actual_count):
                set_char(self.data[indent + i], char)

        return actual_count

    def moveStr(self, indent: int, text: str, attr: ColourAttribute | AttributePair | None = None,
                maxWidth: int | None = None, strOffset: int | None = None) -> int:
        """
        Write text to buffer with attribute.

        :param indent: Indent level.
        :param text: Text to write.
        :param attr: Colour attribute.
        :param maxWidth: Maximum amount of data to be moved
        :param strOffset: Position in text where to start moving from (in text width, not bytes)

        :return: Number of cells moved
        """
        attr = self._normalize_attribute(attr)
        if maxWidth is not None:
            return Text.draw_str(self.data[:indent + maxWidth], text, indent, strOffset, attr=attr)
        else:
            return Text.draw_str(self.data, text, indent, strOffset or 0, attr=attr)

    def moveCStr(self, indent: int, text: str, attrs: AttributePair) -> int:
        """
        Write text to buffer handling C-style formatting with hotkeys.
        Handles special characters like ~ for hotkey highlighting.

        :param indent: Indent level.
        :param text: Text to write (may contain ~ formatting).
        :param attrs: AttributePair containing normal and highlight attributes.
        """
        if isinstance(attrs, AttributePair):
            low_attr, high_attr = attrs.attrs
        else:
            # Fallback - extract from BIOS value
            bios_value = attrs.as_bios()
            low_attr = ColourAttribute.from_bios(bios_value & 0xFF)
            high_attr = ColourAttribute.from_bios((bios_value >> 8) & 0xFF)

        i = indent
        j = 0
        toggle = 1
        current_attr = low_attr  # Start with low byte attribute

        while j < len(text):
            if text[j] == '~':
                # Toggle between normal and highlight attributes
                current_attr = high_attr if toggle else low_attr
                toggle = 1 - toggle
                j += 1
            else:
                # Use Text.draw_one equivalent to TText::drawOne
                success, new_i, new_j = Text.draw_one(self.data, i, text, j, current_attr)
                if not success:
                    break
                i = new_i
                j = new_j

        return i - indent

    def putAttribute(self, indent: int, attr: ColourAttribute | AttributePair, count: int = 1) -> int:
        """
        Set attribute for specified number of cells.
        """
        actual_count = min(count, max(len(self.data) - indent, 0))
        for i in range(actual_count):
            if indent + i < len(self.data):
                self.data[indent + i].attr = attr
        return actual_count

    def moveBuf(self, indent: int, source: str, attr: ColourAttribute | AttributePair, count: int) -> int:
        """
        Copy cells from source buffer.

        :param indent: Indent level.
        :param source: Source buffer.
        :param count: Number of copies.
        :param attr: Colour attribute.
        """
        return self.moveStr(indent, source[:count], attr)

    def putChar(self, indent: int, char: str, attr: ColourAttribute | AttributePair) -> int:
        """
        Put a single character with attribute.

        :param indent: Indent level.
        :param char: Character to put.
        :param attr: Colour attribute.
        """
        if indent < 0 or indent >= self.width:
            return 0

        self.data[indent].char = char
        self.data[indent].attr = attr
        return 1

    def putAttributes(self, indent: int, attr: ColourAttribute, count: int = 1) -> int:
        """
        Set attribute for specified number of cells.

        :param indent: Indent level.
        :param attr: Colour attribute.
        :param count: Number of cells.
        """
        if indent < 0 or indent >= self.width or count <= 0:
            return 0

        actual_count = min(count, self.width - indent)

        for i in range(actual_count):
            if indent + i < len(self.data):
                self.data[indent + i].attr = attr

        return actual_count

    def clear(self, attr: ColourAttribute = None):
        """
        Clear the buffer, optionally setting all cells to specified attribute.

        :param attr: Colour attribute.
        """
        for i in range(len(self.data)):
            self.data[i] = ScreenCell()
            if attr:
                self.data[i].attr = attr

    def fillChar(self, char: str, attr: ColourAttribute = None):
        """
        Fill entire buffer with specified character.

        :param char: Character to fill.
        :param attr: Colour attribute.
        """
        for i in range(len(self.data)):
            self.data[i].char = char
            if attr:
                self.data[i].attr = attr

    def toCells(self, max_width: int = None) -> list[ScreenCell]:
        """
        Return cells as a list, optionally limited to max_width.

        :param max_width: Max width.
        """
        if max_width is None:
            return self.data[:]
        return self.data[: min(max_width, len(self.data))]

    def toString(self, max_width: int = None) -> str:
        """
        Convert buffer to string representation.

        :param max_width: Max width.
        """
        end_pos = min(max_width or self.width, len(self.data))
        return ''.join(cell.char for cell in self.data[:end_pos])

    def getWidth(self, max_chars: int = None) -> int:
        """
        Get display width of buffer content.

        :param max_chars: Max width.
        """
        end_pos = min(max_chars or len(self.data), len(self.data))
        text = ''.join(cell.char for cell in self.data[:end_pos])
        return Text.width(text)

    def __getitem__(self, key):
        """
        Support for subscripting and slicing the buffer
        """
        if isinstance(key, slice):
            return self.data[key]
        elif isinstance(key, int):
            return self.data[key]
        else:
            raise TypeError("Key must be int or slice")

    def __len__(self):
        """
        Return the width of the buffer
        """
        return self.width

    def __setitem__(self, key, value):
        """
        Support for setting buffer contents via subscripting
        """
        if isinstance(key, slice):
            self.data[key] = value
        elif isinstance(key, int):
            self.data[key] = value
        else:
            raise TypeError("Key must be int or slice")

    def resize(self, new_width: int):
        """
        Resize the buffer, preserving existing content.

        :param new_width: New width.
        """
        if new_width > len(self.data):
            # Expand buffer
            self.data.extend(ScreenCell() for _ in range(new_width - len(self.data)))
        elif new_width < len(self.data):
            # Shrink buffer
            self.data = self.data[:new_width]

        self.width = new_width
