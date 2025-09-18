# -*- coding: utf-8 -*-
from dataclasses import dataclass
import logging
from typing import Optional

from vindauga.types.collections.collection import Collection
from vindauga.types.rect import Rect

from .list_viewer import ListViewer
from .scroll_bar import ScrollBar


logger = logging.getLogger(__name__)


@dataclass
class ListBoxRec:
    items: Collection = None
    selection: int = 0


class ListBox(ListViewer):
    name = 'ListBox'

    def __init__(self, bounds: Rect, numCols: int, vScrollBar: ScrollBar, hScrollBar: Optional[ScrollBar] = None):
        super().__init__(bounds, numCols, hScrollBar, vScrollBar)
        self._items = None
        self.setRange(0)

    def consumesData(self) -> bool:
        return True

    def getData(self) -> ListBoxRec:
        rec = ListBoxRec()
        rec.items = self._items
        rec.selection = self.focused
        return rec

    def getText(self, item: int, maxChars: int) -> str:
        dest = ''
        if self._items:
            dest = self._items[item][:maxChars]
        return dest

    def newList(self, collection: Collection):
        self._items = collection
        self.update()

    def update(self):
        collection = self._items
        if collection:
            if self.hScrollBar:
                self.hScrollBar.setParams(
                    self.hScrollBar.value,
                    0, max(len(s) for s in self._items),
                    self.hScrollBar.pageStep, self.hScrollBar.arrowStep)

            self.setRange(len(collection))
        else:
            self.setRange(0)

        # if self._range > 0:
        #     self.focusItem(0)
        self.drawView()

    def setData(self, record: ListBoxRec):
        self.newList(record.items)
        self.focusItem(record.selection)
        self.drawView()

    def getList(self) -> Collection:
        return self._items
