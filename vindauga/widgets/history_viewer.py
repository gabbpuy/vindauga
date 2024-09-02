# -*- coding: utf-8 -*-

import wcwidth

from vindauga.constants.command_codes import cmOK, cmCancel
from vindauga.constants.event_codes import evMouseDown, evKeyDown, evCommand, meDoubleClick
from vindauga.constants.keys import kbEnter, kbEsc, kbTab
from vindauga.events.event import Event
from vindauga.history_support.history_utils import historyCount, historyStr, getHistory
from vindauga.types.palette import Palette
from vindauga.types.rect import Rect

from .list_viewer import ListViewer
from .scroll_bar import ScrollBar


class HistoryViewer(ListViewer):
    name = 'HistoryViewer'
    cpHistoryViewer = '\x06\x06\x07\x06\x06'

    def __init__(self, bounds: Rect, hScrollBar: ScrollBar, vScrollBar: ScrollBar, historyId: int):
        super().__init__(bounds, 1, hScrollBar, vScrollBar)
        self._historyId = historyId
        self.setRange(historyCount(historyId))
        if self._range > 1:
            self.focusItem(1)
        self.hScrollBar.setRange(0, self.historyWidth() - self.size.x - 3)

    def getPalette(self) -> Palette:
        palette = Palette(self.cpHistoryViewer)
        return palette

    def getText(self, item: int, maxChars: int):
        historyString = historyStr(self._historyId, item)[:maxChars]
        return historyString or ''

    def handleEvent(self, event: Event):
        if ((event.what == evMouseDown and
             (event.mouse.eventFlags & meDoubleClick)) or
                (event.what == evKeyDown and event.keyDown.keyCode == kbEnter)):
            self.endModal(cmOK)
            self.clearEvent(event)

        # Let tab cancel too...
        elif ((event.what == evKeyDown and event.keyDown.keyCode in {kbEsc, kbTab}) or
              (event.what == evCommand and event.message.command == cmCancel)):
            self.endModal(cmCancel)
            self.clearEvent(event)
        else:
            super().handleEvent(event)

    def historyWidth(self) -> int:
        history = getHistory(self._historyId)
        if history:
            return max(wcwidth.wcswidth(h) for h in history)
        return 20
