# -*- coding: utf-8 -*-
from __future__ import annotations

import pyperclip

from vindauga.screen_driver.adapters.console_adapter import ConsoleAdapter

from .display_adapter import WindowsConsoleDisplayAdapter
from .input_adapter import WindowsConsoleInputAdapter


class WindowsConsoleAdapter(ConsoleAdapter):
    """
    Windows Console implementation
    """

    @classmethod
    def create(cls) -> WindowsConsoleAdapter:
        display = WindowsConsoleDisplayAdapter()
        input_adapter = WindowsConsoleInputAdapter()
        sources = [input_adapter]

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
