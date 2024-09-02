# -*- coding: utf-8 -*-
import logging
from vindauga.types.draw_buffer import DrawBuffer
from vindauga.types.palette import Palette
from vindauga.types.rect import Rect
from vindauga.types.view import View

logger = logging.getLogger(__name__)
cmStartProgress = 1000


class ProgressBar(View):
    cpProgressBar = '\x04'

    CHARS = '▏▎▍▌▋▊▉'
    FILL_CHAR = '█'
    BACK_CHAR = ' '

    def __init__(self, bounds: Rect, items: int, backChar: str = BACK_CHAR):

        super().__init__(bounds)
        self.total = items
        self.backChar = backChar
        self.progress = 0.0
        self.curPercent = 0.0

    def draw(self):
        nBuf = DrawBuffer()
        text = f'{int(self.curPercent):-3d} %'
        colorNormal = self.getColor(1)
        dill = 0

        if self.total:
            fill = self.progress * self.size.x / self.total
            dill = int(fill)
            diff = fill - dill
            nBuf.moveChar(0, self.FILL_CHAR, colorNormal, dill)
            if diff > .125:
                f = int(diff * 8) - 1
                nBuf.moveChar(dill, self.CHARS[f], colorNormal, 1)
                dill += 1

        nBuf.moveChar(dill, self.backChar, colorNormal, self.size.x - dill)
        numOffset = max(0, (dill // 2) - 3)
        nBuf.moveStr(numOffset, text, colorNormal)
        self.writeLine(0, 0, self.size.x, 1, nBuf)

    def getPalette(self) -> Palette:
        return Palette(self.cpProgressBar)

    def calcPercent(self):
        if not self.total:
            return
        percent = int(self.progress / self.total * 100.0)
        if percent != self.curPercent:
            self.curPercent = percent

    def update(self, progress: float):
        self.progress = progress
        self.calcPercent()
        self.drawView()

    def setTotal(self, total: int):
        self.total = total
        self.calcPercent()
        if total:
            self.drawView()

    def setProgress(self, progress: float):
        self.progress = progress
        self.calcPercent()
        self.drawView()
