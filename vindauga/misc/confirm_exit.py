# -*- coding: utf-8 -*-
from gettext import gettext as _
import logging

import wcwidth
from vindauga.types.draw_buffer import DrawBuffer

logger = logging.getLogger(__name__)


def confirmExit(stdscr):
    # Break current circular dependency
    from vindauga.types.screen import Screen
    b = DrawBuffer()
    msg = _('Warning: are you sure you want to quit ?')

    height, width = stdscr.getmaxyx()
    b.moveChar(0, ' ', 0x4F, width)

    b.moveStr(max((width - (wcwidth.wcswidth(msg) - 1)) // 2, 0), msg, 0x4f)
    Screen.screen.writeRow(0, 0, b._data, width)
    stdscr.timeout(-1)
    key = stdscr.getch()
    stdscr.timeout(0)
    return chr(key & 0xFF).upper() == 'Y'
