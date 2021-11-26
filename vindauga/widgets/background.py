# -*- coding: utf-8 -*-
import logging

from vindauga.constants.grow_flags import gfGrowHiX, gfGrowHiY
from vindauga.types.draw_buffer import DrawBuffer
from vindauga.types.palette import Palette
from vindauga.types.view import View

logger = logging.getLogger(__name__)


class Background(View):
    """
    The default desktop background.

    `Background` is a very simple view which by default is the background of the
    desktop. It is a rectangle painted with an uniform pattern.
    """

    name = 'Background'
    cpBackground = "\x01"

    def __init__(self, bounds, pattern):
        super().__init__(bounds)
        self._pattern = pattern
        self.growMode = gfGrowHiX | gfGrowHiY

    def draw(self):
        b = DrawBuffer()
        b.moveChar(0, self._pattern, self.getColor(0x01), self.size.x)
        self.writeLine(0, 0, self.size.x, self.size.y, b)

    def getPalette(self):
        palette = Palette(self.cpBackground)
        return palette
