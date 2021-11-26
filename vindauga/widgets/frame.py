# -*- coding: utf-8 -*-
import logging

from vindauga.constants.command_codes import (wnNoNumber,
                                              cmClose, cmZoom)
from vindauga.constants.drag_flags import dmDragMove, dmDragGrow
from vindauga.constants.window_flags import wfMove, wfGrow, wfClose, wfZoom
from vindauga.constants.grow_flags import gfGrowHiX, gfGrowHiY
from vindauga.constants.event_codes import evBroadcast, evMouseUp, evMouseDown, evMouse, evCommand, meDoubleClick
from vindauga.constants.option_flags import ofFramed
from vindauga.constants.state_flags import sfVisible, sfActive, sfDragging
from vindauga.misc.util import nameLength
from vindauga.types.draw_buffer import DrawBuffer
from vindauga.types.palette import Palette
from vindauga.types.point import Point
from vindauga.types.view import View
from vindauga.widgets.scroll_group import ScrollGroup

logger = logging.getLogger(__name__)


class Frame(View):
    name = "Frame"

    initFrame = "\x06\x0A\x0C\x05\x00\x05\x03\x0A\x09\x16\x1A\x1C\x15\x00\x15\x13\x1A\x19"
    frameChars = '   └ │┌├ ┘─┴┐┤┬┼   ╚ ║╔╟ ╝═╧╗╢╤ '

    closeIcon = '[~X~]'
    zoomIcon = '[~↕~]'
    unZoomIcon = '[~↓~]'
    dragIcon = '~─┘~'
    cpFrame = "\x01\x01\x02\x02\x03"

    def __init__(self, bounds):
        super().__init__(bounds)
        self.growMode = gfGrowHiX + gfGrowHiY
        self.eventMask |= (evBroadcast | evMouseUp)

    def draw(self):
        """
        Draws the frame with color attributes and icons appropriate to the
        current state flags: active, inactive, being dragged. Adds zoom, close
        and resize icons depending on the owner window's flags. Adds the title,
        if any, from the owning window's title data member.

        Active windows are drawn with a double-lined frame and any icons;
        inactive windows are drawn with a single-lined frame and no icons.
        """
        f = 0
        drawable = DrawBuffer()
        if self.state & sfDragging:
            cFrame = 0x0505
            cTitle = 0x0005
        elif not (self.state & sfActive):
            cFrame = 0x0101
            cTitle = 0x0002
        else:
            cFrame = 0x0503
            cTitle = 0x0004
            f = 9

        cFrame = self.getColor(cFrame)
        cTitle = self.getColor(cTitle)

        width = self.size.x
        lineLength = width - 10

        if self.owner.flags & (wfClose | wfZoom):
            lineLength -= 6

        self.__frameLine(drawable, 0, f, cFrame & 0xFF)

        if self.owner.number != wnNoNumber and self.owner.number < 10:
            lineLength -= 4
            if self.owner.flags & wfZoom:
                i = 7
            else:
                i = 3
            drawable.putChar(width - i, chr(self.owner.number + ord('0')))

        if self.owner:
            title = self.owner.getTitle(lineLength)
            if title:
                lineLength = min(len(title), width - 10)  # min(nameLength(title), width - 10)
                lineLength = max(lineLength, 0)
                i = (width - lineLength) >> 1
                drawable.putChar(i - 1, ' ')
                drawable.moveBuf(i, title, cTitle, lineLength)
                drawable.putChar(i + lineLength, ' ')

        if self.state & sfActive:
            if self.owner.flags & wfClose:
                drawable.moveCStr(2, self.closeIcon, cFrame)
            if self.owner.flags & wfZoom:
                minSize = Point()
                maxSize = Point()
                self.owner.sizeLimits(minSize, maxSize)
                if self.owner.size == maxSize:
                    drawable.moveCStr(width - 5, self.unZoomIcon, cFrame)
                else:
                    drawable.moveCStr(width - 5, self.zoomIcon, cFrame)

        self.writeLine(0, 0, self.size.x, 1, drawable)

        for i in range(1, self.size.y - 1):
            self.__frameLine(drawable, i, f + 3, cFrame)
            self.writeLine(0, i, self.size.x, 1, drawable)

        self.__frameLine(drawable, self.size.y - 1, f + 6, cFrame)

        if self.state & sfActive:
            if self.owner.flags & wfGrow:
                drawable.moveCStr(width - 2, self.dragIcon, cFrame)

        self.writeLine(0, self.size.y - 1, self.size.x, 1, drawable)

    def getPalette(self):
        palette = Palette(self.cpFrame)
        return palette

    def handleEvent(self, event):
        """
        Calls `super().handleEvent()`, then handles mouse events.

        If the mouse is clicked on the close icon, `handleEvent()`
        generates a `cmClose` event. Clicking on the zoom icon or double-clicking
        on the top line of the frame generates a `cmZoom` event.

        Dragging the top line of the frame moves the window, and dragging the
        resize icon moves the lower right corner of the view and therefore
        changes its size.

        :param event: Event to process
        """
        super().handleEvent(event)
        if event.what == evMouseDown:
            mouse = self.makeLocal(event.mouse.where)
            if mouse.y == 0:
                if self.owner.flags & wfClose and self.state & sfActive and 2 <= mouse.x <= 4:
                    while self.mouseEvent(event, evMouse):
                        pass
                    mouse = self.makeLocal(event.mouse.where)
                    if mouse.y == 0 and 2 <= mouse.x <= 4:
                        event.what = evCommand
                        event.message.command = cmClose
                        event.message.infoPtr = self.owner
                        self.putEvent(event)
                        self.clearEvent(event)
                else:
                    if (self.owner.flags & wfZoom and (self.state & sfActive) and
                            (self.size.x - 5 <= mouse.x <= self.size.x - 3) or (
                                    event.mouse.eventFlags & meDoubleClick)):
                        event.what = evCommand
                        event.message.command = cmZoom
                        event.message.infoPtr = self.owner
                        self.putEvent(event)
                        self.clearEvent(event)
                    else:
                        if self.owner.flags & wfMove:
                            self.__dragWindow(event, dmDragMove)
                            self.clearEvent(event)
            else:
                if ((mouse.x >= self.size.x - 2 and mouse.y >= self.size.y - 1 and self.state & sfActive) and
                        self.owner.flags & wfGrow):
                    self.__dragWindow(event, dmDragGrow)
                    self.clearEvent(event)

    def setState(self, state, enable):
        """
        Changes the state of the frame.
        Calls `super().setState(state, enable)`. If the new state is
        `sfActive` or `sfDragging`, calls `super().drawView()` to
        redraw the view.

        :param state: State to set
        :param enable: Enable or disable state
        """
        super().setState(state, enable)
        if state & (sfActive | sfDragging):
            self.drawView()

    def __frameLine(self, frameBuf, y, n, color):
        """
        Explanation of the masks

                Bit 0 (1)
                  |
        Bit 3(8) -+- Bit 1 (2)
                  |
                Bit 2 (4)


        If e.g. it is to be guaranteed that a left upper corner is present in
        the sample, one takes: MASK | = 0x06.
        """

        # Build a line... +--- ... ---+
        frameMask = [self.initFrame[n]] + [self.initFrame[n + 1]] * (self.size.x - 2) + [self.initFrame[n + 2]]
        frameMask = [ord(f) for f in frameMask]

        children = (c for c in self.owner.children if c.options & ofFramed and c.state & sfVisible)

        for child in children:

            if child is self:
                break

            if y + 1 < child.origin.y:
                continue
            elif y + 1 == child.origin.y:
                mask1 = 0x0A
                mask2 = 0x06
            elif y == child.origin.y + child.size.y:
                mask1 = 0x0A
                mask2 = 0x03
            elif y < child.origin.y + child.size.y:
                mask1 = 0
                mask2 = 0x05
            else:
                continue

            xMin = max(1, child.origin.x)
            xMax = min(self.size.x - 1, child.origin.x + child.size.x)

            if xMax > xMin:
                if mask1 == 0:
                    frameMask[xMin - 1] |= mask2
                    frameMask[xMax] |= mask2
                else:
                    frameMask[xMin - 1] |= mask2
                    frameMask[xMax] |= (mask2 ^ mask1)
                    for i in range(xMin, xMax):
                        frameMask[i] |= mask1

        line = ''.join(self.frameChars[frameMask[i]] for i in range(self.size.x))
        frameBuf.moveStr(0, line, color)

    def __dragWindow(self, event, mode):
        minBounds = Point()
        maxBounds = Point()

        limits = self.owner.owner.getExtent()
        self.owner.sizeLimits(minBounds, maxBounds)
        self.owner.dragView(event, self.owner.dragMode | mode, limits, minBounds, maxBounds)
        self.clearEvent(event)
