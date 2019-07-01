# -*- coding: utf-8 -*-
from vindauga.constants.command_codes import cmScrollBarChanged
from vindauga.constants.event_codes import evBroadcast
from vindauga.constants.option_flags import ofSelectable
from vindauga.constants.state_flags import sfActive, sfSelected
from vindauga.types.palette import Palette
from vindauga.types.point import Point
from vindauga.types.view import View


class Scroller(View):
    """
    `Scroller` provides a scrolling virtual window onto a larger view. That is,
    a scrolling view lets the user scroll a large view within a clipped
    boundary.

    The scroller provides an offset from which the `draw()` method
    fills the visible region. All methods needed to provide both scroll bar
    and keyboard scrolling are built into `Scroller`.

    The basic scrolling view provides a useful starting point for scrolling
    views such as text views.
    """
    name = "Scroller"
    cpScroller = "\x06\x07"

    def __init__(self, bounds, hScrollBar, vScrollBar):
        super().__init__(bounds)
        self._drawLock = 0
        self._drawFlag = False
        self._hScrollBar = hScrollBar
        self._vScrollBar = vScrollBar

        self._limit = Point()
        self.delta = Point()

        self.options |= ofSelectable
        self.eventMask |= evBroadcast

    def changeBounds(self, bounds):
        """
        Changes the scroller's size by calling `setbounds()`. If
        necessary, the scroller and scroll bars are then redrawn by calling
        `setLimit()` and `drawView()`.

        :param bounds: Bounds to change to
        """
        self.setBounds(bounds)
        self._drawLock += 1
        self.setLimit(self._limit.x, self._limit.y)
        self._drawLock -= 1
        self._drawFlag = False
        self.drawView()

    def checkDraw(self):
        """
        If `drawLock` is zero and `drawFlag` is True, `drawFlag` is set to False
        and `drawView()` is called.

        If `drawLock` is non-zero or `drawFlag` is False, `checkDraw()`
        does nothing.

        Methods `scrollTo()` and `setLimit()` each call `checkDraw()` so
        that `drawView()` is only called if needed.
        """
        if self._drawLock == 0 and self._drawFlag:
            self._drawFlag = False
            self.drawView()

    def getPalette(self):
        palette = Palette(self.cpScroller)
        return palette

    def handleEvent(self, event):
        """
        Handles most events by calling `super()handleEvent()`.

        Broadcast events such as `cmScrollBarChanged` from either `hScrollBar`
        or `vScrollBar` result in a call to `scrollDraw()`.

        :param event: Event to handle
        """
        super().handleEvent(event)
        if (event.what == evBroadcast and
                event.message.command == cmScrollBarChanged and
                (event.message.infoPtr in {self._hScrollBar, self._vScrollBar})):
            self.scrollDraw()

    def scrollDraw(self):
        """
        Checks to see if `delta` matches the current positions of the scroll
        bars. If not, `delta` is set to the correct value and `drawView()` is called to
        redraw the scroller.
        """
        d = Point()

        if self._hScrollBar:
            d.x = self._hScrollBar.value
        else:
            d.x = 0

        if self._vScrollBar:
            d.y = self._vScrollBar.value
        else:
            d.y = 0

        if d.x != self.delta.x or d.y != self.delta.y:
            self.setCursor(self.cursor.x + self.delta.x - d.x,
                           self.cursor.y + self.delta.y - d.y)
            self.delta = d
            if self._drawLock:
                self._drawFlag = True
            else:
                self.drawView()

    def scrollTo(self, x, y):
        """
        Sets the scroll bars to (x,y) by calling `hScrollBar.setValue(x)` and
        `vScrollBar.setValue(y)` and redraws the view by calling `drawView()`.

        :param x: X position
        :param y: Y position
        """
        self._drawLock += 1

        if self._hScrollBar:
            self._hScrollBar.setValue(x)
        if self._vScrollBar:
            self._vScrollBar.setValue(y)
        self._drawLock -= 1
        self.checkDraw()

    def setLimit(self, x, y):
        """
        Sets the `limit` data member and redraws the scrollbars and scroller if necessary.

        :param x: X limit
        :param y: Y limit
        """
        self._limit.x = x
        self._limit.y = y

        self._drawLock += 1
        if self._hScrollBar:
            self._hScrollBar.setParams(self._hScrollBar.value,
                                       0, x - self.size.x, self.size.x - 1,
                                       self._hScrollBar.arrowStep)
        if self._vScrollBar:
            self._vScrollBar.setParams(self._vScrollBar.value,
                                       0, y - self.size.y, self.size.y - 1,
                                       self._vScrollBar.arrowStep)

        self._drawLock -= 1
        self.checkDraw()

    def setState(self, state, enable):
        """
        This member function is called whenever the scroller's state changes.
        Calls `super().setState()` to set or clear the state flags in state`.

        If the new `state` is `sfSelected` and `sfActive`, `setState()`
        displays the scroll bars; otherwise, they are hidden.

        :param state: State to set
        :param enable: Enable or disable
        """
        super().setState(state, enable)

        if state & (sfActive | sfSelected):
            self.__showScrollbar(self._hScrollBar)
            self.__showScrollbar(self._vScrollBar)

    def shutdown(self):
        self._hScrollBar = None
        self._vScrollBar = None
        super().shutdown()

    def __showScrollbar(self, scrollbar):
        if scrollbar:
            if self.getState(sfActive | sfSelected):
                scrollbar.show()
            else:
                scrollbar.hide()
