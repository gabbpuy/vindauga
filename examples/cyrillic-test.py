# -*- coding: utf-8 -*-
from vindauga.constants.command_codes import cmQuit, cmNext, cmZoom, hcNoContext
from vindauga.constants.keys import kbF3, kbF4, kbF5, kbF6, kbAltW, kbAltX
from vindauga.menus.menu_bar import MenuBar
from vindauga.menus.menu_item import MenuItem
from vindauga.menus.sub_menu import SubMenu
from vindauga.types.rect import Rect
from vindauga.widgets.application import Application


class CyrillicApp(Application):
    def initMenuBar(self, bounds: Rect) -> MenuBar:
        bounds.bottomRight.y = bounds.topLeft.y + 1

        return MenuBar(bounds,
                       SubMenu("~Ф~айл", 0) +
                       MenuItem("~O~pen", 200, kbF3, hcNoContext, "F3") +
                       MenuItem("~N~ew", 200, kbF4, hcNoContext, "F4") +
                       MenuItem.newLine() +
                       MenuItem("E~x~it", cmQuit, kbAltX, hcNoContext, "Alt-X") +
                       # Probably the wrong translation of 'window'
                       SubMenu("~о~кно", kbAltW) +
                       MenuItem("~N~ext", cmNext, kbF6, hcNoContext, "F6") +
                       MenuItem("~Z~oom", cmZoom, kbF5, hcNoContext, "F5")
                       )


if __name__ == '__main__':
    app = CyrillicApp()
    app.run()
