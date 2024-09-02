# -*- coding: utf-8 -*-
from dataclasses import dataclass

import wcwidth

from vindauga.constants.event_codes import evKeyDown
from vindauga.constants.keys import kbTab
from vindauga.events.event import Event
from vindauga.types.draw_buffer import BufferArray
from vindauga.types.palette import Palette
from vindauga.types.records.data_record import DataRecord

from .editor import Editor


@dataclass
class MemoData:
    buffer: str = ''

    @property
    def length(self):
        return wcwidth.wcswidth(self.buffer)

    def __len__(self):
        return wcwidth.wcswidth(self.buffer)


class Memo(Editor):

    name = "Memo"
    cpMemo = "\x1A\x1B"

    def consumesData(self) -> bool:
        return True

    def getData(self) -> DataRecord:
        rec = DataRecord()
        data = MemoData(''.join(chr(c) for c in self.buffer))
        rec.value = data
        return rec

    def setData(self, rec: MemoData):
        self.buffer = BufferArray(ord(c) for c in rec.buffer)
        self.setBufLen(rec.length)

    def getPalette(self) -> Palette:
        palette = Palette(self.cpMemo)
        return palette

    def handleEvent(self, event: Event):
        if event.what != evKeyDown or event.keyDown.keyCode != kbTab:
            super().handleEvent(event)
