# -*- coding: utf-8 -*-
import logging

from vindauga.constants.colors import cmColorBackgroundChanged, cmColorForegroundChanged, cmColorSet, cmSetColorIndex
from vindauga.constants.event_codes import evBroadcast
from vindauga.misc.message import message
from vindauga.types.draw_buffer import DrawBuffer
from vindauga.types.rect import Rect
from vindauga.types.view import View

logger = logging.getLogger(__name__)


class ColorDisplay(View):
    """
    The interrelated classes `ColorItem`, `ColorGroup`, `ColorSelector`,
    `MonoSelector`, `ColorDisplay`, `ColorGroupList`,
    `ColorItemList` and `ColorDialog` provide viewers and dialog boxes
    from which the user can select and change the color assignments from
    available palettes with immediate effect on the screen.

    `ColorDisplay` is a view for displaying text so that the user can select a
    suitable palette.
    """
    name = 'ColorDisplay'

    def __init__(self, bounds: Rect, text: str):
        super().__init__(bounds)
        self._color = 0
        self._text = text
        self.eventMask |= evBroadcast

    def draw(self):
        c = self._color

        if not c:
            c = self.errorAttr

        b = DrawBuffer()
        for i in range((self.size.x // len(self._text)) + 1):
            b.moveStr(i * len(self._text), self._text, c)
        self.writeLine(0, 0, self.size.x, self.size.y, b)

    def handleEvent(self, event):
        super().handleEvent(event)

        if event.what == evBroadcast:
            emc = event.message.command
            if emc in {cmColorBackgroundChanged, cmColorForegroundChanged}:
                if event.message.command == cmColorBackgroundChanged:
                    self._color = (self._color & 0x0F) | ((event.message.infoPtr << 4) & 0xF0)
                elif event.message.command == cmColorForegroundChanged:
                    self._color = (self._color & 0xF0) | (event.message.infoPtr & 0x0F)
                message(self.owner, evBroadcast, cmSetColorIndex, self._color)
                self.drawView()

    def setColor(self, color):
        """
        Change the currently displayed color. Sets `self.color` to `color',
        broadcasts the change to the owning group, then calls `drawView()`.

        :param color: Color to set
        """
        self._color = color
        message(self.owner, evBroadcast, cmColorSet, self._color)
        self.drawView()
