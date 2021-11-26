# -*- coding: utf-8 -*-
import logging

from vindauga.constants.buttons import bfDefault, bfLeftJust, bfGrabFocus, bfBroadcast
from vindauga.constants.command_codes import (cmDefault, cmCommandSetChanged, cmRecordHistory)
from vindauga.constants.event_codes import evBroadcast, evMouseDown, evKeyDown, evMouseMove, evCommand
from vindauga.constants.option_flags import ofSelectable, ofFirstClick, ofPreProcess, ofPostProcess
from vindauga.constants.state_flags import sfActive, sfSelected, sfFocused, sfDisabled
from vindauga.events.event import Event
from vindauga.misc.character_codes import SPECIAL_CHARS, getAltCode
from vindauga.misc.cp437 import cp437ToUnicode
from vindauga.misc.message import message
from vindauga.misc.util import hotKey
from vindauga.misc.util import nameLength
from vindauga.types.draw_buffer import DrawBuffer
from vindauga.types.palette import Palette
from vindauga.types.view import View

logger = logging.getLogger(__name__)

cmGrabDefault = 61
cmReleaseDefault = 62


class Button(View):
    name = 'Button'
    shadows = '▓▓▓'
    cpButton = "\x0A\x0B\x0C\x0D\x0E\x0E\x0E\x0F"
    markers = '[]'

    def __init__(self, bounds, title, commands, flags):
        super().__init__(bounds)
        self.title = title
        self._command = commands
        self._flags = flags
        self._amDefault = ((flags & bfDefault) != 0)

        self.options |= (ofSelectable | ofFirstClick | ofPreProcess | ofPostProcess)

        self.eventMask |= evBroadcast

        if not self.commandEnabled(commands):
            self.state |= sfDisabled

    def draw(self):
        self.drawState(False)

    def drawState(self, down):
        b = DrawBuffer()
        ch = ' '

        if self.state & sfDisabled:
            cButton = self.getColor(0x0404)
        else:
            cButton = self.getColor(0x0501)
            if self.state & sfActive:
                if self.state & sfSelected:
                    cButton = self.getColor(0x0703)
                elif self._amDefault:
                    cButton = self.getColor(0x0602)

        cShadow = self.getColor(8)

        s = self.size.x - 1
        titleRow = self.size.y // 2 - 1
        for y in range(self.size.y - 1):
            b.moveChar(0, ' ', cButton, self.size.x)
            b.putAttribute(0, cShadow)
            if down:
                b.putAttribute(1, cShadow)
                ch = ' '
                i = 2
            else:
                b.putAttribute(s, cShadow)
                if self.showMarkers:
                    ch = ' '
                else:
                    if y == 0:
                        b.putChar(s, self.shadows[0])
                    else:
                        b.putChar(s, self.shadows[1])

                    ch = self.shadows[2]
                i = 1

            if y == titleRow and self.title:
                self.__drawTitle(b, s, i, cButton, down)

            if self.showMarkers and down:
                b.putChar(1, self.markers[0])
                b.putChar(s - 1, self.markers[1])

            self.writeLine(0, y, self.size.x, 1, b)

        b.moveChar(0, ' ', cShadow, 2)
        b.moveChar(2, ch, cShadow, s - 1)

        self.writeLine(0, self.size.y - 1, self.size.x, 1, b)

    def getPalette(self):
        return Palette(self.cpButton)

    def handleEvent(self, event):
        clickRect = self.getExtent()
        clickRect.topLeft.x += 1
        clickRect.bottomRight.x -= 1
        clickRect.bottomRight.y -= 1

        if event.what == evMouseDown:
            mouse = self.makeLocal(event.mouse.where)
            if mouse not in clickRect:
                self.clearEvent(event)

        if self._flags & bfGrabFocus:
            super().handleEvent(event)

        c = hotKey(self.title)

        if event.what == evMouseDown:
            if not self.state & sfDisabled:
                clickRect.bottomRight.x += 1
                down = False
                done = False
                while not done:
                    mouse = self.makeLocal(event.mouse.where)
                    if down != (mouse in clickRect):
                        down = not down
                        self.drawState(down)
                    done = not (self.mouseEvent(event, evMouseMove))
                if down:
                    self.press()
                    self.drawState(False)
            self.clearEvent(event)

        elif event.what == evKeyDown:
            if ((event.keyDown.keyCode == getAltCode(c)) or
                    (self.owner.phase == self.phPostProcess and c and event.keyDown.charScan.charCode.upper() == c) or
                    ((self.state & sfFocused) and event.keyDown.charScan.charCode == ' ')):
                self.press()
                self.clearEvent(event)

        elif event.what == evBroadcast:
            command = event.message.command

            if cmDefault == command:
                if self._amDefault and not (self.state & sfDisabled):
                    self.press()
                    self.clearEvent(event)

            elif command in {cmGrabDefault, cmReleaseDefault}:
                if self._flags & bfDefault:
                    self._amDefault = event.message.command == cmReleaseDefault
                    self.drawView()
            elif command == cmCommandSetChanged:
                self.setState(sfDisabled, not self.commandEnabled(command))
                self.drawView()

    def makeDefault(self, enable):
        if not (self._flags & bfDefault):
            message(self.owner, evBroadcast,
                    [cmReleaseDefault, cmGrabDefault][enable], self)
            self._amDefault = enable
            self.drawView()

    def setState(self, state, enable):
        super().setState(state, enable)

        if state & (sfSelected | sfActive):
            if not enable:
                self.state &= ~sfFocused
                self.makeDefault(False)

            self.drawView()

        if state & sfFocused:
            self.makeDefault(enable)

    def press(self):
        message(self.owner, evBroadcast, cmRecordHistory, None)

        if self._flags & bfBroadcast:
            message(self.owner, evBroadcast, self._command, self)
        else:
            e = Event(evCommand)
            e.message.command = self._command
            e.message.infoPtr = self
            self.putEvent(e)

    def __drawTitle(self, b, s, i, cButton, down):
        if self._flags & bfLeftJust:
            titlePosition = 0
        else:
            titlePosition = (s - nameLength(self.title)) // 2

            if titlePosition < 0:
                titlePosition = 1

        b.moveCStr(i + titlePosition, self.title, cButton)

        if self.showMarkers and not down:
            if self.state & sfSelected:
                scOff = 0
            elif self._amDefault:
                scOff = 2
            else:
                scOff = 4

            b.putChar(0, SPECIAL_CHARS[scOff])
            b.putChar(s, SPECIAL_CHARS[scOff + 1])
