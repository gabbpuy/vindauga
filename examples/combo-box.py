# -*- coding: utf-8 -*-
import logging
import os
import random

from vindauga.events.event import Event
from vindauga.types.collections.gen_collection import GenCollection
from vindauga.constants.buttons import bfNormal, bfDefault
from vindauga.constants.command_codes import cmMenu, cmQuit, cmClose, hcNoContext, cmOK, cmCancel
from vindauga.constants.event_codes import evCommand
from vindauga.constants.keys import kbF10, kbAltX, kbCtrlW, kbAltF, kbF3
from vindauga.menus.menu_bar import MenuBar
from vindauga.menus.menu_item import MenuItem
from vindauga.menus.sub_menu import SubMenu
from vindauga.types.rect import Rect
from vindauga.types.status_def import StatusDef
from vindauga.types.status_item import StatusItem
from vindauga.widgets.application import Application
from vindauga.widgets.button import Button
from vindauga.widgets.combo_box import ComboBox
from vindauga.widgets.dialog import Dialog
from vindauga.widgets.input_line import InputLine
from vindauga.widgets.static_input_line import StaticInputLine
from vindauga.widgets.status_line import StatusLine

cmNewDialog = 200
logger = logging.getLogger('vindauga.examples.combo_box')
here = os.path.dirname(__file__)
animals = open(os.path.join(here, 'animals.txt'), 'rt', encoding='utf-8').read().splitlines(keepends=False)


class ComboApp(Application):

    def initStatusLine(self, bounds: Rect) -> StatusLine:
        bounds.topLeft.y = bounds.bottomRight.y - 1

        return StatusLine(bounds, StatusDef(0, 0xFFFF) +
                          StatusItem('', kbF10, cmMenu) +
                          StatusItem('~Alt+X~ Exit', kbAltX, cmQuit) +
                          StatusItem('~Alt+F3~ Close', kbCtrlW, cmClose))

    def initMenuBar(self, bounds: Rect) -> MenuBar:
        bounds.bottomRight.y = bounds.topLeft.y + 1
        return MenuBar(bounds, SubMenu('~F~ile', kbAltF) +
                       MenuItem('~D~ialog', cmNewDialog, kbF3, hcNoContext, 'F3') +
                       MenuItem.newLine() +
                       MenuItem('E~x~it', cmQuit, kbAltX, hcNoContext, 'Alt+X'))

    def handleEvent(self, event: Event):
        super().handleEvent(event)
        if event.what == evCommand:
            if event.message.command == cmNewDialog:
                self.newDialog()
                self.clearEvent(event)

    def newDialog(self):
        random.seed()

        items = random.sample(animals, 10)
        collection = GenCollection(items)

        r = Rect(2, 1, 27, 10)
        pd = Dialog(r, 'Combobox')

        tv = InputLine(Rect(2, 1, 20, 2), 128)
        pd.insert(tv)
        pd.insert(ComboBox(Rect(20, 1, 21, 2), tv, collection))

        tv = StaticInputLine(Rect(2, 3, 20, 4), 128, collection)
        pd.insert(tv)
        pd.insert(ComboBox(Rect(20, 3, 21, 4), tv, collection))

        pd.insert(Button(Rect(1, 6, 11, 8), '~O~K', cmOK, bfDefault))
        pd.insert(Button(Rect(12, 6, 22, 8), 'Cancel', cmCancel, bfNormal))
        pd.selectNext(False)
        self.desktop.execView(pd)
        data = pd.getData()
        logger.info('Combo Box: %s', data)
        self.destroy(pd)


def setupLogging():
    vLogger = logging.getLogger('vindauga')
    # vLogger.propagate = False
    lFormat = "%(name)-25s | %(message)s"
    vLogger.setLevel(logging.DEBUG)
    handler = logging.StreamHandler(open('vindauga.log', 'wt'))
    handler.setFormatter(logging.Formatter(lFormat))
    vLogger.addHandler(handler)


if __name__ == '__main__':
    setupLogging()
    app = ComboApp()
    app.run()
