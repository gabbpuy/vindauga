# -*- coding: utf-8 -*-
import logging

import wcwidth

from vindauga.types.collections.collection import Collection
from vindauga.constants.drag_flags import dmDragGrow
from vindauga.constants.grow_flags import gfGrowHiX, gfGrowHiY
from vindauga.types.palette import Palette
from vindauga.types.rect import Rect
from vindauga.widgets.list_viewer import ListViewer
from vindauga.widgets.scroll_bar import ScrollBar

logger = logging.getLogger(__name__)


class MessageListViewer(ListViewer):

    cpMsgList = "\x09\x0A\x0B\x0C\x0D"

    def __init__(self, bounds: Rect, numCols: int, hScrollBar: ScrollBar, vScrollbar: ScrollBar):
        super().__init__(bounds, numCols, hScrollBar, vScrollbar)
        self.dragMode = dmDragGrow
        self.growMode = gfGrowHiX | gfGrowHiY
        self.items = Collection()
        self.setRange(0)

    def getText(self, item: int, maxLen: int) -> str:
        if self.items:
            return self.items[item][:maxLen]
        return super().getText(item, maxLen)

    def getPalette(self) -> Palette:
        return Palette(self.cpMsgList)

    def insert(self, message: str):
        self.items.append(message)
        self.setRange(len(self.items))
        textLen = max(wcwidth.wcswidth(s) for s in self.items)
        self.hScrollBar.setRange(0, textLen)
        self.focusItemNum(len(self.items) - 1)
        self.drawView()

    def list(self) -> Collection:
        return self.items
