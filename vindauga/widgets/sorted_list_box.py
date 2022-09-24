# -*- coding: utf-8 -*-
import logging

from vindauga.constants.command_codes import cmReleasedFocus
from vindauga.constants.event_codes import evBroadcast, evKeyDown
from vindauga.constants.keys import kbBackSpace

from .list_box import ListBox

logger = logging.getLogger(__name__)


def _equal(s1, s2, count):
    return s1[:count].upper() == s2[:count].upper()


class SortedListBox(ListBox):

    name = 'SortedListBox'

    def __init__(self, bounds, numCols, scrollBar):
        super().__init__(bounds, numCols, scrollBar)
        self._shiftState = 0
        self.__searchPos = -1

        self.showCursor()
        self.setCursor(1, 0)

    def newList(self, collection):
        super().newList(collection)
        self._items.sort()
        self.__searchPos = -1

    def handleEvent(self, event):
        oldValue = self.focused

        super().handleEvent(event)

        if oldValue != self.focused or (event.what == evBroadcast and event.message.command == cmReleasedFocus):
            self.__searchPos = -1

        if event.what == evKeyDown:
            if event.keyDown.charScan.charCode:
                value = self.focused

                curString = ''

                if value < self._range:
                    curString = self.getText(value, 255)

                oldPos = self.__searchPos

                if event.keyDown.keyCode == kbBackSpace:
                    if self.__searchPos == -1:
                        return
                    self.__searchPos -= 1

                    if self.__searchPos == -1:
                        self._shiftState = event.keyDown.controlKeyState
                    curString = curString[:self.__searchPos + 1]

                elif event.keyDown.charScan.charCode == '.':
                    self.__searchPos = curString.find('.')
                else:
                    self.__searchPos += 1
                    if self.__searchPos == 0:
                        self._shiftState = event.keyDown.controlKeyState

                    curString += event.keyDown.charScan.charCode

                k = self._getKey(curString)
                value = self.getList().search(k)

                if value < self._range:
                    newString = self.getText(value, 255)
                    if _equal(curString, newString, self.__searchPos + 1):
                        if value != oldValue:
                            self.focusItem(value)
                            self.setCursor(self.cursor.x + self.__searchPos + 1, self.cursor.y)
                        else:
                            self.setCursor(self.cursor.x + (self.__searchPos - oldPos), self.cursor.y)
                    else:
                        self.__searchPos = oldPos
                else:
                    self.__searchPos = oldPos

                if self.__searchPos != oldPos or event.keyDown.charScan.charCode.isalpha():
                    self.clearEvent(event)

    def _getKey(self, s):
        return s
