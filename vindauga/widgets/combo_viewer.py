# -*- coding: utf-8 -*-
import string
from vindauga.constants.command_codes import cmOK, cmCancel
from vindauga.constants.event_codes import evMouseDown, evKeyDown, evCommand, meDoubleClick
from vindauga.constants.keys import kbEnter, kbEsc, kbTab
from vindauga.events.event import Event
from vindauga.types.collections.collection import Collection
from vindauga.types.palette import Palette
from vindauga.types.rect import Rect
from vindauga.types.screen import Screen

from .list_viewer import ListViewer
from .scroll_bar import ScrollBar


def matchChars(item, target):
    return item == target


class ComboViewerRec:
    def __init__(self, items, selection):
        self.items = items
        self.selection = selection


class ComboViewer(ListViewer):
    name = 'ComboViewer'
    cpComboViewer = '\x06\x06\x07\x06\x06'

    def __init__(self, bounds: Rect, collection: Collection, scrollBar: ScrollBar):
        super().__init__(bounds, 1, None, scrollBar)
        self.collection = None
        self.newList(collection)
        self.testChar = ''

    def consumesData(self) -> bool:
        return True

    def getPalette(self) -> Palette:
        return Palette(self.cpComboViewer)

    @staticmethod
    def matchChars(item: str, target: str) -> bool:
        return item.lower().startswith(target.lower())

    def getData(self) -> ComboViewerRec:
        rec = ComboViewerRec(self.collection, self.focused)
        return rec

    def getText(self, item: int, maxLen: int) -> str:
        return self.collection.getText(item)[:maxLen]

    def handleEvent(self, event: Event):
        if ((event.what == evMouseDown and event.mouse.eventFlags & meDoubleClick) or
                (event.what == evKeyDown and event.keyDown.keyCode == kbEnter)):
            self.testChar = ''
            self.endModal(cmOK)
            self.clearEvent(event)
            return
        if ((event.what == evKeyDown and event.keyDown.keyCode == kbEsc) or
                (event.what == evCommand and event.message.command == cmCancel)):
            self.testChar = ''
            self.endModal(cmCancel)
            self.clearEvent(event)
            return
        if event.what == evKeyDown:
            if event.keyDown.charScan.charCode in string.printable and event.keyDown.keyCode != kbTab:
                self.testChar += event.keyDown.charScan.charCode
                tempData = self.collection.firstTextThat(self.matchChars, self.testChar)
                if tempData:
                    self.focusItemNum(self.collection.indexOf(tempData))
                else:
                    self.testChar = self.testChar[:-1]
                    Screen.screen.makeBeep()
                self.clearEvent(event)
                return
            elif event.keyDown.keyCode == kbTab:
                pass
            else:
                self.testChar = ''
        super().handleEvent(event)

    def newList(self, collection: Collection):
        if self.collection:
            self.destroy(self.collection)

        self.collection = collection
        self.setRange(len(self.collection))

        if self._range > 0:
            self.focusItem(0)
        self.drawView()

    def setData(self, rec: ComboViewerRec):
        self.newList(rec.items)
        self.focusItem(rec.selection)
        self.drawView()

    def shutdown(self):
        self.collection = None
        super().shutdown()
