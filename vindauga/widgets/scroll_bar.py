# -*- coding: utf-8 -*-
import logging

from vindauga.constants.command_codes import (cmScrollBarClicked, cmScrollBarChanged)
from vindauga.constants.scrollbar_codes import sbLeftArrow, sbRightArrow, sbPageLeft, sbPageRight, sbUpArrow, sbDownArrow, \
    sbPageUp, sbPageDown, sbIndicator
from vindauga.constants.grow_flags import gfGrowLoX, gfGrowLoY, gfGrowHiX, gfGrowHiY
from vindauga.constants.event_codes import evMouseDown, evBroadcast, evMouseAuto, evMouseMove, evKeyDown
from vindauga.constants.keys import (kbLeft, kbUp, kbRight, kbDown, kbCtrlLeft, kbCtrlRight, kbHome, kbEnd, kbPgUp,
                                     kbPgDn, kbCtrlPgUp, kbCtrlPgDn)
from vindauga.constants.state_flags import sfVisible
from vindauga.misc.message import message
from vindauga.misc.util import ctrlToArrow
from vindauga.types.draw_buffer import DrawBuffer
from vindauga.types.palette import Palette
from vindauga.types.rect import Rect
from vindauga.types.view import View

logger = logging.getLogger(__name__)


class ScrollBar(View):
    vChars = '▲▼▒■▓'
    hChars = '◄►▒■▓'
    name = 'ScrollBar'
    cpScrollBar = "\x04\x05\x05"

    def __init__(self, bounds):
        super().__init__(bounds)
        self.value = 0
        self.minVal = 0
        self.maxVal = 0
        self.pageStep = 1
        self.arrowStep = 1
        self.mouse = None
        self.extent = Rect(0, 0, 0, 0)

        if self.size.x == 1:
            self.growMode = gfGrowLoX | gfGrowHiX | gfGrowHiY
            self.chars = self.vChars
        else:
            self.growMode = gfGrowLoY | gfGrowHiX | gfGrowHiY
            self.chars = self.hChars

    def draw(self):
        self.drawPos(self.getPos())

    def getPalette(self):
        palette = Palette(self.cpScrollBar)
        return palette

    def handleEvent(self, event):
        """
        Handles scroll bar events by calling `handleEvent()`. Mouse
        events are broadcast to the scroll bar's owner, which must handle the
        implications of the scroll bar changes.

        `handleEvent()` also determines which scroll bar part has received a
        mouse click (or equivalent keystroke). Data member `value` is
        adjusted according to the current `arrowStep` or `pageStep` values.
        The scroll bar indicator is redrawn.

        :param event: The event to handle
        """
        tracking = False
        i = 0
        super().handleEvent(event)
        what = event.what

        if what == evMouseDown:
            message(self.owner, evBroadcast, cmScrollBarClicked, self)
            self.mouse = self.makeLocal(event.mouse.where)
            self.extent = self.getExtent()
            self.extent.grow(1, 1)
            p = self.getPos()
            s = self.getSize() - 1
            clickPart = self.__getPartCode(s, p)
            if clickPart != sbIndicator:
                mouseDown = True
                while mouseDown:
                    self.mouse = self.makeLocal(event.mouse.where)
                    if self.__getPartCode(s, p) == clickPart:
                        self.setValue(self.value + self.scrollStep(clickPart))
                    mouseDown = (self.mouseEvent(event, evMouseAuto))
            else:
                done = False
                while not done:
                    self.mouse = self.makeLocal(event.mouse.where)
                    tracking = self.mouse in self.extent
                    if tracking:
                        if self.size.x == 1:
                            i = self.mouse.y
                        else:
                            i = self.mouse.x

                        i = max(i, 1)
                        i = min(i, s - 1)
                    else:
                        i = self.getPos()

                    if i != p:
                        self.drawPos(i)

                    done = not (self.mouseEvent(event, evMouseMove))

                if tracking and s > 2:
                    s -= 2
                    self.setValue(((((p - 1) * (self.maxVal - self.minVal) +
                                     (s >> 1)) // s) + self.minVal))

            self.clearEvent(event)
        elif what == evKeyDown:
            if self.state & sfVisible:
                clickPart = sbIndicator
                if self.size.y == 1:
                    kc = ctrlToArrow(event.keyDown.keyCode)
                    if kc == kbLeft:
                        clickPart = sbLeftArrow
                    elif kc == kbRight:
                        clickPart = sbRightArrow
                    elif kc == kbCtrlLeft:
                        clickPart = sbPageLeft
                    elif kc == kbCtrlRight:
                        clickPart = sbPageRight
                    elif kc == kbHome:
                        i = self.minVal
                    elif kc == kbEnd:
                        i = self.maxVal
                    else:
                        return
                else:
                    kc = ctrlToArrow(event.keyDown.keyCode)
                    if kc == kbUp:
                        clickPart = sbUpArrow
                    elif kc == kbDown:
                        clickPart = sbDownArrow
                    elif kc == kbPgUp:
                        clickPart = sbPageUp
                    elif kc == kbPgDn:
                        clickPart = sbPageDown
                    elif kbCtrlPgUp:
                        i = self.minVal
                    elif kbCtrlPgDn:
                        i = self.maxVal
                    else:
                        return

                message(self.owner, evBroadcast, cmScrollBarClicked, self)
                if clickPart != sbIndicator:
                    i = self.value + self.scrollStep(clickPart)

                self.setValue(i)
                self.clearEvent(event)

    def scrollDraw(self):
        """
        Is called whenever `value` data member changes. This function defaults to sending a
        `cmScrollBarChanged` message to the scroll bar's owner:
        """
        message(self.owner, evBroadcast, cmScrollBarChanged, self)

    def scrollStep(self, part):
        """
        By default, `scrollStep()` returns a positive or negative step value,
        depending on the scroll bar part given by `part`, and the current
        values of `arrowStep` and `pageStep`. Parameter `part1 should be one
        of the following constants:
        ```
        Constant     Value Meaning
        sbLeftArrow  0     Left arrow of horizontal scroll bar
        sbRightArrow 1     Right arrow of horizontal scroll bar
        sbPageLeft   2     Left paging area of horizontal scroll bar
        sbPageRight  3     Right paging area of horizontal scroll bar
        sbUpArrow    4     Top arrow of vertical scroll bar
        sbDownArrow  5     Bottom arrow of vertical scroll bar
        sbPageUp     6     Upper paging area of vertical scroll bar
        sbPageDown   7     Lower paging area of vertical scroll bar
        sbIndicator  8     Position indicator on scroll bar
        ```

        These constants define the different areas of a `ScrollBar` in which the
        mouse can be clicked. The `scrollStep()` function converts these constants
        into actual scroll step values.

        Although defined, the `sbIndicator` constant is never passed to `scrollStep()`.

        :param part: Part of the scroll bar interacted with
        :return: Step value of the scroll bar
        """
        if not (part & 2):
            step = self.arrowStep
        else:
            step = self.pageStep

        if not (part & 1):
            return -step
        return step

    def setParams(self, value, minVal, maxVal, pageStep, arrowStep):
        """
        Sets the `value`, `minVal`, `maxVal`, `pageStep` and `arrowStep`
        with the given argument values. Some adjustments are made
        if your arguments conflict.

        The scroll bar is redrawn by calling `drawView()`. If value is
        changed, `scrollDraw()` is also called.

        :param value: Value (position) of scroll bar
        :param minVal: Minimum scroll bar position
        :param maxVal: Maximum scroll bar position
        :param pageStep: Page click step value
        :param arrowStep: Arrow click step value
        """
        maxVal = max(maxVal, minVal)
        value = max(minVal, value)
        value = min(maxVal, value)
        sValue = self.value

        if sValue != value or self.minVal != minVal or self.maxVal != maxVal:
            self.value = value
            self.minVal = minVal
            self.maxVal = maxVal
            self.drawView()
            if sValue != value:
                self.scrollDraw()

        self.pageStep = pageStep
        self.arrowStep = arrowStep

    def setRange(self, minVal, maxVal):
        """
        Sets the legal range for `value` by setting `minVal` and `maxVal`
        to the given arguments `minVal` and `maxVal`.

        Calls `setParams()`, so `drawView()` and `scrollDraw()` will
        be called if the changes require the scroll bar to be redrawn.

        :param minVal: Minimum scroll bar position
        :param maxVal: Maximum scroll bar position
        """
        self.setParams(self.value, minVal, maxVal, self.pageStep, self.arrowStep)

    def setStep(self, pageStep, arrowStep):
        """
        Sets `pageStep` and `arrowStep` to the given arguments `pageStep` and `arrowStep`.
        Calls `setParams()` with the other arguments set to their current values.

        :param pageStep: Page click step value
        :param arrowStep: Arrow click step value
        """
        self.setParams(self.value, self.minVal, self.maxVal, pageStep, arrowStep)

    def setValue(self, value):
        """
        Sets `value` to `value` by calling `setParams()` with the other
        arguments set to their current values.

        Note: `drawView()` and `scrollDraw()` will be called if this call changes value.

        :param value: Value (position) of the scroll bar
        """
        self.setParams(value, self.minVal, self.maxVal, self.pageStep, self.arrowStep)

    def drawPos(self, pos):
        b = DrawBuffer()
        s = self.getSize() - 1
        b.moveChar(0, self.chars[0], self.getColor(2), 1)

        if self.maxVal == self.minVal:
            b.moveChar(1, self.chars[4], self.getColor(1), s - 1)
        else:
            b.moveChar(1, self.chars[2], self.getColor(1), s - 1)
            b.moveChar(pos, self.chars[3], self.getColor(3), 1)

        b.moveChar(s, self.chars[1], self.getColor(2), 1)
        self.writeBuf(0, 0, self.size.x, self.size.y, b)

    def getPos(self):
        r = self.maxVal - self.minVal

        if r == 0:
            return 1
        return ((((self.value - self.minVal) * (self.getSize() - 3)) + (r >> 1)) // r) + 1

    def getSize(self):
        if self.size.x == 1:
            s = self.size.y
        else:
            s = self.size.x

        return max(2, s)

    def __getPartCode(self, size, pos):
        part = -1

        if self.mouse in self.extent:
            mark = self.mouse.y if self.size.x == 1 else self.mouse.x

            if (self.size.x == 1 and self.size.y == 2) or (self.size.x == 2 and self.size.y == 1):
                if mark < 1:
                    part = sbLeftArrow
                elif mark == pos:
                    part = sbRightArrow
            else:
                if mark == pos:
                    part = sbIndicator
                else:
                    if mark < 1:
                        part = sbLeftArrow
                    elif mark < pos:
                        part = sbPageLeft
                    elif mark < size:
                        part = sbPageRight
                    else:
                        part = sbRightArrow

                    if self.size.x == 1:
                        part += 4
        return part
