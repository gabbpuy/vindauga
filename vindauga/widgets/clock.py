# -*- coding: utf-8 -*-
import time
from vindauga.constants.grow_flags import gfGrowAll
from vindauga.types.draw_buffer import DrawBuffer
from vindauga.types.view import View


class ClockView(View):
    def __init__(self, bounds):
        super().__init__(bounds)
        self.lastTime = ' ' * 8
        self.curTime = ' ' * 8
        # If the window resizes, make sure this moves correctly
        self.growMode = gfGrowAll

    def draw(self):
        buf = DrawBuffer()
        c = self.getColor(2)
        buf.moveChar(0, ' ', c, self.size.x)
        buf.moveStr(0, self.curTime, c)
        self.writeLine(0, 0, self.size.x - 1, 1, buf)

    def update(self):
        t = time.time()
        date = time.ctime(t)
        self.curTime = date[11:19]
        if self.lastTime != self.curTime:
            self.drawView()
            self.lastTime = self.curTime
