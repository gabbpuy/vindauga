# -*- coding: utf-8 -*-
from vindauga.constants.scrollbar_codes import sbHorizontal, sbVertical, sbHandleKeyboard
from vindauga.constants.grow_flags import gfGrowHiX, gfGrowHiY
from vindauga.constants.event_codes import evKeyDown
from vindauga.constants.keys import kbTab, kbShiftTab
from vindauga.events.event import Event
from vindauga.types.rect import Rect

from vindauga.widgets.dialog import Dialog
from vindauga.widgets.scroll_group import ScrollGroup, sbHorizontalBar, sbVerticalBar


class ScrollDialog(Dialog):
    def __init__(self, bounds: Rect, title: str, flags: int):
        super().__init__(bounds, title)
        self.hScrollBar = None
        self.vScrollBar = None

        if flags & sbHorizontalBar:
            self.hScrollBar = self.standardScrollBar(sbHorizontal | sbHandleKeyboard)
        if flags & sbVerticalBar:
            self.vScrollBar = self.standardScrollBar(sbVertical | sbHandleKeyboard)

        r = self.getExtent()
        r.grow(-1, -1)
        self.scrollGroup = ScrollGroup(r, self.hScrollBar, self.vScrollBar)
        self.scrollGroup.growMode = gfGrowHiY | gfGrowHiX
        self.insert(self.scrollGroup)

    def handleEvent(self, event: Event):
        if event.what == evKeyDown and event.keyDown.keyCode in {kbTab, kbShiftTab}:
            self.scrollGroup.selectNext(event.keyDown.keyCode == kbShiftTab)
            self.clearEvent(event)
        super().handleEvent(event)
