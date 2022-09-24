# -*- coding: utf-8 -*-
import logging
from typing import Optional

from vindauga.constants.command_codes import cmCancel, cmValid
from vindauga.constants.event_codes import evMouseDown, evMouseAuto, meDoubleClick, evMouseMove, evKeyDown
from vindauga.constants.keys import (kbShift, kbLeft, kbRight, kbHome, kbEnd, kbBackSpace, kbDel, kbIns, kbCtrlY,
                                     kbEnter, kbTab, kbShiftHome, kbShiftLeft, kbShiftRight, kbShiftEnd)
from vindauga.constants.option_flags import ofSelectable, ofFirstClick
from vindauga.constants.state_flags import sfCursorVis, sfCursorIns, sfActive, sfSelected, sfFocused
from vindauga.constants.validation_constants import vtDataSize, vtGetData, vtSetData, vsOK
from vindauga.events.event import Event
from vindauga.misc.util import ctrlToArrow
from vindauga.types.draw_buffer import DrawBuffer
from vindauga.types.palette import Palette
from vindauga.types.records.data_record import DataRecord
from vindauga.types.rect import Rect
from vindauga.types.view import View
from vindauga.types.validation.validator import Validator

logger = logging.getLogger(__name__)

class State:
    def __init__(self):
        self.pos = 0
        self.firstPos = 0
        self.selStart = 0
        self.selEnd = 0
        self.anchor = -1
        self.data = []

    def update(self, other):
        self.pos = other.pos
        self.firstPos = other.firstPos
        self.selStart = other.selStart
        self.selEnd = other.selEnd
        self.anchor = other.anchor
        self.data = other.data[:]

    def deleteSelect(self):
        if self.selStart < self.selEnd:
            self.data = self.data[:self.selStart] + self.data[self.selEnd:]
            self.pos = self.selStart

    def adjustSelectBlock(self):
        if self.anchor < 0:
            self.selEnd = self.selStart = 0
        else:
            if self.pos < self.anchor:
                self.selStart = self.pos
                self.selEnd = self.anchor
            else:
                self.selStart = self.anchor
                self.selEnd = self.pos

    def selectAll(self, enable, size):
        self.selStart = 0
        if enable:
            self.pos = self.selEnd = len(self.data)
        else:
            self.pos = self.selEnd = 0

        self.firstPos = max(0, self.pos - size.x + 2)
        self.anchor = 0

    def __repr__(self):
        return f'State: p: {self.pos}, 1: {self.firstPos}, s: {self.selStart}, e: {self.selEnd}, a: {self.anchor} d:{len(self.data)}'


class InputLine(View):
    rightArrow = '►'
    leftArrow = '◄'
    cpInputLine = '\x13\x13\x14\x15'
    name = 'InputLine'

    def __init__(self, bounds: Rect, maxLen: int, validator: Optional[Validator] = None):
        super().__init__(bounds)

        self.maxLen = maxLen - 1
        self.current = State()
        self.old = State()

        self.validator = validator

        self.state |= sfCursorVis
        self.options |= ofSelectable | ofFirstClick

    def consumesData(self) -> bool:
        return True

    def dataSize(self) -> int:
        return self.maxLen

    def draw(self):
        b = DrawBuffer()

        if self.state & sfFocused:
            color = self.getColor(2)
        else:
            color = self.getColor(1)

        b.moveChar(0, ' ', color, self.size.x)

        buf = ''.join(self.current.data[self.current.firstPos:self.current.firstPos + self.size.x - 2])

        b.moveStr(1, buf, color)

        if self.__canScroll(1):
            b.moveChar(self.size.x - 1, self.rightArrow, self.getColor(4), 1)
        if self.__canScroll(-1):
            b.moveChar(0, self.leftArrow, self.getColor(4), 1)

        if self.state & sfSelected:
            left = self.current.selStart - self.current.firstPos
            right = self.current.selEnd - self.current.firstPos

            left = max(0, left)
            right = min(self.size.x - 2, right)
            if left < right:
                b.moveChar(left + 1, 0, self.getColor(3), right - left)

        self.writeLine(0, 0, self.size.x, self.size.y, b)
        self.setCursor(self.current.pos - self.current.firstPos + 1, 0)

    def getData(self) -> DataRecord:
        rec = DataRecord()
        if not self.validator or (self.validator.transfer(''.join(self.current.data), rec, vtGetData) == 0):
            rec.value = ''.join(self.current.data)
        return rec

    def getDataString(self) -> str:
        return ''.join(self.current.data)

    def getPalette(self) -> Palette:
        palette = Palette(self.cpInputLine)
        return palette

    def handleEvent(self, event: Event):
        # Scancodes for numpad keys...
        numpad_keys = {kbShiftLeft, kbShiftRight, kbShiftHome, kbShiftEnd}
        super().handleEvent(event)

        if self.state & sfSelected:
            if event.what == evMouseDown:
                delta = self.__mouseDelta(event)
                if self.__canScroll(delta):
                    done = False
                    while not done:
                        self.current.firstPos += delta
                        self.drawView()
                        done = not self.mouseEvent(event, evMouseAuto)
                elif event.mouse.eventFlags & meDoubleClick:
                    self.selectAll(True)
                else:
                    self.current.anchor = self.__mousePos(event)
                    done = False
                    while not done:
                        if event.what == evMouseAuto:
                            delta = self.__mouseDelta(event)
                            if self.__canScroll(delta):
                                self.current.firstPos += delta

                        self.current.pos = self.__mousePos(event)
                        self.__adjustSelectBlock()
                        self.drawView()

                        done = not (self.mouseEvent(event, evMouseMove | evMouseAuto))
                self.clearEvent(event)
            elif event.what == evKeyDown:
                self.__saveState()
                oldKeyCode = event.keyDown.keyCode
                event.keyDown.keyCode = ctrlToArrow(event.keyDown.keyCode)
                if event.keyDown.keyCode in numpad_keys:
                    if self.current.anchor < 0:
                        self.current.anchor = self.current.pos
                else:
                    self.current.anchor = -1

                kc = event.keyDown.keyCode

                if kc in (kbLeft, kbShiftLeft):
                    if self.current.pos > 0:
                        self.current.pos -= 1
                elif kc in (kbRight, kbShiftRight):
                    if self.current.pos < len(self.current.data):
                        self.current.pos += 1
                elif kc in (kbHome, kbShiftHome):
                    self.current.pos = 0
                elif kc in (kbEnd, kbShiftEnd):
                    self.current.pos = len(self.current.data)
                elif kc == kbBackSpace:
                    self.__deleteSelect()
                    if self.current.pos > 0:
                        del self.current.data[self.current.pos - 1]
                        self.current.pos -= 1
                        if self.current.firstPos > 0:
                            self.current.firstPos -= 1
                elif kc == kbDel:
                    if self.current.selStart == self.current.selEnd:
                        if self.current.pos < len(self.current.data):
                            self.current.selStart = self.current.pos
                            self.current.selEnd = self.current.pos + 1
                    self.__deleteSelect()
                elif kc == kbIns:
                    self.setState(sfCursorIns, not (self.state & sfCursorIns))
                elif kc == kbCtrlY:
                    self.current.data = []
                    self.current.pos = 0
                elif kc in (kbEnter, kbTab):
                    return
                else:
                    if event.keyDown.charScan.charCode >= ' ':
                        if not self.insertChar(event.keyDown.charScan.charCode):
                            self.clearEvent(event)
                    else:
                        event.keyDown.keyCode = oldKeyCode
                        return

                self.__adjustSelectBlock()
                self.makeVisible()
                self.clearEvent(event)

    def insertChar(self, value: str) -> bool:
        if self.validator:
            if not self.validator.isValidInput(value, False):
                return False
        if not self.state & sfCursorIns:
            self.__deleteSelect()
        length = len(self.current.data)
        if ((not self.state & sfCursorIns and length < self.maxLen) or
                (self.state & sfCursorIns and self.current.pos < self.maxLen)):
            if self.current.firstPos > self.current.pos:
                self.current.firstPos = self.current.pos
            self.current.data.insert(self.current.pos, value)
            self.current.pos += 1
        return True

    def makeVisible(self):
        if self.current.firstPos > self.current.pos:
            self.current.firstPos = self.current.pos
        i = self.current.pos - self.size.x - 2
        if self.current.firstPos < i:
            self.current.firstPos = i
        self.drawView()

    def selectAll(self, enable: bool):
        self.current.selectAll(enable, self.size)
        self.drawView()

    def setData(self, rec):
        if not self.validator or (self.validator.transfer(self.current.data, rec, vtSetData) == 0):
            if isinstance(rec, str):
                self.current.data = list(rec)
            else:
                self.current.data = rec or []

        self.selectAll(True)

    def setState(self, state: int, enable: bool):
        super().setState(state, enable)
        if state == sfSelected or (state == sfActive and (self.state & sfSelected)):
            self.selectAll(enable)

    def setValidator(self, validator: Validator):
        self.validator = validator

    def valid(self, command):
        if self.validator:
            if command == cmValid:
                return self.validator.status == vsOK
            elif command != cmCancel:
                if not self.validator.validate(''.join(self.current.data)):
                    self.select()
                    return False
        return True

    def __canScroll(self, delta: int) -> bool:
        if delta < 0:
            return self.current.firstPos > 0

        if delta > 0:
            return (len(self.current.data) - self.current.firstPos + 2) > self.size.x
        return False

    def __mouseDelta(self, event: Event) -> int:
        mouse = self.makeLocal(event.mouse.where)

        if mouse.x <= 0:
            return -1

        if mouse.x >= self.size.x - 1:
            return 1
        return 0

    def __mousePos(self, event: Event) -> int:
        mouse = self.makeLocal(event.mouse.where)

        mouse.x = max(mouse.x, 1)
        pos = mouse.x + self.current.firstPos - 1

        pos = max(pos, 0)
        pos = min(pos, len(self.current.data))
        return pos

    def __deleteSelect(self):
        self.current.deleteSelect()

    def __adjustSelectBlock(self):
        self.current.adjustSelectBlock()

    def __saveState(self):
        if self.validator:
            self.old.update(self.current)

    def __restoreState(self):
        if self.validator:
            self.current.update(self.old)

    def __checkValid(self, noAutoFill) -> bool:
        if self.validator:
            oldLen = len(self.current.data)
            newData = self.current.data
            if not self.validator.isValidInput(newData, noAutoFill):
                self.__restoreState()
                return False

            if len(newData) > self.maxLen:
                newData = newData[:self.maxLen]

            self.current.data = newData

            if self.current.pos >= oldLen and len(self.current.data) > oldLen:
                self.current.pos = len(self.current.data)
        return True

