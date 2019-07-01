# -*- coding: utf-8 -*-
from .scroller import Scroller


class TextDevice(Scroller):
    def __init__(self, bounds, hScrollBar, vScrollBar):
        super().__init__(bounds, hScrollBar, vScrollBar)

    def do_sputn(self, s, count):
        raise NotImplementedError

