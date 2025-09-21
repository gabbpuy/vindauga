# -*- coding: utf-8 -*-
from gettext import gettext as _

from vindauga.constants.buttons import bfNormal, bfDefault
from vindauga.constants.command_codes import cmOK, cmCancel, cmScrollBarChanged
from vindauga.constants.event_codes import evMouseDown, meDoubleClick, evBroadcast, evCommand
from vindauga.constants.option_flags import ofSelectable, ofCentered
from vindauga.events.event import Event
from vindauga.events.event_queue import event_queue
from vindauga.types.draw_buffer import DrawBuffer
from vindauga.types.palette import Palette
from vindauga.types.rect import Rect
from vindauga.widgets.button import Button
from vindauga.widgets.check_boxes import CheckBoxes
from vindauga.widgets.dialog import Dialog
from vindauga.widgets.label import Label
from vindauga.widgets.scroll_bar import ScrollBar
from vindauga.widgets.static_text import StaticText


class ClickTester(StaticText):
    cpMousePalette = "\x07\x08"

    def __init__(self, r, text):
        super().__init__(r, text)
        self.clicked = False

    def getPalette(self) -> Palette:
        return Palette(self.cpMousePalette)

    def handleEvent(self, event: Event):
        super().handleEvent(event)

        if event.what == evMouseDown:
            if event.mouse.eventFlags & meDoubleClick:
                self.clicked = not self.clicked
                self.drawView()
            self.clearEvent(event)

    def draw(self):
        buf = DrawBuffer()
        c = self.getColor(int(self.clicked) + 1)
        buf.moveChar(0, ' ', c, self.size.x)
        buf.moveStr(0, self._text, c)
        self.writeLine(0, 0, self.size.x, 1, buf)


class MouseDialog(Dialog):
    def __init__(self):
        super().__init__(Rect(0, 0, 34, 12), _('Mouse options'))
        r = Rect(3, 4, 30, 5)
        self.options |= ofCentered
        self.mouseScrollBar = ScrollBar(r)
        self.mouseScrollBar.setParams(1, 1, 20, 20, 1)
        self.mouseScrollBar.options |= ofSelectable
        self.mouseScrollBar.setValue(event_queue.doubleDelay)
        self.insert(self.mouseScrollBar)

        r = Rect(2, 2, 21, 3)
        self.insert(Label(r, _('~M~ouse double click'), self.mouseScrollBar))

        r = Rect(3, 3, 30, 4)
        self.insert(ClickTester(r, _('Fast       Medium      Slow')))

        r = Rect(3, 6, 30, 7)
        self.insert(CheckBoxes(r, (_('~R~everse mouse buttons'),)))
        self.oldDelay = event_queue.doubleDelay

        r = Rect(9, 9, 19, 11)
        self.insert(Button(r, _('O~K~'), cmOK, bfDefault))

        r = Rect(21, 9, 31, 11)
        self.insert(Button(r, _('Cancel'), cmCancel, bfNormal))

        self.selectNext(False)

    def handleEvent(self, event: Event):
        super().handleEvent(event)
        if event.what == evCommand:
            if event.message.command == cmCancel:
                event_queue.doubleDelay = self.oldDelay
        elif event.what == evBroadcast:
            if event.message.command == cmScrollBarChanged:
                event_queue.doubleDelay = self.mouseScrollBar.value
                self.clearEvent(event)
