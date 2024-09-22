# -*- coding: utf-8 -*-
from vindauga.constants.buttons import bfDefault
from vindauga.constants.command_codes import hcNoContext, cmOK, cmQuit
from vindauga.constants.message_flags import mfInformation, mfOKButton
from vindauga.constants.event_codes import evCommand
from vindauga.constants.keys import kbAltA, kbAltP, kbAltI, kbAltX, kbAltT, kbAltSpace
from vindauga.constants.option_flags import ofCentered
from vindauga.dialogs.message_box import messageBox
from vindauga.events.event import Event
from vindauga.menus.menu import Menu
from vindauga.menus.menu_box import MenuBox
from vindauga.menus.menu_bar import MenuBar
from vindauga.menus.menu_item import MenuItem
from vindauga.menus.sub_menu import SubMenu
from vindauga.types.rect import Rect
from vindauga.widgets.application import Application
from vindauga.widgets.button import Button
from vindauga.widgets.dialog import Dialog
from vindauga.widgets.static_text import StaticText

cmAbout = 100
cmPopup = 101
cmOne = 102
cmTwo = 103


class PopupApplication(Application):
    def initMenuBar(self, bounds: Rect) -> MenuBar:
        bounds.bottomRight.y = bounds.topLeft.y + 1
        return MenuBar(bounds, Menu(
            SubMenu('~≡~', kbAltSpace) +
            MenuItem('~A~bout', cmAbout, kbAltA, hcNoContext, '') +
            MenuItem('~P~opup', cmPopup, kbAltP, hcNoContext, '')
        ))

    def handleEvent(self, event: Event):
        super().handleEvent(event)
        if event.what == evCommand:
            emc = event.message.command
            if emc == cmAbout:
                self.aboutDialog()
            elif emc == cmPopup:
                self.popup()
            elif emc == cmOne:
                messageBox('Item 1 selected', mfInformation, (mfOKButton,))
            elif emc == cmTwo:
                messageBox('Item 2 selected', mfInformation, (mfOKButton,))
            self.clearEvent(event)

    def aboutDialog(self):
        pd = Dialog(Rect(0, 0, 35, 12), "About")
        pd.options |= ofCentered
        pd.insert(StaticText(Rect(1, 2, 34, 7),
                             "\003Turbo Vision Example\n\n"
                             "\003Creating a Popup Menu\n\n"
                             "\003Borland Technical Support"))
        pd.insert(Button(Rect(3, 9, 32, 11), "~O~k", cmOK, bfDefault))
        self.desktop.execView(pd)
        self.destroy(pd)

    def popup(self):
        bounds = Rect(0, 0, 0, 0)
        # for clarity, we'll create separately the menu to insert into the menubox
        theMenu = Menu(MenuItem("Item ~1~", cmOne, kbAltI, hcNoContext, "Alt-1", nextItem=
        MenuItem("Item ~2~", cmTwo, kbAltT, hcNoContext, "Alt-2", nextItem=
        MenuItem("E~x~it", cmQuit, kbAltX, hcNoContext, "Alt-X"))))

        # now create the menu with no parent
        mb = MenuBox(bounds, theMenu, None)

        # however, if we don't specify appropriate bounds, we must do something to ensure it is appropriately
        # positioned on the desktop
        mb.options |= ofCentered

        result = None
        # then make sure it's valid and execute it
        if self.validView(mb):
            result = self.desktop.execView(mb)
            self.destroy(mb)

        event = Event(evCommand)
        event.message.command = result
        self.putEvent(event)
        self.clearEvent(event)


if __name__ == '__main__':
    app = PopupApplication()
    app.run()
