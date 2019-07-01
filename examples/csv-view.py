# -*- coding: utf-8 -*-
import csv
import logging
import sys

from vindauga.constants.command_codes import hcNoContext
from vindauga.constants.window_flags import wfGrow
from vindauga.constants.event_codes import evCommand
from vindauga.constants.keys import kbAltF
from vindauga.events.event import Event
from vindauga.menus.menu import Menu
from vindauga.menus.menu_bar import MenuBar
from vindauga.menus.sub_menu import SubMenu
from vindauga.widgets.application import Application
from vindauga.widgets.grid_view_box import ListRec
from vindauga.widgets.grid_view_dialog import GridViewDialog

ListData = {}

cmList = 101

columns = 0
rows = 0
headings = []
widths = []


class GridApp(Application):

    def initMenuBar(self, bounds):
        bounds.bottomRight.y = bounds.topLeft.y + 1
        return MenuBar(bounds, Menu(
            SubMenu('~F~ile', kbAltF, hcNoContext)
        ))

    def handleEvent(self, event):
        super().handleEvent(event)
        if event.what == evCommand:
            if event.message.command == cmList:
                self.ListDialog()
                self.clearEvent(event)

    def ListDialog(self):
        r = self.getExtent()
        r.grow(-3, -3)
        pd = GridViewDialog(r, 'Grid View', headings, 1, ListData, columns, rows, widths, [2, ] * columns)
        pd.flags |= wfGrow
        self.desktop.execView(pd)
        self.destroy(pd)


if __name__ == '__main__':
    logging.basicConfig(level=logging.DEBUG)
    with open(sys.argv[1], 'rt', newline='') as fp:
        rows = csv.reader(fp)
        headings = [next(rows)]
        widths = [len(h) + 2 for h in headings[0]]
        for i, row in enumerate(rows):
            for j, col in enumerate(row):
                columns = max(columns, j)
                widths[j] = max(len(col) + 2, widths[j])
                ListData[i, j] = ListRec(col, True)
    rows = j - 1
    app = GridApp()
    event = Event(evCommand)
    event.message.command = cmList
    app.putEvent(event)
    app.run()
