# -*- coding: utf-8 -*-
import curses
import logging

from vindauga.constants.grow_flags import gfGrowHiX, gfGrowHiY
from vindauga.types.screen import Screen
from vindauga.utilities.ansify import wallpaper
from vindauga.types.draw_buffer import DrawBuffer
from vindauga.types.palette import Palette
from vindauga.types.view import View

logger = logging.getLogger(__name__)


class Wallpaper(View):
    """
    The default desktop background.

    `Background` is a very simple view which by default is the background of the
    desktop. It is a rectangle painted with an uniform pattern.
    """

    name = 'Wallpaper'
    cpBackground = "\x01"

    def __init__(self, bounds, filename):
        super().__init__(bounds)
        self._wpWidth, self._wpHeight, self._wallpaper = wallpaper(filename, bounds)
        self.growMode = gfGrowHiX | gfGrowHiY

    def draw(self):
        with Screen.screen.setRawMode():
            size = self.getBounds()
            vOffset = (size.height - self._wpHeight) // 2
            hOffset = (size.width - self._wpWidth) // 2
            for y, line in enumerate(self._wallpaper):
                self.writeLine(hOffset, vOffset + y, self._wpWidth, 1, line)

    def getPalette(self):
        palette = Palette(self.cpBackground)
        return palette
