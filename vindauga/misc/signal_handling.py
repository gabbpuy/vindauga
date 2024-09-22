# -*- coding: utf-8 -*-
import inspect
import logging
import platform
from signal import *
from typing import Any, Optional

from .confirm_exit import confirmExit

logger = logging.getLogger(__name__)

PLATFORM_IS_WINDOWS = platform.system().lower() == 'windows'


oldWinchHandler = Optional[Any]


def sigWinchHandler():
    global oldWinchHandler
    oldWinchHandler = signal(SIGWINCH, signalHandler)


def signalHandler(signo: int, _frame):
    from vindauga.types.screen import Screen

    if PLATFORM_IS_WINDOWS:
        signals = [SIGINT, SIGBREAK]
    else:
        signals = [SIGINT, SIGQUIT]

    screen = Screen.screen
    if (not PLATFORM_IS_WINDOWS) and signo == SIGCONT:
        screen.resume()
        signal(SIGTSTP, signalHandler)
        return
    elif signo in signals:
        for ignored in signals:
            signal(ignored, SIG_IGN)
        if confirmExit(screen.stdscr):
            # logger.info(inspect.getframeinfo(_frame))
            logger.info(inspect.stack())
            exit(1)
        for ignored in signals:
            signal(ignored, signalHandler)
        screen.doRepaint += 1  # refresh..
        return
    elif signo == SIGTSTP:
        screen.suspend()
        signal(SIGTSTP, SIG_DFL)
        pause()
    elif signo == SIGWINCH:
        if oldWinchHandler:
            oldWinchHandler(signo, _frame)
        screen.doResize += 1
