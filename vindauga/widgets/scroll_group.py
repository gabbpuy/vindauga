# -*- coding: utf-8 -*-
import logging
from typing import Optional

from vindauga.constants.event_codes import evBroadcast
from vindauga.constants.command_codes import cmScrollBarChanged, cmReceivedFocus
from vindauga.constants.grow_flags import gfGrowHiX, gfGrowHiY
from vindauga.constants.state_flags import sfSelected, sfActive
from vindauga.constants.option_flags import ofSelectable
from vindauga.events.event import Event
from vindauga.types.group import Group
from vindauga.types.point import Point
from vindauga.types.rect import Rect
from vindauga.types.view import View

from .background import Background
from .scroll_bar import ScrollBar

logger = logging.getLogger(__name__)
sbHorizontalBar = 1
sbVerticalBar = 2


class ScrollGroup(Group):

    class ScrollInfo:
        delta: Point
        ignore: View

    def __init__(self, bounds: Rect, hScrollBar: Optional[ScrollBar], vScrollBar: Optional[ScrollBar]):
        super().__init__(bounds)
        self.hScrollBar = hScrollBar
        self.vScrollBar = vScrollBar
        self.background = None
        self.eventMask |= evBroadcast
        self.delta = Point(0, 0)
        self.limit = Point(0, 0)

        self.background = self.initBackground(self.getExtent())
        if self.background:
            self.background.growMode = gfGrowHiX | gfGrowHiY
            self.insert(self.background)

    @staticmethod
    def initBackground(r: Rect) -> Background:
        return Background(r, ' ')

    @staticmethod
    def doScroll(view: View, info: ScrollInfo):
        if view is not info.ignore:
            dest = view.origin + info.delta
            view.moveTo(dest.x, dest.y)

    def changeBounds(self, bounds: Rect):
        self.lock()
        try:
            super().changeBounds(bounds)
            self.setLimit(self.limit.x, self.limit.y)
        finally:
            self.unlock()
        self.drawView()

    def handleEvent(self, event: Event):
        super().handleEvent(event)
        if event.what == evBroadcast:
            if (event.message.command == cmScrollBarChanged and
                    (event.message.infoPtr in {self.hScrollBar, self.vScrollBar})):
                self.scrollDraw()
            elif (event.message.command == cmReceivedFocus and
                  self.firstThat(lambda view, args: view is args, event.message.infoPtr)):
                self.focusSubView(event.message.infoPtr)

    def scrollDraw(self):
        d = Point(0, 0)
        d.x = self.hScrollBar.value if self.hScrollBar else 0
        d.y = self.vScrollBar.value if self.vScrollBar else 0

        if d.x != self.delta.x or d.y != self.delta.y:
            info = self.ScrollInfo()
            info.delta = self.delta - d
            info.ignore = self.background
            self.lock()
            try:
                self.forEach(self.doScroll, info)
                self.delta = d
            finally:
                self.unlock()
            self.drawView()

    def scrollTo(self, x: int, y: int):
        self.lock()
        try:
            if self.hScrollBar and x != self.hScrollBar.value:
                self.hScrollBar.setValue(x)
            if self.vScrollBar and y != self.vScrollBar.value:
                self.vScrollBar.setValue(y)
        finally:
            self.unlock()
        self.scrollDraw()

    def setLimit(self, x: int, y: int):
        self.limit.x = x
        self.limit.y = y

        self.lock()
        try:
            if self.hScrollBar:
                self.hScrollBar.setParams(self.hScrollBar.value, 0, x - self.size.x, self.size.x - 1, 1)
            if self.vScrollBar:
                self.vScrollBar.setParams(self.vScrollBar.value, 0, y - self.size.y, self.size.y - 1, 1)
        finally:
            self.unlock()
        self.scrollDraw()

    def setState(self, state: int, enable: bool):
        super().setState(state, enable)
        if state & (sfActive | sfSelected):
            if self.hScrollBar:
                if enable:
                    self.hScrollBar.show()
                else:
                    self.hScrollBar.hide()
            if self.vScrollBar:
                if enable:
                    self.vScrollBar.show()
                else:
                    self.vScrollBar.hide()

    def focusSubView(self, view: View):
        rView = view.getBounds()
        r = self.getExtent()
        r.intersect(rView)
        if r != rView:
            dx = self.delta.x
            if view.origin.x < 0:
                dx = self.delta.x + view.origin.x
            elif view.origin.x + view.size.x > self.size.x:
                dx = self.delta.x + view.origin.x + view.size.x - self.size.x

            dy = self.delta.y
            if view.origin.y < 0:
                dy = self.delta.y + view.origin.y
            elif view.origin.y + view.size.y > self.size.y:
                dy = self.delta.y + view.origin.y + view.size.y - self.size.y
            self.scrollTo(dx, dy)

    def selectNext(self, forward: bool):
        # This logic should probably live in group so that groups of groups work.
        def selectableView(v: View) -> bool:
            logger.info('selectable(%s) - %s', v, v.options & ofSelectable)
            return bool(v.options & ofSelectable)

        if self.current and isinstance(self.current, Group):
            # If current child is itself a group then focus its next
            child = self.current.current
            last = self.current.firstThat(selectableView)  # self.current.first
            first = self.current.lastThat(selectableView)  # self.current.last
            self.current.selectNext(forward)
            # If we weren't on the boundary child then don't focus the next group item
            if child not in {first, last}:
                return
            if not ((child is first and forward) or (child is last and not forward)):
                return
            # Fall through. We're on the edge and rather than go in a circle, focus the next item in the scroll group
        super().selectNext(forward)
        # We moved groups make sure we focus the first or last item.
        if self.current and isinstance(self.current, Group):
            first = self.current.firstThat(selectableView)  # self.current.first
            last = self.current.lastThat(selectableView)  # self.current.last
            if forward:
                first.select()
            else:
                last.select()
        return
