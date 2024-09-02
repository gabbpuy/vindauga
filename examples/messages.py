# -*- coding: utf-8 -*-
import logging

from vindauga.constants.command_codes import cmClose, cmQuit, hcNoContext
from vindauga.constants.buttons import bfDefault
from vindauga.constants.event_codes import evBroadcast, evKeyDown, evCommand
from vindauga.constants.keys import kbUp, kbDown, kbAltX, kbAltF3, kbAltN, kbAltI
from vindauga.events.event import Event
from vindauga.types.collections.string_collection import StringCollection
from vindauga.menus.sub_menu import SubMenu
from vindauga.menus.menu_bar import MenuBar
from vindauga.menus.menu_item import MenuItem
from vindauga.misc.message import message
from vindauga.types.draw_buffer import DrawBuffer
from vindauga.types.rect import Rect
from vindauga.types.status_def import StatusDef
from vindauga.types.status_item import StatusItem
from vindauga.types.view import View
from vindauga.widgets.application import Application
from vindauga.widgets.button import Button
from vindauga.widgets.dialog import Dialog
from vindauga.widgets.list_box import ListBox
from vindauga.widgets.program import Program
from vindauga.widgets.scroll_bar import ScrollBar
from vindauga.widgets.status_line import StatusLine
from vindauga.widgets.window import Window

data = (
    "one", "two", "three", "four", "five",
    "six", "seven", "eight", "nine", "ten"
)

cmTechInfo = 101
cmNewData = 102
logger = logging.getLogger('vindauga.demos.messages')


class MyCollection(StringCollection):
    def __init__(self, items):
        super().__init__(items)


class TechInfoList(ListBox):
    def __init__(self, bounds: Rect, numCols: int, vScrollbar: ScrollBar):
        r = Rect(bounds.topLeft.x, bounds.topLeft.y, bounds.bottomRight.x, bounds.bottomRight.y)
        r.topLeft.x += 2
        r.topLeft.y += 1
        r.bottomRight.x -= 3
        r.bottomRight.y -= 2
        super().__init__(r, numCols, vScrollbar)
        self.tc = MyCollection(data)
        self.newList(self.tc)

    def handleEvent(self, event: Event):
        logger.info('handleEvent(event)')
        if event.what == evKeyDown:
            logger.info('%s %s', self.focused, self.tc)
            if event.keyDown.keyCode == kbUp:
                message(Program.desktop, evBroadcast, cmNewData,
                        self.tc[self.focused - 1 if self.focused > 0 else self.focused])
            elif event.keyDown.keyCode == kbDown:
                message(Program.desktop, evBroadcast, cmNewData,
                        self.tc[self.focused + 1 if self.focused < len(self.tc) - 1 else self.focused])
        super().handleEvent(event)


class TechInfoDialog(Dialog):
    def __init__(self, bounds: Rect):
        super().__init__(bounds, 'Data ListBox')
        t = self.getExtent()
        t.topLeft.x += 1
        t.topLeft.y += 1
        t.bottomRight.x -= 1
        t.bottomRight.y -= 2
        sb = ScrollBar(Rect(t.bottomRight.x - 2, t.topLeft.y + 1, t.bottomRight.x - 1, t.bottomRight.y - 2))
        self.insert(sb)
        self.insert(TechInfoList(t, 1, sb))
        self.insert(Button(Rect(10, t.bottomRight.y - 1, 20, t.bottomRight.y + 1), '~O~k', cmClose, bfDefault))


class TechInfoView(View):
    def __init__(self, bounds):
        super().__init__(bounds)
        self.eventMask |= evBroadcast
        self.curMessage = 'Press Up or Down Arrow'

    def handleEvent(self, event: Event):
        super().handleEvent(event)
        if event.what == evBroadcast:
            if event.message.command == cmNewData:
                self.curMessage = event.message.infoPtr
                self.drawView()

    def draw(self):
        super().draw()
        b = DrawBuffer()
        b.moveBuf(0, self.curMessage, self.getColor(1), len(self.curMessage))
        self.writeBuf(0, 0, len(self.curMessage), 1, b)


class MyApplication(Application):

    def initStatusLine(self, bounds: Rect) -> StatusLine:
        bounds.topLeft.y = bounds.bottomRight.y - 1
        return StatusLine(bounds,
                          StatusDef(0, 0xFFFF) +
                          StatusItem('~Alt+X~ Exit', kbAltX, cmQuit) +
                          StatusItem('~Alt+F3~ Close', kbAltF3, cmClose))

    def initMenuBar(self, bounds: Rect) -> MenuBar:
        bounds.bottomRight.y = bounds.topLeft.y + 1
        return MenuBar(bounds,
                       SubMenu('I~n~fo', kbAltN) +
                       MenuItem('I~n~fo', cmTechInfo, kbAltI, hcNoContext, 'Alt+I') +
                       MenuItem('E~x~it', cmQuit, kbAltX, hcNoContext, 'Alt+X')
                       )

    def handleEvent(self, event: Event):
        super().handleEvent(event)
        if event.what == evCommand:
            if event.message.command == cmTechInfo:
                self.clearEvent(event)
                self.TechInfo()

    def TechInfo(self):
        tr = Rect(10, 2, 40, 5)
        tv = TechInfoView(Rect(1, 1, 28, 3))

        twr = Rect(tr.topLeft.x - 1, tr.topLeft.y - 1, tr.bottomRight.x + 1, tr.bottomRight.y + 1)
        tvw = Window(twr, 'Individual View', 2)
        tvw.insert(tv)
        self.desktop.insert(tvw)

        tr.topLeft.x = 10
        tr.topLeft.y = 7
        tr.bottomRight.x = 40
        tr.bottomRight.y = 25
        ti = TechInfoDialog(tr)
        self.desktop.execView(ti)


def setupLogging():
    vLogger = logging.getLogger('vindauga')
    lFormat = "%(name)-25s | %(message)s"
    vLogger.setLevel(logging.DEBUG)
    handler = logging.StreamHandler(open('vindauga.log', 'wt'))
    handler.setFormatter(logging.Formatter(lFormat))
    vLogger.addHandler(handler)


if __name__ == '__main__':
    setupLogging()
    app = MyApplication()
    app.run()
