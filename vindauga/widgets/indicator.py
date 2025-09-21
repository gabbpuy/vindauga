# -*- coding: utf-8 -*-
from vindauga.constants.grow_flags import gfGrowLoY, gfGrowHiY
from vindauga.constants.state_flags import sfDragging
from vindauga.types.draw_buffer import DrawBuffer
from vindauga.types.palette import Palette
from vindauga.types.point import Point
from vindauga.types.rect import Rect
from vindauga.types.view import View


class Indicator(View):
    dragFrame = '═'
    normalFrame = '─'

    name = 'Indicator'
    cpIndicator = "\x02\x03"

    def __init__(self, bounds: Rect):
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
            b.putChar(0, '☼', color)

        s = f' {self._location.y + 1:3d}:{self._location.x + 1:3d} '

        attr_pair = color
        b.moveCStr(8 - s.find(':'), s, attr_pair)
        self.writeBuf(0, 0, self.size.x, 1, b)

    def getPalette(self) -> Palette:
        return Palette(self.cpIndicator)

    def setState(self, state: int, enable: bool):
        super().setState(state, enable)
        if state == sfDragging:
            self.drawView()

    def setValue(self, location: Point, modified: bool):
        if self._location != location or self._modified != modified:
            self._location.x = location.x
            self._location.y = location.y
            self._modified = modified
            self.drawView()
