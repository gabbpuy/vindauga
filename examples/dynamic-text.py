# -*- coding: utf-8 -*-
from vindauga.constants.buttons import bfNormal
from vindauga.constants.command_codes import hcNoContext, cmOK
from vindauga.constants.event_codes import evCommand, evKeyDown
from vindauga.constants.keys import kbNoKey, kbTab
from vindauga.constants.message_flags import mfOKButton, mfInformation
from vindauga.constants.option_flags import ofCentered
from vindauga.dialogs.message_box import messageBox
from vindauga.events.event import Event
from vindauga.menus.menu import Menu
from vindauga.menus.menu_bar import MenuBar
from vindauga.menus.menu_item import MenuItem
from vindauga.types.rect import Rect
from vindauga.widgets.application import Application
from vindauga.widgets.button import Button
from vindauga.widgets.dialog import Dialog
from vindauga.widgets.dynamic_text import DynamicText
from vindauga.widgets.input_line import InputLine

cmAbout = 100
cmTest = 101


class TestDialog(Dialog):
    def __init__(self):
        super().__init__(Rect(0, 0, 40, 10), 'Dynamic Text')
        self.options |= ofCentered
        self.__master = InputLine(Rect(10, 2, 32, 3), 21)
        self.insert(self.__master)

        self.__slave = DynamicText(Rect(11, 4, 31, 5), 'Initial Text', False)
        self.insert(self.__slave)

        self.insert(Button(Rect(15, 6, 25, 8), 'O~K~', cmOK, bfNormal))
        self.__master.select()

    def handleEvent(self, event):
        if event.what == evKeyDown and event.keyDown.keyCode == kbTab:
            buf = self.__master.getData()
            self.__slave.setText(buf.value)
        super().handleEvent(event)


class TestApplication(Application):

    def initMenuBar(self, bounds):
        bounds.bottomRight.y = bounds.topLeft.y + 1

        return MenuBar(bounds,
                       Menu(
                           MenuItem('~T~est', cmTest, kbNoKey, hcNoContext)
                       )
                       )

    def handleEvent(self, event):
        super().handleEvent(event)

        if event.what == evCommand:
            if event.message.command == cmAbout:
                self.about()
            elif event.message.command == cmTest:
                self.test()
            else:
                return
            self.clearEvent(event)

    def about(self):
        messageBox('\003Dynamic Text Demo', mfInformation, (mfOKButton,))

    def test(self):
        d = TestDialog()
        self.desktop.execView(d)
        self.destroy(d)


if __name__ == '__main__':
    init = Event(evCommand)
    init.message.command = cmAbout

    app = TestApplication()
    app.putEvent(init)
    app.run()

