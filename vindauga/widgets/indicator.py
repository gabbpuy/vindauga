# -*- coding: utf-8 -*-
from vindauga.constants.grow_flags import gfGrowLoY, gfGrowHiY
from vindauga.constants.state_flags import sfDragging
from vindauga.types.draw_buffer import DrawBuffer
from vindauga.types.palette import Palette
from vindauga.types.point import Point
from vindauga.types.view import View


class Indicator(View):
    dragFrame = '═'
    normalFrame = '─'

    name = 'Indicator'
    cpIndicator = "\x02\x03"

    def __init__(self, bounds):
        super().__init__(bounds)
        self._location = Point()
        self._modified = False
        self.growMode = gfGrowLoY | gfGrowHiY

    def draw(self):
        b = DrawBuffer()

        if not self.state & sfDragging:
            color = self.getColor(1)
            frame = self.dragFrame
        else:
            color = self.getColor(2)
            frame = self.normalFrame

        b.moveChar(0, frame, color, self.size.x)

        if self._modified:
            b.putChar(0, '☼')

        s = ' {:3d}:{:3d} '.format(self._location.y + 1, self._location.x + 1)

        b.moveCStr(8 - s.find(':'), s, color)
        self.writeBuf(0, 0, self.size.x, 1, b)

    def getPalette(self):
        return Palette(self.cpIndicator)

    def setState(self, state, enable):
        super().setState(state, enable)
        if state == sfDragging:
            self.drawView()

    def setValue(self, location: Point, modified: bool):
        if self._location != location or self._modified != modified:
            self._location.x = location.x
            self._location.y = location.y
            self._modified = modified
            self.drawView()
