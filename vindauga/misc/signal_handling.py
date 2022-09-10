# -*- coding: utf-8 -*-
import inspect
import logging
import platform
import sys
from signal import *

from .confirm_exit import confirmExit

logger = logging.getLogger(__name__)

PLATFORM_IS_WINDOWS = platform.system().lower() == 'windows'


oldWinchHandler = None


def sigWinchHandler():
    global oldWinchHandler
    oldWinchHandler = signal(SIGWINCH, signalHandler)


def signalHandler(signo, _frame):
    from vindauga.types.screen import Screen

    if PLATFORM_IS_WINDOWS:
        signals = [SIGINT, SIGBREAK]
    else:
        signals = [SIGINT, SIGQUIT]


    if (not PLATFORM_IS_WINDOWS) and signo == SIGCONT:
        Screen.resume()
        signal(SIGTSTP, signalHandler)
        return
    elif signo in signals:
        for ignored in signals:
            signal(ignored, SIG_IGN)
        if confirmExit(Screen.stdscr):
            # logger.info(inspect.getframeinfo(_frame))
            logger.info(inspect.stack())
            exit(1)
        for ignored in signals:
            signal(ignored, signalHandler)
        Screen.doRepaint += 1  # refresh..
        return
    elif signo == SIGTSTP:
        Screen.suspend()
        signal(SIGTSTP, SIG_DFL)
        pause()
    elif signo == SIGWINCH:
        if oldWinchHandler:
            oldWinchHandler(signo, _frame)
        Screen.doResize += 1
