# -*- coding: utf-8 -*-
import string

from vindauga.constants.event_codes import evBroadcast, evKeyboard
from vindauga.constants.option_flags import ofSelectable
from vindauga.types.draw_buffer import DrawBuffer
from vindauga.types.palette import Palette
from vindauga.types.view import View

DISPLAY_LEN = 25

csFirst = 1
csValid = 2
csError = 3

cmCalcButton = 300


class Calculator(View):
    cpCalcPalette = "\x13"

    def __init__(self, r):
        super().__init__(r)
        self.options |= ofSelectable
        self.eventMask = (evKeyboard | evBroadcast)
        self.number = ''
        self.operate = ''
        self.operand = ''
        self.status = None
        self.sign = ' '
        self.clear()

    def getPalette(self):
        return Palette(self.cpCalcPalette)

    def handleEvent(self, event):
        super().handleEvent(event)

        if event.what == evKeyboard:
            self.calcKey(event.keyDown.charScan.charCode)
            self.clearEvent(event)
        elif event.what == evBroadcast:
            if event.message.command == cmCalcButton:
                self.calcKey(event.message.infoPtr.title[0])
                self.clearEvent(event)

    def draw(self):
        color = self.getColor(1)

        buf = DrawBuffer()
        i = self.size.x - len(self.number) - 2

        buf.moveChar(0, ' ', color, self.size.x)
        buf.moveChar(1, self.sign, color, 1)
        buf.moveStr(i + 1, self.number, color)
        self.writeLine(0, 0, self.size.x, 1, buf)

    def clear(self):
        self.status = csFirst
        self.number = '0'
        self.sign = ' '
        self.operate = '='
        self.operand = 0.0

    def error(self):
        self.status = csError
        self.number = 'Error'
        self.sign = ' '

    def setDisplay(self, r):
        if r < 0.0:
            self.sign = '-'
            displayStr = str(-r)
        else:
            displayStr = str(r)
            self.sign = ' '

        if len(displayStr) > DISPLAY_LEN:
            self.error()
        else:
            self.number = displayStr

    def checkFirst(self):
        if self.status == csFirst:
            self.status = csValid
            self.number = '0'
            self.sign = ' '

    def calcKey(self, key):
        key = key.upper()

        if self.status == csError and key != 'C':
            key = ' '

        if key in string.digits:
            self.checkFirst()
            if len(self.number) < 15:
                if self.number == '0':
                    self.number = ''
                self.number += key
        elif key == '.':
            self.checkFirst()
            if '.' not in self.number:
                self.number += '.'

        elif key in {chr(8), chr(27), '←'}:
            self.checkFirst()
            if len(self.number) == 1:
                self.number = '0'
            else:
                self.number = self.number[:-1]

        elif key in {'_', '±'}:
            if self.sign == ' ':
                self.sign = '-'
            else:
                self.sign = ' '

        elif key in {'+', '-', '×', '*', '÷', '/', '=', '%', chr(13)}:
            if self.status == csValid:
                self.status = csFirst
                r = self.getDisplay() * [1, -1][int(self.sign == '-')]
                if key == '%':
                    if self.operate in {'+', '-'}:
                        r = self.operand * r / 100
                    else:
                        r /= 100

                if self.operate == '+':
                    self.setDisplay(self.operand + r)
                elif self.operate == '-':
                    self.setDisplay(self.operand - r)
                elif self.operate in {'*', '×'}:
                    self.setDisplay(self.operand * r)
                elif self.operate in {'÷', '/'}:
                    try:
                        self.setDisplay(self.operand / r)
                    except ArithmeticError:
                        self.error()

            self.operate = key
            self.operand = self.getDisplay() * [1, -1][int(self.sign == '-')]

        elif key == 'C':
            self.clear()

        self.drawView()

    def getDisplay(self):
        return float(self.number)
