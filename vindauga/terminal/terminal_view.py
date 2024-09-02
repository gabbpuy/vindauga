# -*- coding: utf-8 -*-
from __future__ import annotations
import curses
import logging
import os
import unicodedata

import wcwidth

from vindauga.constants.command_codes import cmPaste
from vindauga.constants.event_codes import evMouseUp, evKeyDown, evMouseDown, evCommand
from vindauga.constants.option_flags import ofSelectable
from vindauga.constants.keys import *
from vindauga.events.event import Event
from vindauga.misc.clipboard import Clipboard
from vindauga.types.collections.collection import Collection
from vindauga.types.draw_buffer import DrawBuffer, BufferArray
from vindauga.types.point import Point
from vindauga.types.view import View

from .terminal import Terminal, STATE_CURSOR_INVIS, STATE_TITLE_CHANGED, STATE_MOUSE

logger = logging.getLogger(__name__)


class TerminalView(View):
    ActiveTerminals = Collection()

    def __init__(self, bounds: Rect, parent: Window, command=None, *commandArgs):
        super().__init__(bounds)
        self.window = parent
        self.__clipboard = Clipboard()

        self.eventMask |= evMouseUp
        self.options |= ofSelectable
        self.terminal = Terminal(self.size.x, self.size.y, 0, command, *commandArgs)
        self.terminal.setColors(curses.COLOR_WHITE, curses.COLOR_BLACK)

    def draw(self):
        # TODO: Make this handle utf-8 better
        minY = min(self.size.y, self.terminal.rows)
        minX = min(self.size.x, self.terminal.cols)

        for y in range(minY):
            buffer = DrawBuffer(True)
            x = 0
            right = minX
            while x < right:
                cell = self.terminal.cells[y][x]
                c_w = wcwidth.wcwidth(chr(cell.char))
                attr = cell.attr
                c = cell.color
                if attr & curses.A_REVERSE:
                    c = self.reverseColor(c)
                buffer.putChar(x, chr(cell.char))
                if c_w > 0:
                    buffer.putAttribute(x, c)
                if c_w > 1:
                    # handle glyphs wider than 1
                    right -= (c_w -1)
                x += 1
            self.writeLine(0, y, min(x, minX), 1, buffer)
        self.setCursor(self.terminal.currCol, self.terminal.currRow)

        if self.terminal.state & STATE_CURSOR_INVIS:
            self.hideCursor()
        else:
            self.showCursor()

        if self.terminal.state & STATE_TITLE_CHANGED:
            self.window.setTitle(self.terminal.title)
            self.terminal.state &= ~STATE_TITLE_CHANGED

    def handleEvent(self, event: Event):
        super().handleEvent(event)
        ch = [0, 0]

        if event.what == evKeyDown:
            ch[0] = event.keyDown.charScan.charCode
            if ord(ch[0]) in {-1, 0}:
                ch = self.decodeKey(event.keyDown.keyCode)
            if ch[0] != -1:
                self.terminal.write(ch[0])
            if ch[1]:
                self.terminal.write(ch[1])
            self.clearEvent(event)
        elif event.what in {evMouseDown, evMouseUp}:
            if self.terminal.state & STATE_MOUSE:
                self.sendMouseEvent(event)
            if not self.terminal.state & STATE_MOUSE:
                self.tryPaste(event, 1)
            self.clearEvent(event)
        elif event.what == evCommand:
            if event.message.command == cmPaste:
                self.tryPaste(event, 0)
                self.clearEvent(event)

    def sendMouseEvent(self, event: Event):
        local = self.makeLocal(event.mouse.where)
        b = chr(32)
        mb = event.mouse.buttons
        if mb & 1:
            b = chr(32)
        elif mb & 2:
            b = chr(33)
        elif mb & 4:
            b = chr(34)
        elif mb & 8:
            b = chr(96)
        elif mb & 16:
            b = chr(97)
        elif not (mb & 7):
            b = chr(35)
        bx = chr(local.x + 33)
        by = chr(local.y + 33)
        buffer = bytes(f'\033[M{b}{bx}{by}')
        os.write(self.terminal.ptyFd, buffer)

    def tryPaste(self, event: Event, clip: int):
        if clip and not event.mouse.buttons & 2:
            return
        buffer = self.__clipboard.receiveFromClipboard()
        if buffer:
            os.write(self.terminal.ptyFd, buffer)

    def changeSize(self, s: Point):
        self.terminal.resize(s.x - 2, s.y - 2)
        self.growTo(s.x - 2, s.y - 2)
        self.drawView()

    @staticmethod
    def decodeKey(k: int) -> tuple[int, int]:
        ESC = '\x1B'
        keyMap = {
            kbEnter: (10, 0),
            kbEsc: (ESC, 0),
            kbDown: (curses.KEY_DOWN, 0),
            kbUp: (curses.KEY_UP, 0),
            kbLeft: (curses.KEY_LEFT, 0),
            kbRight: (curses.KEY_RIGHT, 0),
            kbBackSpace: (curses.KEY_BACKSPACE, 0),
            kbTab: (9, 0),
            kbPgDn: (curses.KEY_NPAGE, 0),
            kbPgUp: (curses.KEY_PPAGE, 0),
            kbHome: (curses.KEY_HOME, 0),
            kbEnd: (curses.KEY_END, 0),
            kbIns: (curses.KEY_IC, 0),
            kbDel: (curses.KEY_DC, 0),
            kbF1: (curses.KEY_F1, 0),
            kbF2: (curses.KEY_F2, 0),
            kbF3: (curses.KEY_F3, 0),
            kbF4: (curses.KEY_F4, 0),
            kbF5: (curses.KEY_F5, 0),
            kbF6: (curses.KEY_F6, 0),
            kbF7: (curses.KEY_F7, 0),
            kbF8: (curses.KEY_F8, 0),
            kbF9: (curses.KEY_F9, 0),
            kbF10: (curses.KEY_F10, 0),
            kbAltA: (ESC, 'A'),
            kbAltB: (ESC, 'B'),
            kbAltC: (ESC, 'C'),
            kbAltD: (ESC, 'D'),
            kbAltE: (ESC, 'E'),
            kbAltF: (ESC, 'F'),
            kbAltG: (ESC, 'G'),
            kbAltH: (ESC, 'H'),
            kbAltI: (ESC, 'I'),
            kbAltJ: (ESC, 'J'),
            kbAltK: (ESC, 'K'),
            kbAltL: (ESC, 'L'),
            kbAltM: (ESC, 'M'),
            kbAltN: (ESC, 'N'),
            kbAltO: (ESC, 'O'),
            kbAltP: (ESC, 'P'),
            kbAltQ: (ESC, 'Q'),
            kbAltR: (ESC, 'R'),
            kbAltS: (ESC, 'S'),
            kbAltT: (ESC, 'T'),
            kbAltU: (ESC, 'U'),
            kbAltV: (ESC, 'V'),
            kbAltW: (ESC, 'W'),
            kbAltX: (ESC, 'X'),
            kbAltY: (ESC, 'Y'),
            kbAltZ: (ESC, 'Z'),
        }
        return keyMap.get(k, (-1, 0))

    @staticmethod
    def reverseColor(color: int) -> int:
        a = color & 0x0F
        b = color & 0xF0
        return (a << 4) | (b >> 4)

    @staticmethod
    def handleTerminal(window: TerminalView, *args):
        bytesRead = window.terminal.readPipe()
        if bytesRead > 0:
            window.drawView()
        elif bytesRead == -1:
            window.window.close()

    @staticmethod
    def updateTerminals():
        """
        Call me on idle; `TerminalView.updateTerminals()`
        """
        TerminalView.ActiveTerminals.forEach(TerminalView.handleTerminal)
