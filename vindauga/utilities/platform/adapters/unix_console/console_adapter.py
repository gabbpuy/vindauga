# -*- coding: utf-8 -*-
from __future__ import annotations

from typing import List

import logging
import os
import sys

import pyperclip

from vindauga.utilities.platform.display_buffer import DisplayBuffer
from vindauga.utilities.platform.adapters.console_adapter import ConsoleAdapter
from vindauga.utilities.platform.adapters.console_ctl import ConsoleCtl
from vindauga.utilities.platform.adapters.display_adapter import DisplayAdapter
from vindauga.utilities.platform.adapters.input_adapter import InputAdapter
from vindauga.utilities.platform.events.input_state import InputState
from vindauga.utilities.platform.sig_winch_handler import SigWinchHandler

logger = logging.getLogger(__name__)


class UnixConsoleAdapter(ConsoleAdapter):
    """
    Unix console implementation
    """

    @classmethod
    def create(cls, console_ctl: ConsoleCtl, display_buffer, input_state: InputState,
               display: DisplayAdapter, inputs: InputAdapter) -> UnixConsoleAdapter:
        return cls(display, inputs, console_ctl, display_buffer, input_state, SigWinchHandler.create())

    def __init__(self, display: DisplayAdapter, inputs: InputAdapter, console_ctl: ConsoleCtl,
                 display_buffer: DisplayBuffer, input_state: InputState, sigWinchHandler):
        logger.info('Initializing Unix Console Adapter')
        super().__init__(display, [inputs, sigWinchHandler])
        self.console_ctl = console_ctl
        self.display_buffer = display_buffer
        self.input_state = input_state
        self.sigWinchHandler = sigWinchHandler
        self.input = inputs
        if sigWinchHandler:
            sigWinchHandler.signal()

    def __del__(self):
        del self.sigWinchHandler
        del self.input
        del self.display
        del self.input_state

    def is_alive(self) -> bool:
        """
        Check if console is still functional
        """
        return os.isatty(sys.stdin.fileno())

    def set_clipboard_text(self, text: str) -> bool:
        """
        Set system clipboard text
        """
        try:
            pyperclip.copy(text)
            self.display_buffer.redraw_screen(self.display)
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
