# -*- coding: utf-8 -*-
from vindauga.constants.buttons import bfDefault
from vindauga.constants.command_codes import hcNoContext, cmQuit, cmOK
from vindauga.constants.event_codes import evCommand
from vindauga.constants.keys import kbAltF, kbNoKey, kbAltX
from vindauga.constants.option_flags import ofCentered
from vindauga.menus.menu_bar import MenuBar
from vindauga.menus.menu_item import MenuItem
from vindauga.menus.sub_menu import SubMenu
from vindauga.types.rect import Rect
from vindauga.widgets.application import Application
from vindauga.widgets.button import Button
from vindauga.widgets.dialog import Dialog
from vindauga.widgets.static_text import StaticText

cmAboutCmd = 100


class Demo(Application):
    def __init__(self):
        super().__init__()
        self.aboutDialogBox()

    def handleEvent(self, event):
        super().handleEvent(event)

        if event.what == evCommand:
            if event.message.command == cmAboutCmd:
                self.aboutDialogBox()
                self.clearEvent(event)

    def initMenuBar(self, bounds):
        bounds.bottomRight.y = bounds.topLeft.y + 1
        return MenuBar(bounds,
                       SubMenu('~F~ile', kbAltF, hcNoContext) +
                       MenuItem('~A~bout...', cmAboutCmd, kbNoKey, hcNoContext) +
                       MenuItem.newLine() +
                       MenuItem('E~x~it...', cmQuit, kbAltX, hcNoContext))

    def aboutDialogBox(self):
        aboutBox = Dialog(Rect(0, 0, 39, 13), 'About')
        aboutBox.insert(
            StaticText(Rect(9, 2, 30, 9),
                       '\x03Vision Tutorial\n\n\x03Python Version\n\n\x03Splash Screen Demo.')
        )
        aboutBox.insert(Button(Rect(14, 10, 26, 12), 'OK', cmOK, bfDefault))
        aboutBox.options |= ofCentered
        self.executeDialog(aboutBox, None)


if __name__ == '__main__':
    app = Demo()
    app.run()

