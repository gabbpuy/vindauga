# -*- coding: utf-8 -*-
from vindauga.constants.command_codes import wnNoNumber
from vindauga.constants.scrollbar_codes import sbHorizontal, sbVertical, sbHandleKeyboard
from vindauga.constants.window_flags import wfClose
from vindauga.types.palette import Palette
from vindauga.types.rect import Rect

from .history_viewer import HistoryViewer
from .window import Window


class HistoryWindow(Window):

    cpHistoryWindow = "\x13\x13\x15\x18\x17\x13\x14"

    def __init__(self, bounds: Rect, historyId: int):
        super().__init__(bounds, '', wnNoNumber)
        self.flags |= wfClose
        self._viewer = self.initViewer(self.getExtent(), self, historyId)
        if self._viewer:
            self.insert(self._viewer)

    def getPalette(self) -> Palette:
        palette = Palette(self.cpHistoryWindow)
        return palette

    def getSelection(self) -> str:
        return self._viewer.getText(self._viewer.focused, 255)

    @staticmethod
    def initViewer(r: Rect, win: Window, historyId: int) -> HistoryViewer:
        r.grow(-1, -1)
        return HistoryViewer(r, win.standardScrollBar(sbHorizontal | sbHandleKeyboard),
                             win.standardScrollBar(sbVertical | sbHandleKeyboard), historyId)
