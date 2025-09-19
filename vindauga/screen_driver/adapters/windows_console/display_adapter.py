# -*- coding: utf-8 -*-
import subprocess

import logging

import win32console

from vindauga.screen_driver import ColourAttribute
from vindauga.types.point import Point
from vindauga.screen_driver.adapters.display_adapter import DisplayAdapter
from vindauga.screen_driver.ansi.screen_writer import ScreenWriter
from vindauga.screen_driver.ansi.termcap import TermCap
from vindauga.screen_driver.ansi.attribute import TermAttribute
from vindauga.screen_driver.ansi.colour import TermColour

logger = logging.getLogger(__name__)


class ConsoleWrapper:
    """
    Console wrapper for ANSI ScreenWriter - provides write() method
    """

    def __init__(self, console_handle):
        self._console_handle = console_handle

    def write(self, data: str):
        """Write data to Windows console"""
        if self._console_handle:
            try:
                self._console_handle.WriteConsole(data)
            except Exception as e:
                logger.error("ConsoleWrapper.write: %s", e)


class WindowsConsoleDisplayAdapter(DisplayAdapter):
    """
    Windows Console Display adapter
    """

    def __init__(self, use_ansi: bool = False):
        self._console_out_handle = None
        self._size = Point(80, 25)  # Default size
        self._last_font_info = None
        self._ansi_screen_writer = None
        self._caret_pos = Point(-1, -1)
        self._last_attr = 0x07  # Default white on black
        self._buffer = []
        self._use_ansi = use_ansi

        try:
            self._console_out_handle = win32console.GetStdHandle(win32console.STD_OUTPUT_HANDLE)

            mode = self._console_out_handle.GetConsoleMode()
            mode &= ~win32console.ENABLE_WRAP_AT_EOL_OUTPUT  # Avoid scrolling when reaching end of line

            if use_ansi:
                mode |= getattr(win32console, 'DISABLE_NEWLINE_AUTO_RETURN', 0x8)  # Do not do CR on LF
                mode |= getattr(win32console, 'ENABLE_VIRTUAL_TERMINAL_PROCESSING', 0x4)  # Allow ANSI escape sequences

            self._console_out_handle.SetConsoleMode(mode)

            # Check if VT sequences were actually enabled
            new_mode = self._console_out_handle.GetConsoleMode()
            supports_vt = bool(new_mode & getattr(win32console, 'ENABLE_VIRTUAL_TERMINAL_PROCESSING', 0x4))

            # Initialize ANSI screen writer if VT processing is available
            if supports_vt and use_ansi:
                console_wrapper = ConsoleWrapper(self._console_out_handle)
                termcap = TermCap()
                self._ansi_screen_writer = ScreenWriter(console_wrapper, termcap)

            self.reload_screen_info()

        except Exception as e:
            logger.error("WindowsConsoleDisplayAdapter: initialization failed: %s", e)

    def reload_screen_info(self) -> Point:
        """
        Get current console screen buffer size - mirrors Win32Display::reloadScreenInfo
        """
        try:
            last_size = self._size

            # Get console screen buffer info to determine size
            csbi = self._console_out_handle.GetConsoleScreenBufferInfo()
            logger.info('Console Screen Buffer Info: %s', csbi)
            window = csbi['Window']
            self._size = Point(
                window.Right - window.Left + 1,
                window.Bottom - window.Top + 1
            )

            if last_size != self._size:
                # Size changed - set cursor to (0,0) to prevent console crash
                cur_pos = csbi['CursorPosition']
                coord_zero = win32console.PyCOORDType(0, 0)
                self._console_out_handle.SetConsoleCursorPosition(coord_zero)

                # Make sure buffer size matches viewport size
                coord_size = win32console.PyCOORDType(self._size.x, self._size.y)
                self._console_out_handle.SetConsoleScreenBufferSize(coord_size)

                # Restore cursor position
                self._console_out_handle.SetConsoleCursorPosition(cur_pos)

            # Handle font changes
            try:
                font_info = self._console_out_handle.GetCurrentConsoleFont(False)
                if font_info != self._last_font_info:
                    self._last_font_info = font_info
            except Exception:
                pass

            if self._ansi_screen_writer:
                self._ansi_screen_writer.reset()
            else:
                self._caret_pos = Point(-1, -1)
                self._last_attr = 0x07

            return self._size

        except Exception as e:
            logger.error("WindowsConsoleDisplayAdapter.reload_screen_info: %s", e)
            return Point(80, 25)

    def get_colour_count(self) -> int:
        """
        Windows Console color count - mirrors Win32Display::getColorCount
        """
        if not self._console_out_handle:
            return 16

        try:
            console_mode = self._console_out_handle.GetConsoleMode()
            if console_mode & getattr(win32console, 'ENABLE_VIRTUAL_TERMINAL_PROCESSING', 0x4):
                return 256 * 256 * 256  # True color with VT sequences
            return 16
        except Exception:
            return 16

    def get_font_size(self) -> Point:
        """
        Get console font size
        """
        return Point(8, 12)  # Typical console font size

    def write_cell(self, pos: Point, text: str, attr: ColourAttribute, double_width: bool = False):
        """
        Write cell to console at position - mirrors Win32Display::writeCell
        """
        if not self._console_out_handle:
            return

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
        if not self._console_out_handle:
            return

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
        if not self._console_out_handle:
            return

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
        if not self._console_out_handle:
            return

        if self._ansi_screen_writer:
            self._ansi_screen_writer.flush()
        else:
            try:
                if self._buffer:
                    # Write buffered text to console
                    text = bytes(self._buffer).decode('utf-8', errors='replace')
                    self._console_out_handle.WriteConsole(text)
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
        if not self._console_out_handle:
            return

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
                fg_idx = getattr(attr.foreground, 'value', 7) if attr.foreground else 7
                bg_idx = getattr(attr.background, 'value', 0) if attr.background else 0
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
        subprocess.call(['mode', 'con:', f'cols={width}', f'lines={height}'], shell=True)
        # trigger resize.. ?
