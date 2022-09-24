# -*- coding: utf-8 -*-
from enum import IntEnum
import logging

from vindauga.constants.colors import cmColorForegroundChanged, cmColorBackgroundChanged, cmColorSet
from vindauga.constants.event_codes import evBroadcast, evMouseDown, evKeyDown, evMouseMove
from vindauga.constants.keys import kbLeft, kbRight, kbDown, kbUp
from vindauga.constants.option_flags import ofSelectable, ofFirstClick, ofFramed
from vindauga.events.event import Event
from vindauga.misc.cp437 import cp437ToUnicode
from vindauga.misc.message import message
from vindauga.misc.util import ctrlToArrow
from vindauga.types.draw_buffer import DrawBuffer
from vindauga.types.rect import Rect
from vindauga.types.view import View

logger = logging.getLogger(__name__)


class ColorSel(IntEnum):
    csBackground = 0
    csForeground = 1


class ColorSelector(View):
    """
    The interrelated classes `ColorItem`, `ColorGroup`, `ColorSelector`,
    `MonoSelector`, `ColorDisplay`, `ColorGroupList`, `ColorItemList` and
    `ColorDialog` provide viewers and dialog boxes from which the user can
    select and change the color assignments from available palettes with
    immediate effect on the screen.

    `ColorSelector` is a view for displaying the color selections available.
    """
    icon = '○'
    icon_reversed = '◙'
    name = 'ColorSelector'

    def __init__(self, bounds: Rect, selectorType: ColorSel):
        super().__init__(bounds)
        self.options |= (ofSelectable | ofFirstClick | ofFramed)
        self.eventMask |= evBroadcast
        self._selectorType = selectorType
        self._color = 0

    def draw(self):
        b = DrawBuffer()
        b.moveChar(0, ' ', 0x70, self.size.x)
        for y in range(self.size.y + 1):
            if y < 4:
                for x in range(4):
                    c = y * 4 + x
                    b.moveChar(x * 3, self.icon, c, 3)
                    if c == self._color:
                        b.putChar(x * 3 + 1, self.icon_reversed)
                        if c == 0:
                            b.putAttribute(x * 3 + 1, 0x70)

            self.writeLine(0, y, self.size.x, 1, b)

    def handleEvent(self, event: Event):
        """
        Handles mouse and key events: you can click on a given color indicator
        to select that color, or you can select colors by positioning the
        cursor with the arrow keys.
       
        Changes invoke `drawView()` when appropriate.

        :param event: Event to handle
        """
        width = 4
        super().handleEvent(event)

        oldColor = self._color
        maxCol = [7, 15][self._selectorType]

        what = event.what
        if what == evMouseDown:
            self.__handleMouseEvent(event, oldColor)
        elif what == evKeyDown:
            key = ctrlToArrow(event.keyDown.keyCode)
            if key in {kbLeft, kbRight, kbUp, kbDown}:
                if self.__handleKeyDownEvent(key, maxCol, width):
                    self.clearEvent(event)
        elif what == evBroadcast:
            self.__handleBroadcastEvent(event)

    def __colorChanged(self):
        """
        Send a message to indicate color has changed
        """
        if self._selectorType == ColorSel.csForeground:
            msg = cmColorForegroundChanged
        else:
            msg = cmColorBackgroundChanged

        message(self.owner, evBroadcast, msg, self._color)

    def __handleBroadcastEvent(self, event: Event):
        if event.message.command == cmColorSet:
            if self._selectorType == ColorSel.csBackground:
                self._color = event.message.infoPtr >> 4
            else:
                self._color = event.message.infoPtr & 0x0f
            self.drawView()

    def __handleKeyDownEvent(self, key, maxCol, width):
        if key == kbLeft:
            if self._color > 0:
                self._color -= 1
            else:
                self._color = maxCol
        elif key == kbRight:
            if self._color < maxCol:
                self._color += 1
            else:
                self._color = 0
        elif key == kbUp:
            if self._color > width - 1:
                self._color -= width
            elif self._color == 0:
                self._color = maxCol
            else:
                self._color += maxCol - width
        elif key == kbDown:
            if self._color < maxCol - (width - 1):
                self._color += width
            elif self._color == maxCol:
                self._color = 0
            else:
                self._color -= maxCol - width
        else:
            return
        self.__colorChanged()
        self.drawView()
        return True

    def __handleMouseEvent(self, event, oldColor):
        mousing = True
        while mousing:
            if self.mouseInView(event.mouse.where):
                mouse = self.makeLocal(event.mouse.where)
                self._color = mouse.y * 4 + mouse.x // 3
            else:
                self._color = oldColor
            self.__colorChanged()
            self.drawView()
            mousing = self.mouseEvent(event, evMouseMove)
        self.__colorChanged()
        self.drawView()
        self.clearEvent(event)
