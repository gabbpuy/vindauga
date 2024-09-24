# -*- coding: utf-8 -*-
from ctypes import windll, wintypes, byref, pointer
import logging
import sys

from vindauga.types.point import Point
from vindauga.types.rect import Rect

logger = logging.getLogger(__name__)

def _change_window_title(title: str):
    windll.kernel32.SetConsoleTitleW(title)

def get_window_rect(title: str) -> Rect:
    _change_window_title(title)
    hwnd = windll.user32.FindWindowW(0, title)
    # Get the size of the entire window
    w_rect = wintypes.RECT()
    windll.user32.GetWindowRect(hwnd, pointer(w_rect))
    # Get the size of the client area. (0, 0, width, height)
    c_rect = wintypes.RECT()
    windll.user32.GetClientRect(hwnd, pointer(c_rect))
    # Convert client area to screen coords
    left_top = wintypes.POINT(c_rect.left, c_rect.top)
    right_bottom = wintypes.POINT(c_rect.right, c_rect.bottom)
    windll.user32.ClientToScreen(hwnd, pointer(left_top))
    windll.user32.ClientToScreen(hwnd, pointer(right_bottom))
    # Work out the bounds...
    left_margin = left_top.x - w_rect.left
    right_margin = w_rect.right - right_bottom.x
    # XXX: New Windows terminal draws its own title bar... lazily assume the top is 31px
    top_margin = (left_top.y - w_rect.top) or 31
    bottom_margin = w_rect.bottom - right_bottom.y
    return Rect(w_rect.left + left_margin, w_rect.top + top_margin, w_rect.right - right_margin, w_rect.bottom - bottom_margin)

def get_cursor_pos() -> Point | None:
    from vindauga.types.screen import Screen
    rect = get_window_rect(sys.argv[0])
    cursor = wintypes.POINT()
    windll.user32.GetCursorPos(byref(cursor))
    mouse_location = Point(cursor.x, cursor.y)

    if mouse_location in rect:
        sh, sw = Screen.screen.stdscr.getmaxyx()
        ww = rect.width
        wh = rect.height
        char_width = ww / sw
        char_height = wh / sh
        mouse_location.x = int((mouse_location.x - rect.topLeft.x) // char_width)
        mouse_location.y = int((mouse_location.y - rect.topLeft.y) // char_height)
        return mouse_location

    return None