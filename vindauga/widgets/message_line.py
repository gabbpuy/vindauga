# -*- coding: utf-8 -*-
from vindauga.types.draw_buffer import DrawBuffer
from vindauga.types.palette import Palette
from vindauga.types.rect import Rect
from vindauga.types.view import View


class MessageLine(View):

    cpMessageLine = "\x02\x04"

    def __init__(self, bounds: Rect, s: str):
        super().__init__(bounds)
        self.width = bounds.bottomRight.x - bounds.topLeft.x
        self.text = s[:self.width]

    def getPalette(self) -> Palette:
        return Palette(self.cpMessageLine)

    def setText(self, s: str):
        self.text = s[:self.width]
        self.drawView()

    def draw(self):
        b = DrawBuffer()
        color = self.getColor(0x0201)

        b.moveChar(0, ' ', color, self.size.x)
        b.moveCStr(1, self.text, color)
        self.writeLine(0, 0, self.size.x, 1, b)
