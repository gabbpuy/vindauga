# -*- coding: utf-8 -*-
import logging
import platform
import sys
import threading

import wcwidth

from vindauga.utilities.singleton import Singleton
from vindauga.types.display import Display
from vindauga.types.point import Point

from .adapters.console_adapter import ConsoleAdapter
from .adapters.console_ctl import ConsoleCtl
from .adapters.display_adapter import DisplayAdapter
from .display_buffer import DisplayBuffer
from .events.event_waiter import EventWaiter
from .events.input_state import InputState
from .events.signal_handler import SignalHandler
from vindauga.utilities.screen.screen_cell import ScreenCell

logger = logging.getLogger(__name__)


class ConsoleManager(metaclass=Singleton):
    def __init__(self):
        self.waiter = EventWaiter()
        self.display_buffer = DisplayBuffer()
        self.dummy_display = DisplayAdapter()
        self.dummy_console = ConsoleAdapter(self.dummy_display, [])
        self.console = self.dummy_console

    def __setup_console(self):
        if self.console == self.dummy_console:
            real_console = self.__create_console()
            SignalHandler.enable(self.signal_callback)
            self.console = real_console
            # CRITICAL: Update display buffer with real console's screen dimensions
            # self.display_buffer.reload_screen_info(real_console.display)
            # Add event sources to waiter
            for i, source in enumerate(real_console.sources):
                if source:
                    self.waiter.add_source(source)

    def __restore_console(self, console: ConsoleAdapter):
        if console != self.dummy_console:
            # Flush any pending screen updates
            self.display_buffer.flush_screen(console.display)
            # Remove event sources from waiter
            for source in console.sources:
                if source:
                    # EventWaiter.remove_source uses single dispatch - call with source directly
                    self.waiter.remove_source(source)
            SignalHandler.disable()
            self.console = self.dummy_console
            if platform.system().lower() == 'windows':
                ConsoleCtl.destroyInstance()

    def __check_console(self):
        with self.console.lock:
            # Check if console is still alive (mainly for Windows)
            if not self.console.is_alive():
                # Console crashed - restore and recreate (Windows scenario)
                self.__restore_console(self.console)
                self.__setup_console()

    def __create_console(self) -> ConsoleAdapter:
        """
        Create appropriate console adapter based on platform
        """
        if sys.platform == 'win32':
            # Windows: Use Win32ConsoleAdapter
            from .adapters.windows_console.display_adapter import WindowsConsoleDisplayAdapter
            from .adapters.windows_console.input_adapter import WindowsConsoleInputAdapter
            from .adapters.windows_console.console_adapter import WindowsConsoleAdapter

            con = ConsoleCtl.getInstance()
            input_state = InputState()
            display = WindowsConsoleDisplayAdapter.create(con)
            windows_input = WindowsConsoleInputAdapter(con, display, input_state, True)
            return WindowsConsoleAdapter.create(con, self.display_buffer, input_state, display, windows_input)
        else:
            from .adapters.ncurses_console.display_adapter import NcursesDisplayAdapter
            from .adapters.ncurses_console.input_adapter import NcursesInputAdapter
            from .adapters.unix_console.console_adapter import UnixConsoleAdapter
            
            con = ConsoleCtl.getInstance()
            input_state = InputState()
            display = NcursesDisplayAdapter.create(con)
            curses_input = NcursesInputAdapter(con, display, input_state, True)
            return UnixConsoleAdapter.create(con, self.display_buffer, input_state, display, curses_input)

    def __init_and_get_char_width(self, x: int):
        # Initialize encoding and return character width
        self.__init_encodings()
        return self.get_char_width(x)

    def __init_encodings(self):
        # Initialize character width calculation
        self._char_width_func = wcwidth.wcswidth

    def setup_console(self):
        with self.console.lock:
            self.__setup_console()

    def restore_console(self):
        with self.console.lock:
            self.__restore_console(self.console)

    def get_event(self, event):
        result = self.waiter.get_event(event)
        return result

    def wait_for_events(self, timeout_ms: int = -1):
        self.__check_console()

        wait_timeout_ms = timeout_ms
        # Check if display buffer has pending flush
        flush_timeout_ms = self.display_buffer.time_until_pending_flush_ms()

        if timeout_ms < 0:
            wait_timeout_ms = flush_timeout_ms
        elif flush_timeout_ms >= 0:
            wait_timeout_ms = min(timeout_ms, flush_timeout_ms)

        self.waiter.wait_for_events(wait_timeout_ms)

    def interrupt_event_wait(self):
        self.waiter.interrupt_event_wait()

    def get_caret_size(self):
        return min(max(self.display_buffer.caret_size, 1), 100)

    def is_caret_visible(self):
        return self.display_buffer.caret_size > 0

    def clear_screen(self):
        with self.console.lock:
            self.display_buffer.clear_screen(self.console.display)

    def get_screen_rows(self):
        with self.console.lock:
            return self.display_buffer.size.y

    def get_screen_cols(self):
        with self. console.lock:
            return self.display_buffer.size.x

    def set_caret_position(self, x: int, y: int):
        self.display_buffer.set_caret_position(x, y)

    def get_screen_mode(self):
        
        with self.console.lock:
            # Get color count from display adapter
            color_count = self.console.display.get_colour_count()

            if color_count == 0:
                mode = Display.smMono  # Monochrome mode
            else:
                mode = Display.smCO80

            if color_count >= 256:
                mode |= Display.smColor256

            if color_count >= 256**3:
                mode |= Display.smColorHigh

            font_size = self.console.display.get_font_size()
            if font_size.x > 0 and font_size.y > 0 and font_size.x >= font_size.y:
                mode |= Display.smFont8x8

            return mode

    def set_caret_size(self, size: int):
        self.display_buffer.set_caret_size(size)

    def screen_write(self, x: int, y: int, b: list[ScreenCell], length: int):
        with self.console.lock:
            self.display_buffer.screen_write(x, y, b, length)

    def flush_screen(self):
        with self.console.lock:
            self.display_buffer.flush_screen(self.console.display)

    def reload_screen_info(self) -> list[ScreenCell]:
        with self.console.lock:
            return self.display_buffer.reload_screen_info(self.console.display)

    def free_screen_buffer(self):
        with self.console.lock:
            self.display_buffer.free_buffer()

    def set_clipboard_text(self, text: str):
        with self.console.lock:
            self.console.set_clipboard_text(text)

    def request_clipboard_text(self) -> str:
        with self.console.lock:
            return self.console.request_clipboard_text()

    def get_char_width(self, char_code: int) -> int:
        """
        Get display width of character

        :param char_code: character code

        :return: width of character
        """
        return self.__init_and_get_char_width(char_code)

    def resize(self, width: int, height: int):
        with self.console.lock:
            self.console.resize(width, height)

    @staticmethod
    def signal_callback(enter: bool):
        instance: ConsoleManager = ConsoleManager()
        if instance and not instance.console.lock.locked():
            if enter:
                instance.restore_console()
            else:
                instance.setup_console()
