# -*- coding: utf-8 -*-
from __future__ import annotations

import logging
import subprocess
from typing import Optional

import win32console

from vindauga.utilities.singleton import Singleton
from vindauga.utilities.colours.colour_attribute import ColourAttribute
from vindauga.utilities.platform.adapters.console_ctl import ConsoleCtl
from vindauga.utilities.platform.adapters.display_adapter import DisplayAdapter
from vindauga.utilities.platform.ansi.attribute import TermAttribute
from vindauga.utilities.platform.ansi.colour import TermColour
from vindauga.utilities.platform.ansi.screen_writer import ScreenWriter
from vindauga.utilities.platform.ansi.termcap import TermCap
from vindauga.types.point import Point

logger = logging.getLogger(__name__)


class ConsoleWrapper:
    """
    Console wrapper for ANSI ScreenWriter - provides write() method
    """
    def __init__(self, console_handle):
        self._console_handle = console_handle

    def write(self, data: str):
        """
        Write data to Windows console
        """
        if self._console_handle:
            try:
                self._console_handle.WriteConsole(data)
            except Exception as e:
                logger.error("ConsoleWrapper.write: %s", e)


ENABLE_VIRTUAL_TERMINAL_PROCESSING = 0x04
DISABLE_NEWLINE_AUTO_RETURN = 0x08


class WindowsConsoleDisplayAdapter(DisplayAdapter, metaclass=Singleton):
    """
    Windows Console Display adapter
    """

    @classmethod
    def create(cls, console_ctl: ConsoleCtl) -> WindowsConsoleDisplayAdapter:
        return cls(console_ctl, True)

    def __init__(self, console_ctl: ConsoleCtl, use_ansi: bool = False):
        self._console_ctl = console_ctl
        self._ansi_screen_writer = None
        self._size = Point(80, 25)  # Default size
        self._last_font_info = None
        self._caret_pos = Point(-1, -1)
        self._last_attr = 0x07  # Default white on black
        self._buffer = []
        self._console_out_handle = win32console.GetStdHandle(win32console.STD_OUTPUT_HANDLE)
        if use_ansi:
            self._ansi_screen_writer = ScreenWriter(
                self._console_ctl, TermCap.get_display_capabilities(self._console_ctl, self))

    def reload_screen_info(self):
        last_size = self._size
        self._size = self._console_ctl.get_size()

        if last_size != self._size:
            sb_info = self._console_out_handle.GetConsoleScreenBufferInfo()
            cur_pos = sb_info['CursorPosition']
            coord_zero = win32console.PyCOORDType(0, 0)
            self._console_out_handle.SetConsoleCursorPosition(coord_zero)
            coord_size = win32console.PyCOORDType(self._size.x, self._size.y)
            self._console_out_handle.SetConsoleScreenBufferSize(coord_size)
            self._console_out_handle.SetConsoleCursorPosition(cur_pos)

        font_info = self._console_out_handle.GetCurrentConsoleFont(False)
        if font_info != self._last_font_info:
            # WinWidth.reset()
            self._last_font_info = font_info

        if self._ansi_screen_writer:
            self._ansi_screen_writer.reset()
        else:
            self._caret_pos = Point(-1, -1)
            self._last_attr = 0x00
        return self._size

    def get_colour_count(self) -> int:
        """
        Windows Console color count
        """
        try:
            console_mode = self._console_out_handle.GetConsoleMode()
            if console_mode & ENABLE_VIRTUAL_TERMINAL_PROCESSING:
                return 256 * 256 * 256  # True color with VT sequences
            return 16
        except Exception:
            logger.exception("Exception while getting color count")
            return 16

    def get_font_size(self) -> Point:
        """
        Get console font size
        """
        return self._console_ctl.get_font_size()

    def write_cell(self, pos: Point, text: str, attr: ColourAttribute, double_width: bool = False):
        """
        Write cell to console at position - mirrors Win32Display::writeCell
        """

        if self._ansi_screen_writer:
            self._ansi_screen_writer.write_cell(pos, text, attr, double_width)
            return

        try:
            if pos != self._caret_pos:
                self.flush()  # Flush pending buffer first
                coord = win32console.PyCOORDType(pos.x, pos.y)
                self._console_out_handle.SetConsoleCursorPosition(coord)

            bios_attr = self._convert_to_bios_attr(attr) if attr else 0x07
            if bios_attr != self._last_attr:
                self.flush()  # Flush pending buffer first
                self._console_out_handle.SetConsoleTextAttribute(bios_attr)

            if isinstance(text, str):
                self._buffer.extend(text.encode('utf-8', errors='replace'))
            else:
                self._buffer.extend(text)

            self._caret_pos = Point(pos.x + 1 + (1 if double_width else 0), pos.y)
            self._last_attr = bios_attr

        except Exception as e:
            logger.error("WindowsConsoleDisplayAdapter.write_cell: %s", e)

    def set_caret_size(self, size: int):
        """
        Set cursor size
        """
        try:
            # SetConsoleCursorInfo expects (dwSize, bVisible) tuple
            # where dwSize is 1-100 (percentage of cell height) and bVisible is boolean
            if size:
                # Show cursor with specified size (clamp to valid range)
                cursor_size = max(1, min(100, size))
                self._console_out_handle.SetConsoleCursorInfo(cursor_size, True)
            else:
                # Hide cursor
                self._console_out_handle.SetConsoleCursorInfo(1, False)
        except Exception as e:
            logger.error("WindowsConsoleDisplayAdapter.set_caret_size: %s", e)

    def clear_screen(self):
        """
        Clear the console screen
        """
        if self._ansi_screen_writer:
            self._ansi_screen_writer.clear_screen()
            return

        try:
            coord = win32console.PyCOORDType(0, 0)
            length = self._size.x * self._size.y
            attr = 0x07  # Default white on black

            # Fill attributes
            self._console_out_handle.FillConsoleOutputAttribute(attr, length, coord)

            # Fill characters with spaces
            self._console_out_handle.FillConsoleOutputCharacter(' ', length, coord)
            self._last_attr = attr

        except Exception as e:
            logger.error("WindowsConsoleDisplayAdapter.clear_screen: %s", e)

    def flush(self):
        """
        Flush any pending output
        """
        if self._ansi_screen_writer:
            self._ansi_screen_writer.flush()
        else:
            try:
                if self._buffer:
                    # Write buffered text to console
                    text = bytes(self._buffer).decode('utf-8', errors='replace')
                    self._console_ctl.write(text)
                    self._buffer.clear()
            except Exception as e:
                logger.error("WindowsConsoleDisplayAdapter.flush: %s", e)

    def _convert_to_bios_attr(self, attr) -> int:
        """
        Convert color attribute to BIOS format for Windows Console
        """
        if not attr:
            return 0x07  # Default white on black

        try:
            if hasattr(attr, 'to_bios'):
                return attr.to_bios() & 0xFF
            elif hasattr(attr, 'toBIOS'):
                return attr.toBIOS() & 0xFF
            else:
                # Fallback: try to extract color info
                return 0x07
        except Exception:
            return 0x07

    def set_caret_position(self, pos: Point):
        """
        Set caret position
        """
        if self._ansi_screen_writer:
            self._ansi_screen_writer.set_caret_pos(pos)
            return

        try:
            self.flush()  # Flush pending buffer first
            coord = win32console.PyCOORDType(pos.x, pos.y)
            self._console_out_handle.SetConsoleCursorPosition(coord)
            self._caret_pos = pos
        except Exception as e:
            logger.error("WindowsConsoleDisplayAdapter.set_caret_position: %s", e)

    def _convert_to_term_attribute(self, attr) -> TermAttribute:
        """
        Convert Vindauga color attribute to TermAttribute for ANSI output
        """
        if not attr:
            return TermAttribute(TermColour.default(), TermColour.default())

        try:
            # Try to extract color information from the attribute
            fg = TermColour.default()
            bg = TermColour.default()

            # If attr has color extraction methods, use them
            if hasattr(attr, 'foreground') and hasattr(attr, 'background'):
                # Convert to indexed colors (basic 16-color palette)
                fg_idx = attr.foreground or 7
                bg_idx = attr.background or 0
                fg = TermColour.indexed(fg_idx & 0x0F)
                bg = TermColour.indexed(bg_idx & 0x0F)
            elif hasattr(attr, 'to_bios') or hasattr(attr, 'toBIOS'):
                # Extract from BIOS-style attribute
                bios_attr = attr.to_bios() if hasattr(attr, 'to_bios') else attr.toBIOS()
                fg = TermColour.indexed(bios_attr & 0x0F)
                bg = TermColour.indexed((bios_attr >> 4) & 0x0F)

            return TermAttribute(fg, bg)
        except Exception:
            return TermAttribute(TermColour.default(), TermColour.default())

    def resize(self, width: int, height: int):
        self._console_ctl.write(f'\x1b[8;{height};{width}t')
