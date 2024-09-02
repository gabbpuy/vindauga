# -*- coding: utf-8 -*-
import logging

from vindauga.constants.command_codes import cmQuit, cmHelp, cmClose, cmZoom, cmResize, cmMenu
from vindauga.constants.keys import kbAltSpace, kbNoKey, kbAltX, kbCtrlW, kbF5, kbCtrlF5, kbF10, kbF1
from vindauga.menus.menu import Menu
from vindauga.menus.menu_bar import MenuBar
from vindauga.menus.menu_item import MenuItem
from vindauga.menus.sub_menu import SubMenu
from vindauga.types.rect import Rect
from vindauga.types.status_def import StatusDef
from vindauga.types.status_item import StatusItem
from vindauga.widgets.application import Application
from vindauga.widgets.status_line import StatusLine

"""
This file demonstrates a simple method of implementing the 'hint'
functionality of Turbo Vision status lines. Hints are _text that appears to
the right on the status line, and is seperated from the status line items
by a vertical line. Hints are somewhat like 'quick and dirty help' messages;
the hint that appears is determined by the focused item's help context.

In general, implementing hints is easy - you just derive a new class
from StatusLine, and override the hint() method. The new hint() method is
passed a number that is a help context; it needs to return a string to
that represents the 'hint' for that context.
"""

cmAbout = 1000
cmFileNew = 1001

hcSystem = 1000
hcAbout = 1001
hcFile = 1002
hcFileExit = 1003
hcFileNew = 1004


class HintStatusLine(StatusLine):
    strRef = {
        hcSystem: "system commands",
        hcAbout: "show version and copyright information",
        hcFile: "file-management commands (Open, Save, etc)",
        hcFileExit: "exit the program",
        hcFileNew: "create a new file in a new Edit window"
    }

    def hint(self, helpCtx: int) -> str:
        p = self.strRef.get(helpCtx)
        if not p:
            return super().hint(helpCtx)
        return p


class HintApp(Application):

    def initMenuBar(self, bounds: Rect) -> MenuBar:
        bounds.bottomRight.y = bounds.topLeft.y + 1
        sub1 = SubMenu('~≡~', kbAltSpace, hcSystem) + MenuItem('~A~bout', cmAbout, kbNoKey, hcAbout, '')
        sub2 = (SubMenu('~F~ile', kbNoKey, hcFile) +
                MenuItem('~N~ew', cmFileNew, kbNoKey, hcFileNew, 0, '') +
                MenuItem.newLine() +
                MenuItem('E~x~it', cmQuit, kbAltX, hcFileExit, 'Alt+X'))
        return MenuBar(bounds, Menu(sub1 + sub2))

    def initStatusLine(self, bounds: Rect) -> StatusLine:
        bounds.topLeft.y = bounds.bottomRight.y - 1
        return HintStatusLine(bounds,
                              StatusDef(hcSystem, hcFileNew) +
                              StatusItem('~F1~ Help', kbF1, cmHelp) +
                              StatusItem('', kbAltX, cmQuit) +
                              StatusItem('', kbCtrlW, cmClose) +
                              StatusItem('', kbF5, cmZoom) +
                              StatusItem('', kbCtrlF5, cmResize) +
                              StatusItem('', kbF10, cmMenu) +
                              StatusDef(0, 0xFFFF) +
                              StatusItem('~F1~ Help', kbF1, cmHelp) +
                              StatusItem('~Alt+X~ Exit', kbAltX, cmQuit) +
                              StatusItem('', kbCtrlW, cmClose) +
                              StatusItem('', kbF5, cmZoom) +
                              StatusItem('', kbCtrlF5, cmResize) +
                              StatusItem('', kbF10, cmMenu)
                              )


def setupLogging():
    vLogger = logging.getLogger('vindauga')
    vLogger.propagate = False
    lFormat = "%(name)-25s | %(message)s"
    vLogger.setLevel(logging.DEBUG)
    handler = logging.StreamHandler(open('vindauga.log', 'wt'))
    handler.setFormatter(logging.Formatter(lFormat))
    vLogger.addHandler(handler)


if __name__ == '__main__':
    setupLogging()
    app = HintApp()
    app.run()
    app.shutdown()

