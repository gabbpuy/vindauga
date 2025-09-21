# -*- coding: utf-8 -*-
from __future__ import annotations
from typing import Callable
import unicodedata

import wcwidth

from vindauga.utilities.colours.colour_attribute import ColourAttribute
from vindauga.utilities.screen.screen_cell import ScreenCell, set_cell, set_char

from .text_metrics import TextMetrics


class Text:
    """
    Provides sophisticated text handling with Unicode support and screen cell drawing.
    """
    @staticmethod
    def width(text: str) -> int:
        """
        Returns the display width of text using wcwidth.
        """
        try:
            return wcwidth.wcswidth(text) or 0
        except ImportError:
            # Fallback to simple length
            return len(text)

    @staticmethod
    def measure(text: str) -> TextMetrics:
        """
        Returns the width, character count and grapheme count of text.
        """
        width = Text.width(text)
        char_count = len(text)

        # Count graphemes (visible characters, excluding combining marks)
        grapheme_count = 0
        for char in text:
            if unicodedata.category(char) not in ('Mn', 'Mc', 'Me'):  # Not combining marks
                grapheme_count += 1

        return TextMetrics(width, char_count, grapheme_count)

    @staticmethod
    def next_char(text: str, start_index: int = 0) -> int:
        """
        Returns the length in bytes of the next character.
        """
        if start_index >= len(text):
            return 0

        # In Python, strings are Unicode, so next character is always 1 position
        # But we need to handle surrogate pairs for proper Unicode support
        char = text[start_index]
        if 0xD800 <= ord(char) <= 0xDBFF and start_index + 1 < len(text):
            # High surrogate, check for low surrogate
            next_char = text[start_index + 1]
            if 0xDC00 <= ord(next_char) <= 0xDFFF:
                return 2  # Surrogate pair
        return 1

    @staticmethod
    def next(text: str, index: int) -> tuple[bool, int]:
        """
        Advance index by one character. Returns (success, new_index).
        """
        if index >= len(text):
            return False, index

        char_len = Text.next_char(text, index)
        return True, index + char_len

    @staticmethod
    def prev(text: str, index: int) -> int:
        """
        Returns the length of the character before index.
        """
        if index <= 0 or index > len(text):
            return 0
        return Text.prev_char(text, index)

    @staticmethod
    def next_with_width(text: str, index: int) -> tuple[bool, int, int]:
        """
        Advance index and width by one character. Returns (success, new_index, width_delta).
        """
        if index >= len(text):
            return False, index, 0

        char_len = Text.next_char(text, index)
        if char_len == 0:
            return False, index, 0

        # Get width of this character
        char = text[index : index + char_len]
        char_width = Text.width(char)

        return True, index + char_len, char_width

    @staticmethod
    def prev_char(text: str, index: int) -> int:
        """
        Returns the length of the character before index.
        """
        if index <= 0 or index > len(text):
            return 0

        # Check for low surrogate (part of surrogate pair)
        if index >= 2:
            char = text[index - 1]
            if 0xDC00 <= ord(char) <= 0xDFFF:
                prev_char = text[index - 2]
                if 0xD800 <= ord(prev_char) <= 0xDBFF:
                    return 2  # Surrogate pair

        return 1

    @staticmethod
    def to_code_page(text: str) -> str:
        """
        Convert first character to current code page (simplified).
        """
        if not text:
            return '\0'

        char = text[0]
        # Try to encode to ASCII/Latin-1 for compatibility
        try:
            return char.encode('latin-1').decode('latin-1')
        except UnicodeEncodeError:
            return '?'  # Replacement character

    @staticmethod
    def scroll(text: str, count: int, include_incomplete: bool = False) -> int:
        """
        Returns the byte length of a substring that is 'count' columns wide.
        """
        if count <= 0:
            return 0

        length = 0
        width = 0
        index = 0

        while index < len(text) and width < count:
            success, new_index, char_width = Text.next_with_width(text, index)
            if not success:
                break

            if width + char_width > count and not include_incomplete:
                break  # Would exceed count, don't include this character

            length = new_index
            width += char_width
            index = new_index

            if width >= count:
                break

        return length

    @staticmethod
    def scroll_with_metrics(text: str, count: int, include_incomplete: bool = False) -> tuple[int, int]:
        """
        Returns (length, width) of substring that fits in 'count' columns.
        """
        if count <= 0:
            return 0, 0

        length = 0
        width = 0
        index = 0

        while index < len(text) and width < count:
            success, new_index, char_width = Text.next_with_width(text, index)
            if not success:
                break

            if width + char_width > count and not include_incomplete:
                break

            length = new_index
            width += char_width
            index = new_index

            if width >= count:
                break

        return length, width

    @staticmethod
    def draw_char(cells: list[ScreenCell], char: str, attr: ColourAttribute = None):
        """
        Fill cells with the given character.
        """
        if attr:
            template_cell = ScreenCell()
            set_cell(template_cell, char, attr)
            for i in range(len(cells)):
                cells[i] = template_cell
        else:
            # Just set character, preserve existing attributes
            for i in range(len(cells)):
                cells[i].char = char

    @staticmethod
    def draw_str(cells: list[ScreenCell], text: str, indent: int = 0, text_indent: int = 0,
                 attr: ColourAttribute | None = None) -> int:
        """
        Copy text into cells, starting at indent position.
        Returns number of cells filled.
        """
        if indent >= len(cells) or text_indent >= len(text):
            return 0

        # Skip to text_indent position
        text_start = Text.scroll(text, text_indent, False)
        if text_start >= len(text):
            return 0

        visible_text = text[text_start:]
        cells_span = cells[indent:]

        filled = 0
        text_pos = 0
        cell_pos = 0

        while cell_pos < len(cells_span) and text_pos < len(visible_text):
            # Use draw_one for proper combining character handling
            success, new_cell_pos, new_text_pos = Text.draw_one(
                cells_span, cell_pos, visible_text, text_pos, attr
            )
            
            if not success:
                break
                
            filled += (new_cell_pos - cell_pos) if new_cell_pos > cell_pos else 0
            cell_pos = new_cell_pos
            text_pos = new_text_pos

        return filled

    @staticmethod
    def draw_one(
        cells: list[ScreenCell], cell_index: int, text: str, text_index: int, attr: ColourAttribute = None
    ) -> tuple[bool, int, int]:
        """
        Draw one character from text into cells.
        Returns (success, new_cell_index, new_text_index).
        """
        if cell_index >= len(cells) or text_index >= len(text):
            return False, cell_index, text_index

        success, new_text_index, char_width = Text.next_with_width(text, text_index)
        if not success:
            return False, cell_index, text_index

        if cell_index + char_width > len(cells):
            return False, cell_index, text_index  # Not enough space

        char = text[text_index:new_text_index]

        # Handle combining characters
        if char_width == 0 and cell_index > 0:
            # Combining character - add to previous cell
            prev_cell = cells[cell_index - 1]
            if prev_cell.char:
                prev_cell.char += char
            return True, cell_index, new_text_index  # Don't advance cell_index

        if attr:
            set_cell(cells[cell_index], char, attr)
        else:
            set_char(cells[cell_index], char)

        # Mark continuation cells for wide characters
        for i in range(1, char_width):
            if cell_index + i < len(cells):
                cells[cell_index + i].char = ''  # Continuation
                if attr:
                    cells[cell_index + i].attr = attr

        return True, cell_index + char_width, new_text_index

    @staticmethod
    def draw_str_ex(
        cells: list[ScreenCell],
        text: str,
        indent: int = 0,
        text_indent: int = 0,
        transform_attr: Callable[[ColourAttribute], ColourAttribute] = None,
    ) -> int:
        """
        Advanced drawing with attribute transformation callback.
        """
        if indent >= len(cells) or text_indent >= len(text):
            return 0

        # Handle text indentation in the middle of wide characters
        text_start = 0
        if text_indent > 0:
            text_start, lead_width = Text.scroll_with_metrics(text, text_indent, True)
            if lead_width > text_indent and indent < len(cells):
                # We're in the middle of a wide character, draw a space
                cells[indent].char = ' '
                if transform_attr and cells[indent].attr:
                    cells[indent].attr = transform_attr(cells[indent].attr)
                indent += 1

        # Draw the rest of the text
        visible_text = text[text_start:]
        cell_pos = indent
        text_pos = 0

        while cell_pos < len(cells) and text_pos < len(visible_text):
            success, new_cell_pos, new_text_pos = Text.draw_one(cells, cell_pos, visible_text, text_pos)
            if not success:
                break

            # Apply attribute transformation
            if transform_attr:
                for i in range(cell_pos, new_cell_pos):
                    if cells[i].attr:
                        cells[i].attr = transform_attr(cells[i].attr)

            cell_pos = new_cell_pos
            text_pos = new_text_pos

        return cell_pos - indent


# Convenience functions for common operations
def measure_text(text: str) -> TextMetrics:
    """
    Convenience function to measure text.
    """
    return Text.measure(text)


def text_width(text: str) -> int:
    """
    Convenience function to get text width.
    """
    return Text.width(text)


def text_fits_width(text: str, max_width: int) -> bool:
    """
    Check if text fits within given width.
    """
    return Text.width(text) <= max_width


def truncate_text(text: str, max_width: int, ellipsis: str = '...') -> str:
    """
    Truncate text to fit within max_width, adding ellipsis if needed.
    """
    if Text.width(text) <= max_width:
        return text

    ellipsis_width = Text.width(ellipsis)
    if ellipsis_width >= max_width:
        return ellipsis[:max_width]

    target_width = max_width - ellipsis_width
    length = Text.scroll(text, target_width, False)

    return text[:length] + ellipsis
