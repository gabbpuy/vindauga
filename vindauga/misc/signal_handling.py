# -*- coding: utf-8 -*-
import inspect
import logging
import platform
import sys
from signal import *

from .confirm_exit import confirmExit

logger = logging.getLogger('vindauga.misc.signal_handling')

PLATFORM_IS_WINDOWS = platform.system().lower() == 'windows'


oldWinchHandler = None


def sigWinchHandler():
    global oldWinchHandler
    oldWinchHandler = signal(SIGWINCH, signalHandler)


def signalHandler(signo, _frame):
    from vindauga.types.screen import Screen

    signals = [SIGINT, SIGQUIT]
    if PLATFORM_IS_WINDOWS:
        signals = [SIGINT, SIGQUIT, SIGBREAK]

    if signo == SIGCONT:
        Screen.resume()
        signal(SIGTSTP, signalHandler)
        return

    elif signo in signals:
        signal(SIGINT, SIG_IGN)
        signal(SIGQUIT, SIG_IGN)
        if PLATFORM_IS_WINDOWS:
            signal(SIGBREAK, SIG_IGN)
        if confirmExit(Screen.stdscr):
            # logger.info(inspect.getframeinfo(_frame))
            logger.info(inspect.stack())
            sys.exit(1)
        signal(SIGINT, signalHandler)
        signal(SIGQUIT, signalHandler)
        if PLATFORM_IS_WINDOWS:
            signal(SIGBREAK, signalHandler)
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
