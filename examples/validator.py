# -*- coding: utf-8 -*-
import logging

from vindauga.constants.buttons import bfDefault, bfNormal
from vindauga.constants.command_codes import hcNoContext, cmQuit, cmOK, cmCancel
from vindauga.constants.event_codes import evCommand
from vindauga.constants.keys import kbAltF, kbAltX, kbNoKey
from vindauga.constants.option_flags import ofCentered
from vindauga.menus.menu_bar import MenuBar
from vindauga.menus.sub_menu import SubMenu
from vindauga.menus.menu_item import MenuItem
from vindauga.types.rect import Rect
from vindauga.widgets.application import Application
from vindauga.widgets.button import Button
from vindauga.widgets.dialog import Dialog
from vindauga.widgets.input_line import InputLine
from vindauga.widgets.label import Label
from vindauga.widgets.static_text import StaticText

from vindauga.types.validation.range_validator import RangeValidator


cmOpenDialog = 100


class DemoDialog(Dialog):
    def __init__(self):
        super().__init__(Rect(0, 0, 42, 16), 'Validator Example')
        self.options |= ofCentered
        obj = InputLine(Rect(23, 1, 40, 2), 40)
        self.insert(obj)
        self.insert(Label(Rect(1, 1, 22, 2), 'No validator', obj))

        obj = InputLine(Rect(23, 3, 27, 4), 3, RangeValidator(1, 31))
        self.insert(obj)
        self.insert(Label(Rect(1, 3, 22, 4), 'Date Style', obj))
        self.insert(StaticText(Rect(27, 3, 28, 4), '/'))

        line = InputLine(Rect(28, 3, 32, 4), 3)
        self.insert(line)
        line.setValidator(RangeValidator(1, 12))

        self.insert(StaticText(Rect(32, 3, 33, 4), '/'))
        self.insert(InputLine(Rect(33, 3, 39, 4), 5, RangeValidator(1950, 2050)))

        self.insert(Button(Rect(1, 13, 11, 15), 'O~K~', cmOK, bfDefault))
        self.insert(Button(Rect(12, 13, 24, 15), '~C~ancel', cmCancel, bfNormal))
        self.selectNext(False)


class DemoApp(Application):
    def handleEvent(self, event):
        super().handleEvent(event)
        if event.what == evCommand:
            if event.message.command == cmOpenDialog:
                d = DemoDialog()
                self.executeDialog(d, None)
            else:
                return
        self.clearEvent(event)

    def initMenuBar(self, bounds):
        bounds.bottomRight.y = bounds.topLeft.y + 1

        return MenuBar(bounds,
                       SubMenu('~F~ile', kbAltF, hcNoContext) +
                       MenuItem('~D~ialog...', cmOpenDialog, kbNoKey, hcNoContext ) +
                       MenuItem.newLine() +
                       MenuItem('E~x~it', cmQuit, kbAltX, hcNoContext))


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
    app = DemoApp()
    app.run()
