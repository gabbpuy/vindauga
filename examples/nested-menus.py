# -*- coding: utf-8 -*-
import logging

from vindauga.constants.buttons import bfDefault
from vindauga.constants.command_codes import cmQuit, hcNoContext, cmOK
from vindauga.constants.event_codes import evCommand
from vindauga.constants.keys import kbAltSpace, kbNoKey, kbAltX, kbAltA, kbAltY, kbAltZ, kbAltF
from vindauga.constants.option_flags import ofCentered
from vindauga.menus.menu import Menu
from vindauga.menus.menu_bar import MenuBar
from vindauga.menus.menu_item import MenuItem
from vindauga.menus.sub_menu import SubMenu
from vindauga.types.rect import Rect
from vindauga.widgets.application import Application
from vindauga.widgets.button import Button
from vindauga.widgets.dialog import Dialog
from vindauga.widgets.static_text import StaticText

cmAbout = 100


class NestedApplication(Application):

    def initMenuBar(self, bounds):
        bounds.bottomRight.y = bounds.topLeft.y + 1

        menuBar = MenuBar(bounds,
                          SubMenu('~F~ile', kbAltF) +
                          MenuItem('~A~bout', cmAbout, kbAltA, hcNoContext, 'Alt+A') +
                          MenuItem.newLine() +
                          MenuItem('Exit', 0, kbNoKey, helpCtx=hcNoContext,
                                   subMenu=Menu(
                                       MenuItem('Exit & ~S~ave', cmQuit, kbAltX, hcNoContext, None, nextItem=
                                       MenuItem('Exit & ~A~bandon', cmQuit, kbAltY, hcNoContext, None, nextItem=
                                       MenuItem('Just ~Q~uit', cmQuit, kbAltZ, hcNoContext, None, nextItem=
                                       MenuItem('~N~ext Level', 0, kbNoKey,
                                                subMenu=Menu(
                                                    MenuItem('~O~ne', cmQuit, kbAltX, hcNoContext, None, nextItem=
                                                    MenuItem('~T~wo', cmQuit, kbAltX)
                                                             )
                                                )))))
                                       ),

                                   )


                          )

        return menuBar

    def handleEvent(self, event):
        super().handleEvent(event)
        if event.what == evCommand:
            if event.message.command == cmAbout:
                self.aboutBox()
                self.clearEvent(event)

    def aboutBox(self):
        pd = Dialog(Rect(0, 0, 35, 12), 'About')
        pd.insert(StaticText(Rect(1, 2, 34, 7),
                             '\x03Turbo Vision\n\n' +
                             '\x03Creating a nested menu\n\n' +
                             '\x03Borland Technical Support'))
        pd.insert(Button(Rect(3, 9, 32, 11), '~O~key-d~O~key', cmOK, bfDefault))
        pd.options |= ofCentered
        self.desktop.execView(pd)
        self.destroy(pd)


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
    app = NestedApplication()
    app.run()
