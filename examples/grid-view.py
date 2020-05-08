# -*- coding: utf-8 -*-
import logging

from vindauga.constants.buttons import bfDefault
from vindauga.constants.command_codes import hcNoContext, cmOK
from vindauga.constants.event_codes import evCommand
from vindauga.constants.keys import kbAltA, kbAltL, kbAltF
from vindauga.constants.option_flags import ofCentered
from vindauga.constants.window_flags import wfGrow
from vindauga.dialogs.grid_view_dialog import GridViewDialog
from vindauga.menus.menu import Menu
from vindauga.menus.menu_bar import MenuBar
from vindauga.menus.menu_item import MenuItem
from vindauga.menus.sub_menu import SubMenu
from vindauga.types.rect import Rect
from vindauga.widgets.application import Application
from vindauga.widgets.button import Button
from vindauga.widgets.dialog import Dialog
from vindauga.widgets.grid_view_box import ListRec
from vindauga.widgets.static_text import StaticText

NUM_COLUMNS = 11
NUM_ROWS = 18
NUM_HEAD_ROWS = 2
headings = (
    ("ROOT", "FACTOR", "FACTOR", "FACTOR", "FACTOR", "FACTOR", "FACTOR", "FACTOR", "FACTOR", "FACTOR", "FACTOR"),
    ("NO." , "A"     , "B"     , "C"     , "D"     , "E"     , "F"     , "G"     , "H"     , "I"     , "J")
)

widths = (
    7    , 10      , 14      , 10      , 10      , 10      , 10      , 10      , 10      , 10      , 10
)

decipoints = (2, 2, 3, 4, 2, 2, 2, 2, 3, 2, 2)

cmAbout = 100
cmList = 101

ListData = {}


class GridApp(Application):

    def initMenuBar(self, bounds):
        bounds.bottomRight.y = bounds.topLeft.y + 1
        return MenuBar(bounds, Menu(
            SubMenu('~F~ile', kbAltF, hcNoContext) +
            MenuItem('~A~bout', cmAbout, kbAltA, hcNoContext, 0) +
            MenuItem('~G~rid View', cmList, kbAltL, hcNoContext, 0)
        ))

    def handleEvent(self, event):
        super().handleEvent(event)
        if event.what == evCommand:
            if event.message.command == cmAbout:
                self.AboutDialog()
                self.clearEvent(event)
            elif event.message.command == cmList:
                self.ListDialog()
                self.clearEvent(event)

    def AboutDialog(self):
        pd = Dialog(Rect(0, 0, 35, 10), 'About')
        pd.options |= ofCentered
        pd.insert(StaticText(Rect(1, 2, 34, 6),
                             '\003Grid View\n'
                             '\003Fairly Crap\n'))
        pd.insert(Button(Rect(13, 7, 22, 9), '~O~K', cmOK, bfDefault))
        self.desktop.execView(pd)
        self.destroy(pd)

    def ListDialog(self):
        r = self.getExtent()
        r.grow(-3, -3)
        pd = GridViewDialog(r, 'Grid View', headings, NUM_HEAD_ROWS, ListData, NUM_COLUMNS, NUM_ROWS, widths, decipoints)
        pd.flags |= wfGrow
        self.desktop.execView(pd)
        self.destroy(pd)


if __name__ == '__main__':
    logging.basicConfig(level=logging.DEBUG)
    for i in range(NUM_ROWS):
        ListData[i, 0] = ListRec(i, True)
        for j in range(1, NUM_COLUMNS):
            ListData[i, j] = ListRec(ListData[i, j - 1].val ** .5, True)
            if j == 4:
                ListData[i, j].show = False
    app = GridApp()
    app.run()
