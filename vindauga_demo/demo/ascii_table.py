# -*- coding: utf-8 -*-
from curses.ascii import controlnames, unctrl
from enum import IntEnum

from vindauga.constants.command_codes import wnNoNumber, wpGrayWindow
from vindauga.constants.event_codes import evKeyboard, evBroadcast, evMouseDown, evMouseMove
from vindauga.constants.keys import kbHome, kbEnd, kbUp, kbDown, kbLeft, kbRight
from vindauga.constants.option_flags import ofFramed, ofSelectable
from vindauga.constants.window_flags import wfGrow, wfZoom
from vindauga.utilities.message import message
from vindauga.types.draw_buffer import DrawBuffer
from vindauga.types.rect import Rect
from vindauga.types.view import View
from vindauga.widgets.window import Window


class AsciiTableCommands(IntEnum):
    cmAsciiTableCmdBase = 910


cmCharFocused = 0


class _Table(View):
    name = '_Table'

    def __init__(self, bounds):
        super().__init__(bounds)
        self.eventMask |= evKeyboard

    def draw(self):
        buf = DrawBuffer()
        color = self.getColor(6)

        for y in range(0, self.size.y):
            buf.moveChar(0, ' ', color, self.size.x)
            for x in range(self.size.x):
                c = chr(32 * y + x)
                if not c.isprintable():
                    c = '.'
                buf.moveChar(x, c, color, 1)
            self.writeLine(0, y, self.size.x, 1, buf)
        self.showCursor()

    def charFocused(self):
        message(self.owner, evBroadcast, AsciiTableCommands.cmAsciiTableCmdBase + cmCharFocused,
                chr(self.cursor.x + 32 * self.cursor.y))

    def handleEvent(self, event):
        super().handleEvent(event)

        if event.what == evMouseDown:
            processing = True
            while processing:
                spot = self.makeLocal(event.mouse.where)
                self.setCursor(spot.x, spot.y)
                self.charFocused()
                processing = self.mouseEvent(event, evMouseMove)
            self.clearEvent(event)
        elif event.what == evKeyboard:
            kc = event.keyDown.keyCode
            if kc == kbHome:
                spot = (0, 0)
            elif kc == kbEnd:
                spot = (self.size.x - 1, self.size.y - 1)
            elif kc == kbUp:
                if self.cursor.y > 0:
                    spot = (self.cursor.x, self.cursor.y - 1)
                else:
                    spot = (self.cursor.x, self.size.y - 1)
            elif kc == kbDown:
                if self.cursor.y < self.size.y - 1:
                    spot = (self.cursor.x, self.cursor.y + 1)
                else:
                    spot = (self.cursor.x, 0)
            elif kc == kbLeft:
                if self.cursor.x > 0:
                    spot = (self.cursor.x - 1, self.cursor.y)
                else:
                    spot = (self.size.x - 1, self.cursor.y)
            elif kc == kbRight:
                if self.cursor.x < self.size.x - 1:
                    spot = (self.cursor.x + 1, self.cursor.y)
                else:
                    spot = (0, self.cursor.y)
            else:
                c = event.keyDown.charScan.charCode
                if isinstance(c, str):
                    c = ord(c)
                y, x = divmod(c, 32)
                spot = (x, y)

            if spot is not None:
                self.setCursor(*spot)

            self.charFocused()
            self.clearEvent(event)


class _Report(View):
    name = '_Report'

    def __init__(self, bounds):
        super().__init__(bounds)
        self.__asciiChar = '\x00'

    def draw(self):
        buf = DrawBuffer()
        color = self.getColor(6)

        c = self.__asciiChar
        if ord(c) <= 0x1F:
            c = controlnames[ord(c)]
        elif c == ' ':
            c = 'SP'
        elif not c.isprintable():
            c = unctrl(c)

        line = ' Char: {:3s} Decimal: {:3d} Hex: {:02X}    '.format(c, ord(self.__asciiChar), ord(self.__asciiChar))

        buf.moveStr(0, line, color)
        self.writeLine(0, 0, 32, 1, buf)

    def handleEvent(self, event):
        super().handleEvent(event)
        if event.what == evBroadcast:
            if event.message.command == AsciiTableCommands.cmAsciiTableCmdBase + cmCharFocused:
                # self.__asciiChar = event.message.infoLong
                self.__asciiChar = event.message.infoPtr
                self.drawView()


class AsciiChart(Window):
    name = 'AsciiChart'

    def __init__(self):
        super().__init__(Rect(0, 0, 34, 12), 'ASCII Chart', wnNoNumber)

        self.flags &= ~(wfGrow | wfZoom)
        self.palette = wpGrayWindow

        r = self.getExtent()
        r.grow(-1, -1)
        r.topLeft.y = r.bottomRight.y - 1

        control = _Report(r)
        control.options |= ofFramed
        control.eventMask |= evBroadcast
        self.insert(control)

        r = self.getExtent()
        r.grow(-1, -1)
        r.bottomRight.y = r.bottomRight.y - 2
        control = _Table(r)
        control.options |= ofFramed
        control.options |= ofSelectable
        control.blockCursor()
        self.insert(control)
        control.select()
