# -*- coding: utf-8 -*-
import logging
import string

from vindauga.constants.command_codes import cmReleasedFocus
from vindauga.constants.event_codes import evKeyDown
from vindauga.constants.keys import kbUp, kbHome, kbEnd, kbLeft, kbRight, kbBackSpace, kbIns, kbDel, kbEnter, kbTab
from vindauga.events.event import Event
from vindauga.types.collections.collection import Collection
from vindauga.types.rect import Rect
from vindauga.types.screen import Screen

from .input_regex import InputRegex


logger = logging.getLogger(__name__)


class StaticInputLine(InputRegex):
    name = "StaticInputLine"

    def __init__(self, bounds: Rect, maxLen: int, collection: Collection):
        super().__init__(bounds, maxLen)
        self.collection = collection
        self.searchString = ''

    @staticmethod
    def matchChars(item: str, target: str) -> bool:
        if not target:
            return item == ''
        return item.lower().startswith(target.lower())

    def handleEvent(self, event: Event):
        if event.what == evKeyDown:
            if not self.collection:
                super().handleEvent(event)
                return

            charCode = event.keyDown.charScan.charCode
            ekk = event.keyDown.keyCode
            if charCode in string.printable and ekk not in {kbEnter, kbTab}:
                self.searchString += event.keyDown.charScan.charCode
                tempData = self.collection.firstThat(self.matchChars, self.searchString)
                if tempData:
                    self.setData(tempData)
                    self.current.selStart = 0
                    self.current.selEnd = len(self.searchString)
                    self.current.pos = len(self.searchString)
                    self.drawView()
                else:
                    logger.info('::handleEvent() no match for %s', self.searchString)
                    self.searchString = self.searchString[:-1]
                    Screen.screen.makeBeep()
                self.clearEvent(event)
                return

            ekk = event.keyDown.keyCode

            if ekk in {kbLeft, kbRight, kbHome, kbEnd}:
                off = {kbLeft: -1, kbRight: 1, kbHome: -len(self.collection), kbEnd: len(self.collection)}[ekk]
                if len(self.collection):
                    idx = self.collection.indexOf(self.collection.firstThat(self.matchChars, self.getDataString()))
                    idx += off
                    idx = min(max(idx, 0), len(self.collection) - 1)
                    self.setData(self.collection[idx][:self.maxLen])
                self.searchString = ''
                self.selectAll(False)
                self.drawView()
                self.clearEvent(event)
                return
            if ekk in {kbUp, kbIns}:
                self.clearEvent(event)
                return
            if ekk == kbDel:
                self.searchString = ''
                self.setData('')
                self.current.selStart = self.current.selEnd = self.current.pos = 0
                self.drawView()
                self.clearEvent(event)
                return
            if ekk == kbBackSpace:
                if self.searchString:
                    self.searchString = self.searchString[:-1]
                tempData = self.collection.firstThat(self.matchChars, self.searchString)
                if not tempData:
                    tempData = self.collection[0]

                self.setData(tempData[:self.maxLen])
                self.current.selStart = 0
                self.current.selEnd = self.current.pos = len(self.searchString)
                self.drawView()
                self.clearEvent(event)
                return
        super().handleEvent(event)

    def valid(self, command: int) -> bool:
        if command == cmReleasedFocus:
            self.searchString = ''
            return True
        return super().valid(command)

    def newList(self, collection: Collection):
        self.collection = collection
        self.drawView()
