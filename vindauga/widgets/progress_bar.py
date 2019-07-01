# -*- coding: utf-8 -*-
import logging
from vindauga.types.draw_buffer import DrawBuffer
from vindauga.types.palette import Palette
from vindauga.types.view import View

logger = logging.getLogger('vindauga.widgets.progress_bar')
cmStartProgress = 1000


class ProgressBar(View):
    cpProgressBar = '\x04'

    CHARS = '▏▎▍▌▋▊▉'
    BAR_CHAR = '█'

    def __init__(self, bounds, items, backChar):

        super().__init__(bounds)
        self.total = items
        self.backChar = backChar
        self.numOffset = (self.size.x // 2) - 3
        self.bar = [self.backChar] * self.size.x
        self.charValue = 100.0 / self.size.x
        self.progress = 0
        self.curPercent = 0
        self.curWidth = 0

    def draw(self):
        nBuf = DrawBuffer()
        text = '{}'.format(self.curPercent).rjust(3)
        colorNormal = self.getColor(1)

        fg = colorNormal >> 4
        hi = fg + ((colorNormal - (fg << 4)) << 4)

        nBuf.moveChar(0, self.backChar, colorNormal, self.size.x)
        nBuf.moveStr(self.numOffset, text, colorNormal)
        nBuf.moveStr(self.numOffset + 3, ' %', colorNormal)
        for i in range(self.curWidth):
           nBuf.putAttribute(i, hi)
        self.writeLine(0, 0, self.size.x, 1, nBuf)

    def getPalette(self):
        return Palette(self.cpProgressBar)

    def calcPercent(self):
        if not self.total:
            return
        percent = int(self.progress / self.total * 100.0)
        if percent != self.curPercent:
            self.curPercent = percent
            width = int(self.curPercent // self.charValue)
            if width != self.curWidth:
                self.curWidth = width

    def update(self, progress):
        self.progress = progress
        self.calcPercent()
        self.drawView()

    def setTotal(self, total):
        tmp = self.total
        self.total = total
        self.bar = [self.backChar] * self.size.x
        self.curWidth = 0
        self.progress = 0
        self.curPercent = 0
        if tmp:
            self.drawView()

    def setProgress(self, progress):
        self.progress = progress
        self.calcPercent()
        self.drawView()
