# -*- coding: utf-8 -*-
from enum import Enum
import string
from vindauga.constants.event_codes import evKeyDown
from vindauga.constants.keys import kbShiftTab, kbTab, kbBackSpace, kbEnter, kbEsc, kbUp, kbDown
from vindauga.types.records.data_record import DataRecord

from .input_line import InputLine


class NumericInputType(Enum):
    UnsignedInteger = 0
    Integer = 1
    FloatingPoint = 2


class NumericInputLine(InputLine):
    def __init__(self, bounds, maxLen, inputType: NumericInputType):
        super().__init__(bounds, maxLen)
        self.inputType = inputType

    def handleEvent(self, event):
        if event.what == evKeyDown:
            keyCode = event.keyDown.keyCode
            if keyCode == kbUp:
                v = self._toNumber()
                v -= 1
                if self.inputType == NumericInputType.UnsignedInteger and v < 0:
                    v = 0
                super().setData(str(v))
                self.clearEvent(event)
            elif keyCode == kbDown:
                v = self._toNumber()
                v += 1
                super().setData(str(v))

            if keyCode not in {kbShiftTab, kbTab, kbBackSpace, kbEnter, kbEsc}:
                if event.keyDown.charScan.charCode:
                    if not self.isValidChar(event):
                        self.clearEvent(event)
        super().handleEvent(event)

    def isValidChar(self, event):
        key = event.keyDown.charScan.charCode
        if key in string.digits:
            return True

        if self.inputType == NumericInputType.UnsignedInteger:
            # Only digits
            return False

        if key == '-':
            currPos = self.current.pos
            if currPos and currPos == self.current.selEnd:
                return True
            if currPos > 0:
                return False
            if self.current.data[0] == '-':
                return False
            return True

        if self.inputType == NumericInputType.Integer:
            # only - and digits
            return False

        currPos = self.current.pos
        if key == '.':
            if currPos and currPos == self.current.selEnd:
                return True
            if '.' in self.current.data:
                return False
            return True
        return False

    def setData(self, value):
        super().setData(str(value))

    def _toNumber(self):
        if self.inputType == NumericInputType.FloatingPoint:
            return float(self.getDataString())
        return int(self.getDataString())

    def getData(self):
        return DataRecord(value=self._toNumber())
