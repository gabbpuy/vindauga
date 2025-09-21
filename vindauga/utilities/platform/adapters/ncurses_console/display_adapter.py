# -*- coding: utf-8 -*-
from __future__ import annotations

import atexit
import curses
import logging
from typing import Optional

from vindauga.utilities.singleton import Singleton
from vindauga.utilities.colours.colour_attribute import ColourAttribute
from vindauga.utilities.platform.adapters.console_ctl import ConsoleCtl
from vindauga.utilities.platform.adapters.display_adapter import DisplayAdapter
from vindauga.utilities.platform.ansi.screen_writer import ScreenWriter
from vindauga.utilities.platform.ansi.termcap import TermCap
from vindauga.types.point import Point


logger = logging.getLogger(__name__)


class NcursesDisplayAdapter(DisplayAdapter, metaclass=Singleton):
    """
    Ncurses-based display adapter providing full terminal control
    """

    def __init__(self, console_ctl: ConsoleCtl):
        self._stdscr = None
        self._initialize_ncurses()
        self._console_ctl = console_ctl
        self.ansi_screen_writer = ScreenWriter(console_ctl, TermCap.get_display_capabilities(console_ctl, self))

    @classmethod
    def create(cls, console_ctl: ConsoleCtl) -> NcursesDisplayAdapter:
        return cls(console_ctl)

    def _initialize_ncurses(self):
        try:
            self._stdscr = curses.initscr()
            if curses.has_colors():
                curses.start_color()
                curses.use_default_colors()
            else:
                pass  # Terminal does not support colors
            self._stdscr.refresh()
            atexit.register(self.cleanup)
        except Exception as e:
            logger.error("NcursesDisplayAdapter: initialization failed: %s", e)
            try:
                curses.endwin()
            except Exception:
                pass
            self._stdscr = None

    def resize(self, width: int, height: int):
        # Doesn't work in WSL (even though works for CMD/PWSH), works in MinTTY
        self._console_ctl.write(f'\x1b[8;{height};{width}t')

    def reload_screen_info(self) -> Point:
        """
        Reload screen information and return new size
        """
        size = self._console_ctl.get_size()
        curses.resize_term(size.y, size.x)
        self.ansi_screen_writer.reset()
        return size
    
    def get_colour_count(self) -> int:
        """
        Get number of supported colors
        """
        color_count = curses.COLORS if curses.has_colors() else 0
        return color_count

    def get_font_size(self) -> Point:
        """
        Get font size (estimated for terminals)
        """
        return self._console_ctl.get_font_size()
    
    def write_cell(self, pos: Point, text: str, attr: ColourAttribute, double_width: bool = False):
        """
        Write single cell using ncurses
        """
        self.ansi_screen_writer.write_cell(pos, text, attr, double_width)

    def set_caret_position(self, pos: Point):
        """
        Set cursor position
        """
        self.ansi_screen_writer.set_caret_pos(pos)

    def clear_screen(self):
        """
        Clear screen
        """
        self.ansi_screen_writer.clear_screen()

    def flush(self):
        """
        Flush output to screen
        """
        self.ansi_screen_writer.flush()

    def cleanup(self):
        """
        Cleanup curses display - restore terminal to normal state
        """
        if self._stdscr:
            try:
                # Restore cursor
                curses.curs_set(1)
                # End curses mode - this restores terminal to normal state
                curses.endwin()
            except Exception:
                logger.exception("cleanup: curses.curs_set")
            finally:
                self._stdscr = None

    def __del__(self):
        """
        Cleanup ncurses on destruction
        """
        self.cleanup()
