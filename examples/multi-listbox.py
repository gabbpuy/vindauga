# -*- coding: utf-8 -*-
import os
import random

from vindauga.events.event import Event
from vindauga.types.collections.string_collection import StringCollection
from vindauga.constants.command_codes import (cmOK, cmCancel, cmQuit, hcNoContext,
                                              cmNext, cmZoom, cmMenu)
from vindauga.constants.message_flags import mfInformation, mfOKButton
from vindauga.constants.buttons import bfDefault, bfNormal
from vindauga.constants.event_codes import evCommand
from vindauga.constants.keys import kbAltF, kbAltW, kbF6, kbF5, kbF2, kbF10, kbAltX
from vindauga.dialogs.message_box import messageBox
from vindauga.menus.menu_bar import MenuBar
from vindauga.menus.menu_item import MenuItem
from vindauga.menus.sub_menu import SubMenu
from vindauga.types.rect import Rect
from vindauga.types.status_def import StatusDef
from vindauga.types.status_item import StatusItem
from vindauga.widgets.application import Application
from vindauga.widgets.button import Button
from vindauga.widgets.dialog import Dialog
from vindauga.widgets.multi_select_list_box import MultiSelectListBox, ListBoxRec
from vindauga.widgets.scroll_bar import ScrollBar
from vindauga.widgets.status_line import StatusLine


cmNewDialog = 200

here = os.path.dirname(__file__)
animals = open(os.path.join(here, 'animals.txt'), 'rt', encoding='utf-8').read().splitlines(keepends=False)


class Demo(Application):
    """
    How to __change the background _pattern
    """

    def __init__(self):
        super().__init__()

    def initStatusLine(self, bounds: Rect) -> StatusLine:
        # Top of status line is 1 above bottom
        bounds.topLeft.y = bounds.bottomRight.y - 1
        return StatusLine(bounds,
                          StatusDef(0, 0xFFFF) +
                          StatusItem(0, kbF10, cmMenu) +
                          StatusItem('~Alt+X~ Exit', kbAltX, cmQuit))

    def initMenuBar(self, bounds: Rect) -> MenuBar:
        # always do this
        bounds.bottomRight.y = bounds.topLeft.y + 1
        return MenuBar(bounds,
                       SubMenu('~F~ile', kbAltF) +
                       MenuItem('E~x~it', cmQuit, cmQuit, hcNoContext, 'Alt+X') +
                       SubMenu('~W~indow', kbAltW) +
                       MenuItem('~N~ext', cmNext, kbF6, hcNoContext, 'F6') +
                       MenuItem('~Z~oom', cmZoom, kbF5, hcNoContext, 'F5') +
                       MenuItem('~D~ialog', cmNewDialog, kbF2, hcNoContext, 'F2'))

    def handleEvent(self, event: Event):
        super().handleEvent(event)

        if event.what == evCommand:
            if event.message.command == cmNewDialog:
                self.newDialog()
                self.clearEvent(event)

    def newDialog(self):
        pd = Dialog(Rect(20, 6, 60, 19), 'Demo Dialog')
        sb = ScrollBar(Rect(25, 2, 26, 11))
        pd.insert(sb)
        lb = MultiSelectListBox(Rect(2, 2, 24, 11), 2, sb)
        pd.insert(lb)
        names = random.sample(animals, 20)
        tsc = StringCollection(names)
        pd.insert(Button(Rect(28, 6, 38, 8), '~O~K', cmOK, bfDefault))
        pd.insert(Button(Rect(28, 10, 38, 12), '~C~ancel', cmCancel, bfNormal))
        data = ListBoxRec()
        data.items = tsc
        data.selection = 2
        items = [data]
        selection = ''
        pd.setData(items)
        control = self.desktop.execView(pd)
        if control != cmCancel:
            data = pd.getData()
            selection = ','.join(names[x] for x in data[0].selection)
        if control == cmOK:
            messageBox('\x03Your selection is {}'.format(selection), mfInformation, (mfOKButton,))
        self.destroy(pd)


if __name__ == '__main__':
    app = Demo()
    app.run()
