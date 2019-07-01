# -*- coding: utf-8 -*-
from vindauga.constants.event_codes import evKeyDown
from vindauga.constants.keys import kbTab
from vindauga.types.palette import Palette
from vindauga.types.records.data_record import DataRecord

from .editor import Editor


class MemoData:
    def __init__(self, buffer):
        self.buffer = buffer

    @property
    def length(self):
        return len(self.buffer)

    def __len__(self):
        return len(self.buffer)


class Memo(Editor):

    name = "Memo"
    cpMemo = "\x1A\x1B"

    def __init__(self, bounds, hScrollBar, vScrollBar, indicator, bufSize):
        super().__init__(bounds, hScrollBar, vScrollBar, indicator, bufSize)
        self.buffer = None

    def consumesData(self):
        return True

    def getData(self):
        rec = DataRecord()
        data = MemoData(self.buffer)
        rec.value = data
        return rec

    def setData(self, rec: MemoData):
        self.buffer = rec.buffer
        self.setBufLen(rec.length)

    def getPalette(self):
        palette = Palette(self.cpMemo)
        return palette

    def handleEvent(self, event):
        if event.what != evKeyDown or event.keyDown.keyCode != kbTab:
            super().handleEvent(event)
