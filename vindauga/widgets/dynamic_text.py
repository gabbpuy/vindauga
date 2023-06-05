# -*- coding: utf-8 -*-
import wcwidth

from vindauga.types.draw_buffer import DrawBuffer
from vindauga.types.palette import Palette
from vindauga.types.view import View



class DynamicText(View):
    name = 'DynamicText'
    cpDynamicText = '\x06'

    def __init__(self, bounds, text, rightJustify=True):
        super().__init__(bounds)
        self._text = text
        self._rightJustify = rightJustify

    def draw(self):
        b = DrawBuffer()
        color = self.getColor(0x01)
        offset = self.size.x - wcwidth.wcswidth(self._text) if self._rightJustify else 0

        b.moveChar(0, ' ', color, self.size.x)
        b.moveStr(offset, self._text, color)
        self.writeBuf(0, 0, self.size.x, 1, b)

    def getPalette(self):
        return Palette(self.cpDynamicText)

    def setText(self, text):
        self.setData(text)
        self.drawView()

    def setData(self, text):
        self._text = text

    def getData(self):
        return self._text

    def consumesData(self):
        return True
