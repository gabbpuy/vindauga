# -*- coding: utf-8 -*-
import wcwidth

from vindauga.types.draw_buffer import DrawBuffer
from vindauga.types.palette import Palette
from vindauga.types.rect import Rect
from vindauga.types.view import View


class DynamicText(View):
    name = 'DynamicText'
    cpDynamicText = '\x06'

    def __init__(self, bounds: Rect, text: str, rightJustify: bool = True):
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

    def getPalette(self) -> Palette:
        return Palette(self.cpDynamicText)

    def setText(self, text: str):
        self.setData(text)
        self.drawView()

    def setData(self, text: str):
        self._text = text

    def getData(self) -> str:
        return self._text

    def consumesData(self) -> bool:
        return True
