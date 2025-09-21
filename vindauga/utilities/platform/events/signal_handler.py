# -*- coding: utf-8 -*-
from __future__ import annotations

import sys

from dataclasses import dataclass
from enum import Enum, auto
import signal
from typing import Callable


@dataclass
class HandleSignal:
    old_handler: Callable = None
    running: bool = False


class SignalHandler:
    """
    Cross-platform signal handling for terminal events.
    """

    if sys.platform != 'win32':
        handledSignals: list[int] = [signal.SIGINT, signal.SIGQUIT, signal.SIGILL,
                                     signal.SIGABRT, signal.SIGFPE, signal.SIGSEGV, signal.SIGTERM,
                                     signal.SIGTSTP]
        callback: Callable[[bool], None] = None

        oldHandlers: dict[int, HandleSignal] = {}

    @staticmethod
    def enable(callback: Callable[[bool], None] | None = None):
        """
        Enable the signal handler.
        """
        if sys.platform == 'win32':
            pass
        else:
            if not SignalHandler.callback:
                for signo in SignalHandler.handledSignals:
                    handler = signal.signal(signo, SignalHandler.handle_signal)
                    SignalHandler.oldHandlers[signo] = HandleSignal(handler)
                signal.callback = callback

    @staticmethod
    def disable():
        if sys.platform == 'win32':
            pass
        else:
            if SignalHandler.callback:
                SignalHandler.callback = None
                for signo in SignalHandler.handledSignals:
                    handler = signal.getsignal(signo)
                    if handler and handler == SignalHandler.handle_signal:
                        signal.signal(signo, SignalHandler.oldHandlers[signo].old_handler)

    @staticmethod
    def handle_signal(signum: int, _frame):
        if SignalHandler.callback and not SignalHandler.oldHandlers[signum].running:
            SignalHandler.oldHandlers[signum].running = True
            SignalHandler.callback(True)
            SignalHandler.callback(False)


def get_signal_handler() -> SignalHandler:
    """
    Get the global signal handler instance.
    """
    return SignalHandler
