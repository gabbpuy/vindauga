# -*- coding: utf-8 -*-
from vindauga.types.rect import Rect
from .scroll_bar import ScrollBar
from .scroller import Scroller


class TextDevice(Scroller):
    def __init__(self, bounds: Rect, hScrollBar: ScrollBar, vScrollBar: ScrollBar):
        super().__init__(bounds, hScrollBar, vScrollBar)

    def do_sputn(self, s: str, count: int):
        raise NotImplementedError
