# -*- coding: utf-8 -*-
import logging
from vindauga.constants.event_codes import evKeyDown, evMouseDown, mbLeftButton
from vindauga.constants.keys import kbF7, kbF8, kbF9, kbEnter
from vindauga.events.event import Event
from vindauga.types.rect import Rect

from .list_box import ListBox, ListBoxRec

logger = logging.getLogger(__name__)


class MultiSelectListBox(ListBox):
    tag = '→'

    def __init__(self, bounds: Rect, numColumns, scrollBar):
        super().__init__(bounds, numColumns, vScrollBar=scrollBar)
        self.selectedItems = set()

    def handleEvent(self, event: Event):
        if event.what == evMouseDown and event.mouse.buttons == mbLeftButton:
            super().handleEvent(event)
            self.__toggleItem(self.focused)
            self.clearEvent(event)
            self.drawView()
            return
        elif event.what == evKeyDown:
            kc = event.keyDown.keyCode
            if kc in {kbEnter, kbF7, kbF8, kbF9}:
                if kc == kbEnter:
                    self.__toggleItem(self.focused)
                elif kc == kbF7:
                    self.__markAll()
                elif kc == kbF8:
                    self.__unmarkAll()
                elif kc == kbF9:
                    self.__toggleAll()
                self.drawView()
                self.clearEvent(event)
                return
        super().handleEvent(event)

    def __toggleItem(self, itemNumber: int):
        if self._range <= 0:
            return
        if itemNumber in self.selectedItems:
            self.selectedItems.remove(itemNumber)
        else:
            self.selectedItems.add(itemNumber)

    def __markAll(self):
        if self._range <= 0:
            return

        self.selectedItems.update(range(self._range))

    def __unmarkAll(self):
        if self._range <= 0:
            return

        self.selectedItems = set()

    def __toggleAll(self):
        allItems = set(range(self._range))
        self.selectedItems = allItems - self.selectedItems

    def getText(self, item: int, maxChars: int) -> str:
        text = super().getText(item, maxChars)
        if item in self.selectedItems:
            text = f'{self.tag} {text}'
        else:
            text = f'  {text}'
        return text[:maxChars]

    def getData(self) -> ListBoxRec:
        rec = ListBoxRec()
        rec.items = self._items
        rec.selection = tuple(self.selectedItems)
        return rec
