# -*- coding: utf-8 -*-
import logging

from vindauga.constants.command_codes import (hcNoContext)
from vindauga.constants.event_codes import evMouseDown, evMouseMove, evKeyDown
from vindauga.constants.keys import kbUp, kbDown, kbLeft, kbRight
from vindauga.constants.option_flags import ofSelectable, ofFirstClick, ofPreProcess, ofPostProcess
from vindauga.constants.state_flags import sfSelected, sfFocused
from vindauga.misc.character_codes import SPECIAL_CHARS, getAltCode
from vindauga.misc.util import ctrlToArrow, nameLength, hotKey
from vindauga.types.draw_buffer import DrawBuffer
from vindauga.types.palette import Palette
from vindauga.types.records.data_record import DataRecord
from vindauga.types.view import View

logger = logging.getLogger(__name__)


class Cluster(View):
    name = 'Cluster'
    cpCluster = '\x10\x11\x12\x12\x1f'

    def __init__(self, bounds, strings):
        super().__init__(bounds)
        self._value = 0
        self._sel = 0
        self._strings = strings[:]
        self._enableMask = 0xFFFFFFFF

        self.options |= ofSelectable | ofFirstClick | ofPreProcess | ofPostProcess
        self.setCursor(2, 0)
        self.showCursor()

    def drawBox(self, icon, marker):
        s = ' ' + marker
        self.drawMultiBox(icon, s)

    def drawMultiBox(self, icon, marker):
        b = DrawBuffer()

        cNorm = self.getColor(0x0301)
        cSel = self.getColor(0x0402)
        cDis = self.getColor(0x0505)

        for i in range(self.size.y):
            b.moveChar(0, ' ', cNorm, self.size.x)

            for j in range((len(self._strings) - 1) // self.size.y + 1):
                cur = j * self.size.y + i
                if cur < len(self._strings):
                    col = self.__column(cur)

                    if col < self.size.x:
                        if not self.buttonState(cur):
                            color = cDis
                        elif (cur == self._sel) and (self.state & sfSelected):
                            color = cSel
                        else:
                            color = cNorm
                        b.moveChar(col, ' ', color, self.size.x - col)
                        b.moveCStr(col, icon, color)
                        b.putChar(col + 2, marker[self.multiMark(cur)])
                        b.moveCStr(col + 5, self._strings[cur], color)

                        if (self.showMarkers and ((self.state & sfSelected) != 0 and
                                                  cur == self._sel)):
                            b.putChar(col, SPECIAL_CHARS[0])
                            b.putChar(self.__column(cur + self.size.y) - 1, SPECIAL_CHARS[1])

            self.writeBuf(0, i, self.size.x, 1, b)
        self.setCursor(self.__column(self._sel) + 2, self.__row(self._sel))

    def getData(self):
        rec = DataRecord()
        self.drawView()
        rec.value = self._value
        return rec

    def getHelpCtx(self):
        if self.helpCtx == hcNoContext:
            return hcNoContext
        return self.helpCtx + self._sel

    def getPalette(self):
        palette = Palette(self.cpCluster)
        return palette

    def handleEvent(self, event):
        super().handleEvent(event)

        if not self.options & ofSelectable:
            return event

        if event.what == evMouseDown:
            mouse = self.makeLocal(event.mouse.where)
            i = self.__findSel(mouse)

            if i != -1 and self.buttonState(i):
                self._sel = i
            self.drawView()

            done = False
            while not done:
                mouse = self.makeLocal(event.mouse.where)
                if self.__findSel(mouse) == self._sel and self.buttonState(self._sel):
                    self.showCursor()
                else:
                    self.hideCursor()
                done = not (self.mouseEvent(event, evMouseMove))
            self.showCursor()
            mouse = self.makeLocal(event.mouse.where)
            if self.__findSel(mouse) == self._sel:
                self.press(self._sel)
                self.drawView()

            self.clearEvent(event)
        elif event.what == evKeyDown:
            self._handleKeyDownEvent(event)

    def _handleKeyDownEvent(self, event):
        s = self._sel
        cta = ctrlToArrow(event.keyDown.keyCode)
        if cta == kbUp:
            if self.state & sfFocused:
                i = 0
                done = False
                while not done:
                    i += 1
                    s -= 1
                    if s < 0:
                        s = len(self._strings) - 1
                    done = (self.buttonState(s) or i > len(self._strings))
                self.__moveSel(i, s)
                self.clearEvent(event)
        elif cta == kbDown:
            if self.state & sfFocused:
                i = 0
                done = False
                while not done:
                    i += 1
                    s += 1
                    if s >= len(self._strings):
                        s = 0
                    done = (self.buttonState(s) or i > len(self._strings))
                self.__moveSel(i, s)
                self.clearEvent(event)
        elif cta == kbRight:
            if self.state & sfFocused:
                i = 0
                done = False
                while not done:
                    i += 1
                    s += self.size.y

                    if s >= len(self._strings):
                        s = (s + 1) % self.size.y
                        if s >= len(self._strings):
                            s = 0
                    done = (self.buttonState(s) or (i > len(self._strings)))
                self.__moveSel(i, s)
                self.clearEvent(event)
        elif cta == kbLeft:
            if self.state & sfFocused:
                i = 0
                done = False
                while not done:
                    i += 1
                    if s > 0:
                        s -= self.size.y
                        if s < 0:
                            s = ((len(self._strings) + self.size.y - 1) // self.size.y) * self.size.y + s - 1
                            s %= len(self._strings)
                    else:
                        s = len(self._strings) - 1
                    done = (self.buttonState(s) or (i > len(self._strings)))
                self.__moveSel(i, s)
                self.clearEvent(event)
        else:
            for i, s in enumerate(self._strings):
                c = hotKey(s)

                if getAltCode(c) == event.keyDown.keyCode or ((self.owner.phase == self.phPostProcess or
                                                               (self.state & sfFocused) != 0) and c != 0 and
                                                              event.keyDown.charScan.charCode.upper() == c):
                    if self.buttonState(i):
                        if self.focus():
                            self._sel = i
                            self.movedTo(self._sel)
                            self.press(self._sel)
                            self.drawView()
                        self.clearEvent(event)
                    return
            if event.keyDown.charScan.charCode == ' ' and (self.state & sfFocused):
                self.press(self._sel)
                self.drawView()
                self.clearEvent(event)

    def setButtonState(self, mask, enable):
        if not enable:
            self._enableMask &= ~mask
        else:
            self._enableMask |= mask

        n = len(self._strings)

        if n < 64:
            testMask = (1 << n) - 1
            if self._enableMask & testMask:
                self.options |= ofSelectable
            else:
                self.options &= ~ofSelectable

    def setData(self, rec):
        self._value = rec
        self.drawView()

    def setState(self, state, enable):
        super().setState(state, enable)

        if state == sfSelected:
            i = 0
            s = self._sel - 1
            for i in range(len(self._strings)):
                s = (s + 1) % len(self._strings)
                if self.buttonState(s):
                    break

            self.__moveSel(i, s)
        self.drawView()

    def mark(self, item):
        return False

    def multiMark(self, item):
        return self.mark(item)

    def movedTo(self, *args):
        pass

    def press(self, *args):
        pass

    def buttonState(self, item):
        if item >= 64:
            return False

        return bool(self._enableMask & (1 << item))

    def __row(self, item):
        return item % self.size.y

    def __column(self, item):
        if item < self.size.y:
            return 0
        width = 0
        col = -6
        cellLength = 0
        for i in range(item + 1):
            if i % self.size.y == 0:
                col += width + 6
                width = 0

            if i < len(self._strings):
                cellLength = nameLength(self._strings[i])

            if cellLength > width:
                width = cellLength
        return col

    def __findSel(self, p):
        r = self.getExtent()
        if p not in r:
            return -1
        else:
            i = 0
            while p.x >= self.__column(i + self.size.y):
                i += self.size.y

            s = i + p.y

            if s >= len(self._strings):
                return -1

        return s

    def __moveSel(self, i, s):
        if i < len(self._strings):
            self._sel = s
            self.movedTo(self._sel)
            self.drawView()
