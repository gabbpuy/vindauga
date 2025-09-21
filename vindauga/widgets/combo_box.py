# -*- coding: utf-8 -*-
from vindauga.constants.command_codes import cmOK
from vindauga.constants.event_codes import evBroadcast, evKeyDown, evMouseDown
from vindauga.constants.keys import kbDown
from vindauga.constants.option_flags import ofPostProcess
from vindauga.constants.state_flags import sfFocused, sfDisabled
from vindauga.events.event import Event
from vindauga.utilities.input.key_utils import ctrlToArrow
from vindauga.types.collections.collection import Collection
from vindauga.types.draw_buffer import DrawBuffer
from vindauga.types.palette import Palette
from vindauga.types.rect import Rect
from vindauga.types.view import View

from .combo_window import ComboWindow
from .input_line import InputLine
from .static_input_line import StaticInputLine


class ComboBox(View):
    cpComboBox = '\x16'
    cpSComboBox = '\x1A'
    icon = '↓'
    name = 'ComboBox'

    def __init__(self, bounds: Rect, inputLine: InputLine, collection: Collection):
        super().__init__(bounds)
        self.inputLine = None
        self.collection = None
        self.initBox(inputLine, collection)
        self.__focused = None

    def initBox(self, inputLine: InputLine, collection: Collection):
        self.options |= ofPostProcess
        self.eventMask |= evBroadcast
        self.inputLine = inputLine
        self.collection = collection

    @property
    def focused(self):
        return self.__focused

    def consumesData(self):
        return False

    def draw(self):
        b = DrawBuffer()
        b.moveStr(0, self.icon, self.getColor(0x01))
        self.writeLine(0, 0, self.size.x, self.size.y, b)

    def getPalette(self) -> Palette:
        if isinstance(self.inputLine, StaticInputLine):
            return Palette(self.cpSComboBox)
        return Palette(self.cpComboBox)

    def handleEvent(self, event: Event):
        super().handleEvent(event)

        if event.what == evMouseDown or (event.what == evKeyDown and ctrlToArrow(event.keyDown.keyCode) == kbDown and
                                         self.inputLine.state & sfFocused):
            if not self.collection or not self.inputLine:
                return

            if not self.inputLine.state & sfDisabled:
                self.inputLine.select()

            r = self.inputLine.getBounds()
            r.bottomRight.x = r.topLeft.x + max(self.collection.getTextLength() + 1, self.inputLine.size.x) + 1

            delta = self.owner.size.x - r.bottomRight.x - 1

            if delta < 0:
                r.topLeft.x += delta
                r.bottomRight.x += delta

            r.topLeft.x = max(r.topLeft.x, 1)
            r.topLeft.y += 1
            r.bottomRight.y = r.topLeft.y + len(self.collection)
            delta = self.owner.size.y - r.bottomRight.y - 1
            if delta < 0:
                r.topLeft.y += delta
                r.bottomRight.y += delta

            r.topLeft.y = max(r.topLeft.y, 1)

            comboWindow = ComboWindow(r, self.collection)
            c = self.owner.execView(comboWindow)

            if c == cmOK and not self.inputLine.state & sfDisabled:
                result = comboWindow.getSelection()
                self.__focused = comboWindow.viewer.focused
                self.inputLine.setData(result)
                self.inputLine.selectAll(True)
                self.inputLine.drawView()
            self.destroy(comboWindow)
            self.clearEvent(event)

    def newList(self, collection: Collection):
        self.collection = collection

    def shutdown(self):
        self.inputLine = None
        super().shutdown()
