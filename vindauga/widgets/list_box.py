# -*- coding: utf-8 -*-
from dataclasses import dataclass
import logging
from typing import Iterable

from .list_viewer import ListViewer


logger = logging.getLogger(__name__)


@dataclass
class ListBoxRec:
    items: Iterable = None
    selection: int = 0


class ListBox(ListViewer):
    name = 'ListBox'

    def __init__(self, bounds, numCols, vScrollBar, hScrollBar=None):
        super().__init__(bounds, numCols, hScrollBar, vScrollBar)
        self._items = None
        self.setRange(0)

    def consumesData(self):
        return True

    def getData(self):
        rec = ListBoxRec()
        rec.items = self._items
        rec.selection = self.focused
        return rec

    def getText(self, item, maxChars):
        dest = ''
        if self._items:
            dest = self._items[item][:maxChars]
        return dest

    def newList(self, collection):
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

        # Scroll to the bottom
        if self._range > 0:
            self.focusItem(self._range - 1)

        self.drawView()

    def setData(self, record):
        self.newList(record.items)
        self.focusItem(record.selection)
        self.drawView()

    def getList(self):
        return self._items
