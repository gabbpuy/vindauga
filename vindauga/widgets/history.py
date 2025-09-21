# -*- coding: utf-8 -*_
from vindauga.constants.command_codes import cmOK, cmReleasedFocus, cmRecordHistory
from vindauga.constants.event_codes import *
from vindauga.constants.keys import kbDown
from vindauga.constants.option_flags import ofPostProcess
from vindauga.constants.state_flags import sfFocused
from vindauga.events.event import Event
from vindauga.history_support.history_utils import *
from vindauga.utilities.input.key_utils import ctrlToArrow
from vindauga.types.draw_buffer import DrawBuffer
from vindauga.types.rect import Rect
from vindauga.types.palette import Palette
from vindauga.types.view import View

from .history_window import HistoryWindow
from .input_line import InputLine


class History(View):
    icon = '▐~↓~▌'
    name = 'History'
    cpHistory = '\x16\x17'

    def __init__(self, bounds: Rect, linkedWidget: InputLine, historyId: int):
        super().__init__(bounds)
        self._linkedWidget = linkedWidget
        self._historyId = historyId

        self.options |= ofPostProcess
        self.eventMask |= evBroadcast

    def shutdown(self):
        self._linkedWidget = None
        super().shutdown()

    def draw(self):
        b = DrawBuffer()
        attr_pair = self.getColor(0x0102)
        b.moveCStr(0, self.icon, attr_pair)
        self.writeLine(0, 0, self.size.x, self.size.y, b)

    def getPalette(self) -> Palette:
        palette = Palette(self.cpHistory)
        return palette

    def handleEvent(self, event: Event):
        super().handleEvent(event)

        if (event.what == evMouseDown or (event.what == evKeyDown and ctrlToArrow(event.keyDown.keyCode) == kbDown and
                                          (self._linkedWidget.state & sfFocused))):

            if not self._linkedWidget.focus():
                self.clearEvent(event)
                return

            historyRecord = self._linkedWidget.getData()
            self.recordHistory(historyRecord.value)
            r = self._linkedWidget.getBounds()
            r.topLeft.x -= 1
            r.bottomRight.x += 1
            r.bottomRight.y += 7
            r.topLeft.y -= 1

            p = self.owner.getExtent()
            r.intersect(p)
            r.bottomRight.y -= 1

            historyWindow = self.initHistoryWindow(r)
            if historyWindow:
                c = self.owner.execView(historyWindow)
                if c == cmOK:
                    result = historyWindow.getSelection()
                    self._linkedWidget.setData(result)
                    self._linkedWidget.selectAll(True)
                    self._linkedWidget.drawView()
                self.destroy(historyWindow)
            self.clearEvent(event)
        elif event.what == evBroadcast:
            if ((event.message.command == cmReleasedFocus and
                 event.message.infoPtr == self._linkedWidget) or
                    event.message.command == cmRecordHistory):
                historyRecord = self._linkedWidget.getData()
                self.recordHistory(historyRecord.value)

    def initHistoryWindow(self, bounds: Rect) -> HistoryWindow:
        p = HistoryWindow(bounds, self._historyId)
        p.helpCtx = self._linkedWidget.helpCtx
        return p

    def recordHistory(self, historyString: str):
        historyAdd(self._historyId, historyString)
