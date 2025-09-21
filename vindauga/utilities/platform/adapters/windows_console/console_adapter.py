# -*- coding: utf-8 -*-
from __future__ import annotations

import pyperclip

from vindauga.utilities.platform.adapters.console_adapter import ConsoleAdapter
from vindauga.utilities.platform.adapters.console_ctl import ConsoleCtl
from vindauga.utilities.platform.adapters.display_adapter import DisplayAdapter
from vindauga.utilities.platform.adapters.input_adapter import InputAdapter
from vindauga.utilities.platform.events.input_state import InputState

from .display_adapter import WindowsConsoleDisplayAdapter
from .input_adapter import WindowsConsoleInputAdapter


class WindowsConsoleAdapter(ConsoleAdapter):
    """
    Windows Console implementation
    """

    @classmethod
    def create(cls, console_ctl: ConsoleCtl, display_buffer, input_state: InputState,
               display: DisplayAdapter, inputs: InputAdapter) -> WindowsConsoleAdapter:
        sources = [inputs]
        return cls(display, sources)

    def is_alive(self) -> bool:
        """
        Check if console is still functional
        """
        return True

    def set_clipboard_text(self, text: str) -> bool:
        """
        Set system clipboard text
        """
        try:
            pyperclip.copy(text)
            return True
        except Exception:
            return False

    def request_clipboard_text(self, callback) -> bool:
        """
        Get system clipboard text
        """
        try:
            text = pyperclip.paste()
            callback(text)
            return True
        except Exception:
            return False
