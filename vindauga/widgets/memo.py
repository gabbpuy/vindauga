# -*- coding: utf-8 -*-
from dataclasses import dataclass

import wcwidth

from vindauga.constants.event_codes import evKeyDown
from vindauga.constants.keys import kbTab
from vindauga.events.event import Event
# BufferArray no longer needed - using strings for buffers now
from vindauga.types.palette import Palette
from vindauga.types.records.data_record import DataRecord

from .editor import Editor


@dataclass
class MemoData:
    buffer: str = ''

    @property
    def length(self):
        # wcwidth.wcswidth returns -1 for strings with control chars (like newlines)
        # For memo data, just use the actual string length
        return len(self.buffer) if self.buffer else 0

    def __len__(self):
        # wcwidth.wcswidth returns -1 for strings with control chars (like newlines)
        # For memo data, just use the actual string length
        return len(self.buffer) if self.buffer else 0


class Memo(Editor):

    name = "Memo"
    cpMemo = "\x1A\x1B"

    def consumesData(self) -> bool:
        return True

    def getData(self) -> DataRecord:
        rec = DataRecord()
        # self.buffer is already a string, just use it directly
        # Remove null terminators and trailing nulls
        bufferStr = self.buffer.rstrip('\x00') if self.buffer else ''
        data = MemoData(bufferStr)
        rec.value = data
        return rec

    def setData(self, rec: MemoData):
        # Use string directly now instead of BufferArray
        self.buffer = rec.buffer
        self.setBufLen(rec.length)

    def getPalette(self) -> Palette:
        palette = Palette(self.cpMemo)
        return palette

    def handleEvent(self, event: Event):
        if event.what != evKeyDown or event.keyDown.keyCode != kbTab:
            super().handleEvent(event)
