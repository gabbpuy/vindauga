# -*- coding: utf-8 -*-
import logging

from vindauga.types.draw_buffer import DrawBuffer

logger = logging.getLogger('vindauga.misc.confirm_exit')


def confirmExit(stdscr):
    # Break current circular dependency
    from vindauga.types.screen import Screen
    b = DrawBuffer()
    msg = _('Warning: are you sure you want to quit ?')

    height, width = stdscr.getmaxyx()
    b.moveChar(0, ' ', 0x4F, width)

    b.moveStr(max((width - (len(msg) - 1)) // 2, 0), msg, 0x4f)
    Screen.writeRow(0, 0, b._data, width)
    stdscr.timeout(-1)
    key = stdscr.getch()
    stdscr.timeout(0)
    return chr(key & 0xFF).upper() == 'Y'
