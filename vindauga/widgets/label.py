# -*- coding: utf-8 -*-
from vindauga.constants.command_codes import (cmReceivedFocus, cmReleasedFocus)
from vindauga.constants.event_codes import evBroadcast, evMouseDown, evKeyDown
from vindauga.constants.option_flags import ofSelectable, ofPreProcess, ofPostProcess
from vindauga.constants.state_flags import sfFocused
from vindauga.misc.character_codes import SPECIAL_CHARS, getAltCode
from vindauga.misc.util import hotKey
from vindauga.types.draw_buffer import DrawBuffer
from vindauga.types.group import Group
from vindauga.types.palette import Palette
from .static_text import StaticText


class Label(StaticText):
    name = 'Label'
    cpLabel = "\x07\x08\x09\x09"

    def __init__(self, bounds, text, linkedWidget=None):
        super().__init__(bounds, text)
        self._linkedWidget = linkedWidget
        self._light = False

        self.options |= ofPreProcess | ofPostProcess
        self.eventMask |= evBroadcast

    def draw(self):
        b = DrawBuffer()

        if self._light:
            color = self.getColor(0x0402)
            scOff = 0
        else:
            color = self.getColor(0x0301)
            scOff = 4

        b.moveChar(0, ' ', color, self.size.x)
        if self._text:
            b.moveCStr(1, self._text, color)

        if self.showMarkers:
            b.putChar(0, SPECIAL_CHARS[scOff])

        self.writeLine(0, 0, self.size.x, 1, b)

    def getPalette(self):
        palette = Palette(self.cpLabel)
        return palette

    def focusLink(self, event):
        if self._linkedWidget and self._linkedWidget.options & ofSelectable:
            self._linkedWidget.focus()
        self.clearEvent(event)

    def handleEvent(self, event):
        super().handleEvent(event)

        if event.what == evMouseDown:
            self.focusLink(event)
        elif event.what == evKeyDown:
            c = hotKey(self._text)

            if (getAltCode(c) == event.keyDown.keyCode or c != 0 and self.owner.phase == Group.phPostProcess and
                    event.keyDown.charScan.charCode.upper() == c):
                self.focusLink(event)
        elif event.what == evBroadcast and self._linkedWidget and event.message.command in {cmReceivedFocus, cmReleasedFocus}:
            self._light = ((self._linkedWidget.state & sfFocused) != 0)
            self.drawView()
