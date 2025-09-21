# -*- coding: utf-8 -*-
import logging

from vindauga.constants.grow_flags import gfGrowHiX, gfGrowHiY
from vindauga.types.draw_buffer import DrawBuffer
from vindauga.types.palette import Palette
from vindauga.types.rect import Rect
from vindauga.types.view import View

logger = logging.getLogger(__name__)


class Background(View):
    """
    The default desktop background.

    `Background` is a very simple view which by default is the background of the
    desktop. It is a rectangle painted with a uniform pattern.
    """

    name = 'Background'
    cpBackground = "\x01"

    def __init__(self, bounds: Rect, pattern: str):
        super().__init__(bounds)
        self._pattern = pattern
        self.growMode: int = gfGrowHiX | gfGrowHiY

    def draw(self):
        b = DrawBuffer()
        color_pair = self.getColor(0x01)
        color_attr = color_pair & 0xFF
        b.moveChar(0, self._pattern, color_attr, self.size.x)
        self.writeLine(0, 0, self.size.x, self.size.y, b)

    def getPalette(self) -> Palette:
        palette = Palette(self.cpBackground)
        return palette
