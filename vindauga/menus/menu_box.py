# -*- coding: utf-8 -*-
import logging

from vindauga.constants.option_flags import ofPreProcess
from vindauga.constants.state_flags import sfShadow
from vindauga.misc.cp437 import cp437ToUnicode
from vindauga.misc.util import nameLength
from vindauga.types.draw_buffer import DrawBuffer
from vindauga.types.rect import Rect
from .menu_view import MenuView

logger = logging.getLogger(__name__)


class MenuBox(MenuView):
    """
    TMenuBox objects represent vertical menu boxes. Color coding is used to
    indicate disabled items. Menu boxes can be instantiated as submenus of the
    menu bar or other menu boxes, or can be used alone as pop-up menus.
    """
    name = 'MenuBox'
    frameChars = ' ┌─┐  └─┘  │ │  ├─┤ '
    subMenuIndicator = '►'

    def __init__(self, bounds, menu, parentMenu):
        super().__init__(self.getRect(bounds, menu), menu, parentMenu)
        self.state |= sfShadow
        self.options |= ofPreProcess

    @property
    def cNormal(self):
        return self.getColor(0x0301)

    @staticmethod
    def getRect(bounds, menu):
        w = 10
        h = 2
        r = Rect(bounds.topLeft.x, bounds.topLeft.y, bounds.bottomRight.x, bounds.bottomRight.y)

        if menu:
            for p in menu.items:
                h += 1
                if not p.name:
                    continue
                nameLen = nameLength(p.name) + 6
                if not p.command:
                    nameLen += 3
                elif p.param:
                    nameLen += (nameLength(p.param) + 2)
                w = max(nameLen, w)

            if (r.topLeft.x + w) < r.bottomRight.x:
                r.bottomRight.x = r.topLeft.x + w
            else:
                r.topLeft.x = r.bottomRight.x - w

            if (r.topLeft.y + h) < r.bottomRight.y:
                r.bottomRight.y = r.topLeft.y + h
            else:
                r.topLeft.y = r.bottomRight.y - h
        return r

    def draw(self):
        """
        Draws the framed menu box and associated menu items in the default
        colors.
        """
        b = DrawBuffer()
        cSelect = self.getColor(0x0604)
        cNormDisabled = self.getColor(0x0202)
        cSelDisabled = self.getColor(0x0505)
        y = 0
        color = self.cNormal
        self.__frameLine(b, 0, color)
        self.writeBuf(0, y, self.size.x, 1, b)
        y += 1

        if self.menu:
            for p in self.menu.items:
                color = self.cNormal
                if not p.name:
                    self.__frameLine(b, 15, color)
                else:
                    if p.disabled:
                        if p is self._current:
                            color = cSelDisabled
                        else:
                            color = cNormDisabled
                    elif p is self._current:
                        color = cSelect

                    self.__frameLine(b, 10, color)
                    b.moveCStr(3, p.name, color)
                    if not p.command:
                        b.putChar(self.size.x - 4, self.subMenuIndicator)
                    elif p.param:
                        b.moveStr(self.size.x - 3 - len(p.param), p.param, color)
                self.writeBuf(0, y, self.size.x, 1, b)
                y += 1
        color = self.cNormal
        self.__frameLine(b, 5, color)
        self.writeBuf(0, y, self.size.x, 1, b)

    def getItemRect(self, item):
        """
        Returns the rectangle occupied by the given menu item. It can be used
        to determine if a mouse click has occurred on a given menu selection.

        :param item: Item to locate
        :return: `Rect` bounds of the item
        """
        y = list(self.menu.items).index(item) + 1
        r = Rect(2, y, self.size.x - 2, y + 1)
        return r

    def __frameLine(self, b, n, color):
        b.moveBuf(0, self.frameChars[n: n + 2], self.cNormal, 2)
        b.moveChar(2, self.frameChars[n + 2], color, self.size.x - 4)
        b.moveBuf(self.size.x - 2, self.frameChars[n + 3: n + 5], self.cNormal, 2)
