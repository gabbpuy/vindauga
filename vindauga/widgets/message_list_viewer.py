# -*- coding: utf-8 -*-
import logging

from vindauga.types.collections.collection import Collection
from vindauga.constants.drag_flags import dmDragGrow
from vindauga.constants.grow_flags import gfGrowHiX, gfGrowHiY
from vindauga.types.palette import Palette
from vindauga.widgets.list_viewer import ListViewer

logger = logging.getLogger('vindauga.widgets.message_list_viewer')


class MessageListViewer(ListViewer):

    cpMsgList = "\x09\x0A\x0B\x0C\x0D"

    def __init__(self, bounds, numCols, hScrollBar, vScrollbar):
        super().__init__(bounds, numCols, hScrollBar, vScrollbar)
        self.dragMode = dmDragGrow
        self.growMode = gfGrowHiX | gfGrowHiY
        self.items = Collection()
        self.setRange(0)

    def getText(self, item, maxLen):
        if self.items:
            return self.items[item][:maxLen]

    def getPalette(self):
        return Palette(self.cpMsgList)

    def insert(self, message):
        self.items.append(message)
        self.setRange(len(self.items))
        self.focusItemNum(len(self.items) - 1)
        self.drawView()

    def list(self):
        return self.items
