# -*- coding: utf-8 -*-
import logging

from vindauga.constants.command_codes import (wpBlueWindow, cmClose, cmResize, cmCancel, cmZoom,
                                              cmSelectWindowNum,
                                              cmNext, cmPrev)
from vindauga.constants.scrollbar_codes import sbVertical, sbHandleKeyboard
from vindauga.constants.window_flags import wfMove, wfGrow, wfClose, wfZoom
from vindauga.constants.grow_flags import gfGrowAll, gfGrowRel
from vindauga.constants.event_codes import evCommand, evKeyDown, evBroadcast
from vindauga.constants.keys import kbTab, kbShiftTab
from vindauga.constants.option_flags import ofSelectable, ofTopSelect, ofPostProcess
from vindauga.constants.state_flags import sfShadow, sfActive, sfSelected, sfModal
from vindauga.types.command_set import CommandSet
from vindauga.types.group import Group
from vindauga.types.palette import Palette
from vindauga.types.point import Point
from vindauga.types.rect import Rect
from vindauga.types.view import View
from .frame import Frame
from .scroll_bar import ScrollBar

logger = logging.getLogger(__name__)
minWinSize = Point(16, 6)


class Window(Group):
    """
    A `Window` object is a specialized group that typically owns a `Frame`
    object, an interior `Scroller` object, and one or two `ScrollBar` objects.
    These attached subviews provide the "visibility" to the `Window` object.
    """

    name = 'Window'
    cpBlueWindow = '\x08\x09\x0A\x0B\x0C\x0D\x0E\x0F'
    cpCyanWindow = '\x10\x11\x12\x13\x14\x15\x16\x17'
    cpGrayWindow = '\x18\x19\x1A\x1B\x1C\x1D\x1E\x1F'

    def __init__(self, bounds, title, windowNumber):
        super().__init__(bounds)

        self.flags = (wfMove | wfGrow | wfClose | wfZoom)
        self.zoomRect = self.getBounds()
        self.number = windowNumber
        self.palette = wpBlueWindow
        self.title = title

        self.state |= sfShadow
        self.options |= ofSelectable | ofTopSelect
        self.growMode = gfGrowAll | gfGrowRel

        frame = self.initFrame(self.getExtent())
        if frame:
            self.frame = frame
            self.insert(self.frame)

    def close(self):
        if self.valid(cmClose):
            self.destroy(self)

    def shutdown(self):
        self.frame = None
        super().shutdown()

    def getPalette(self):
        blue = Palette(self.cpBlueWindow)
        cyan = Palette(self.cpCyanWindow)
        gray = Palette(self.cpGrayWindow)

        palettes = (blue, cyan, gray)

        return palettes[self.palette]

    def getTitle(self, *args):
        return self.title

    def handleEvent(self, event):
        """
        First calls `super().handleEvent()`, and then handles events
        specific to a `Window` as follows:

        * The following `evCommand` events are handled if the `flags`
          data member permits that operation:
          * `cmResize` (move or resize the window using the `dragView()`
            member function);
          * `cmClose` (close the window by creating a `cmCancel` event);
          * `cmZoom` (zoom the window using the `zoom()` member function).
        * `evKeyDown` events with a keyCode value of `kbTab` or `kbShiftTab`
          are handled by selecting the next or previous selectable subview (if
          any).
        * An `evBroadcast` event with a command value of `cmSelectWindowNum`
          is handled by selecting the window if the `event.infoPtr' data
          member is equal to `number` data member.

        :param event: Event to be handled
        """
        super().handleEvent(event)

        if event.what == evCommand:
            emc = event.message.command

            if emc == cmResize:
                if self.flags & (wfMove | wfGrow):
                    minBounds = Point()
                    maxBounds = Point()
                    limits = self.owner.getExtent()
                    self.sizeLimits(minBounds, maxBounds)
                    self.dragView(event, self.dragMode | (self.flags & (wfMove | wfGrow)), limits, minBounds, maxBounds)
                    self.clearEvent(event)
            if emc == cmClose:
                if self.flags & wfClose and event.message.infoPtr in {None, self}:
                    self.clearEvent(event)
                    if not self.state & sfModal:
                        self.close()
                    else:
                        event.what = evCommand
                        event.message.command = cmCancel
                        self.putEvent(event)
                        self.clearEvent(event)
            if emc == cmZoom:
                if self.flags & wfZoom and event.message.infoPtr in {None, self}:
                    self.zoom()
                    self.clearEvent(event)
        elif event.what == evKeyDown:
            kc = event.keyDown.keyCode
            if kc == kbTab:
                self.focusNext(False)
                self.clearEvent(event)
            elif kc == kbShiftTab:
                # TODO: Modern terminals send \e[Z for shift tab
                self.focusNext(True)
                self.clearEvent(event)
        elif (event.what == evBroadcast and event.message.command == cmSelectWindowNum and
              event.message.infoPtr == self.number and (self.options & ofSelectable)):
            self.select()
            self.clearEvent(event)

    @staticmethod
    def initFrame(bounds):
        """
        Creates a `Frame` object for the window and returns it,
        it should never be called directly. You can override
        `initFrame()` to instantiate a user-defined class derived from
        `Frame` instead of the standard `Frame`.

        :param bounds: The bounds of the containing window
        :return: a `Frame` instance
        """
        return Frame(bounds)

    def setState(self, state, enable):
        """
        First calls `super().setState(state, enable)`. Then, if `state` is
        equal to `sfSelected`, activates or deactivates the window and all
        its subviews using a call to `setState(sfActive, enable)`, and calls
        `enableCommands()` or `disableCommands()` for `cmNext`, `cmPrev`,
        `cmResize`, `cmClose` and `cmZoom`.

        :param state: State to modify
        :param enable: Enable or disable
        """
        super().setState(state, enable)

        windowCommands = CommandSet()

        if state & sfSelected:
            self.setState(sfActive, enable)
            if self.frame:
                self.frame.setState(sfActive, enable)

            windowCommands += cmNext
            windowCommands += cmPrev

            if self.flags & (wfGrow | wfMove):
                windowCommands += cmResize

            if self.flags & wfClose:
                windowCommands += cmClose

            if self.flags & wfZoom:
                windowCommands += cmZoom

            if enable:
                View.enableCommands(windowCommands)
            else:
                View.disableCommands(windowCommands)

    def standardScrollBar(self, options):
        r = self.getExtent()
        if options & sbVertical:
            r = Rect(r.bottomRight.x - 1, r.topLeft.y + 1, r.bottomRight.x, r.bottomRight.y - 1)
        else:
            r = Rect(r.topLeft.x + 2, r.bottomRight.y - 1, r.bottomRight.x - 2, r.bottomRight.y)

        s = ScrollBar(r)
        self.insert(s)
        if options & sbHandleKeyboard:
            s.options |= ofPostProcess
        return s

    def sizeLimits(self, minLimit, maxLimit):
        super().sizeLimits(minLimit, maxLimit)
        minLimit.x = minWinSize.x
        minLimit.y = minWinSize.y

    def zoom(self):
        minSize = Point()
        maxSize = Point()

        self.sizeLimits(minSize, maxSize)

        if self.size != maxSize:
            self.zoomRect = self.getBounds()
            r = Rect(0, 0, maxSize.x, maxSize.y)
            self.locate(r)
        else:
            self.locate(self.zoomRect)
