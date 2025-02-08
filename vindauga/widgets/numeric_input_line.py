# -*- coding: utf-8 -*-
from enum import Enum
import string
from typing import Optional, Union

from vindauga.constants.event_codes import evKeyDown
from vindauga.constants.validation_constants import vtGetData
from vindauga.constants.keys import (kbShiftTab, kbTab, kbBackSpace, kbEnter, kbEsc, kbUp, kbDown, kbDel,
                                     kbLeft, kbShiftLeft, kbRight, kbShiftRight, kbHome, kbShiftHome, kbEnd, kbShiftEnd,
                                     kbIns, kbCtrlY)

from vindauga.events.event import Event
from vindauga.types.records.data_record import DataRecord
from vindauga.types.rect import Rect
from vindauga.types.validation.validator import Validator

from .input_line import InputLine


class NumericInputType(Enum):
    UnsignedInteger = 0
    Integer = 1
    FloatingPoint = 2


class NumericInputLine(InputLine):
    def __init__(self, bounds: Rect, maxLen: int, inputType: NumericInputType, validator: Optional[Validator] = None):
        super().__init__(bounds, maxLen, validator=validator)
        self.inputType = inputType

    def handleEvent(self, event: Event):
        if event.what == evKeyDown:
            keyCode = event.keyDown.keyCode
            if keyCode == kbDown:
                v = self._toNumber()

                if self.inputType == NumericInputType.FloatingPoint:
                    v -= .1
                else:
                    v -= 1
                if self.inputType == NumericInputType.UnsignedInteger and v < 0:
                    v = 0
                self.setData(v)
                self.clearEvent(event)
            elif keyCode == kbUp:
                v = self._toNumber()
                if self.inputType == NumericInputType.FloatingPoint:
                    v += .1
                else:
                    v += 1
                self.setData(v)
                self.clearEvent(event)
            elif keyCode not in {kbShiftTab, kbTab, kbBackSpace, kbEnter, kbEsc, kbDel,
                                 kbLeft, kbShiftLeft, kbRight, kbShiftRight,
                                 kbHome, kbShiftHome, kbEnd, kbShiftEnd, kbIns, kbCtrlY}:
                if event.keyDown.charScan.charCode:
                    if not self.isValidChar(event):
                        self.clearEvent(event)
        super().handleEvent(event)

    def isValidChar(self, event: Event) -> bool:
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
            if self.current.data and self.current.data[0] == '-':
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

    def setData(self, value: Union[int, float]):
        if self.inputType == NumericInputType.FloatingPoint:
            v = f'{value:.2f}'
        else:
            v = str(value)
        super().setData(v)

    def _toNumber(self):
        s = self.getDataString() or '0'
        if self.inputType == NumericInputType.FloatingPoint:
            return float(s)
        return int(s)

    def getData(self) -> DataRecord:
        rec = DataRecord()
        if not self.validator or not self.validator.transfer(''.join(self.current.data), rec, vtGetData):
            rec.value = self._toNumber()
        return rec
