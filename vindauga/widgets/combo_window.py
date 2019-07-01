# -*- coding: utf-8 -*-
from vindauga.constants.command_codes import wnNoNumber, cmCancel
from vindauga.constants.event_codes import evMouseDown
from vindauga.constants.state_flags import sfShadow
from vindauga.types.palette import Palette
from .combo_viewer import ComboViewer
from .scroll_bar import ScrollBar
from .window import Window


class ComboWindow(Window):
    name = 'ComboWindow'
    cpComboWindow = '\x13\x13\x15\x04\x05\x1A\x14'

    def __init__(self, bounds, collection):
        super().__init__(bounds, '', wnNoNumber)
        self.setState(sfShadow, False)
        self.flags = 0

        r = self.getExtent()
        r.topLeft.x = r.bottomRight.x - 1
        sb = ScrollBar(r)
        self.insert(sb)
        r = self.getExtent()
        r.bottomRight.x -= 1

        self.viewer = ComboViewer(r, collection, sb)
        self.insert(self.viewer)

    def getPalette(self):
        return Palette(self.cpComboWindow)

    def getSelection(self):
        return self.viewer.getText(self.viewer.focused, 255)

    def handleEvent(self, event):
        if event.what == evMouseDown and not self.containsMouse(event):
            self.endModal(cmCancel)
            self.clearEvent(event)
        super().handleEvent(event)
