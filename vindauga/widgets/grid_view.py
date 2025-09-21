# -*- coding: utf-8 -*-
from gettext import gettext as _
import logging
from typing import Optional, Sequence

from vindauga.constants.command_codes import cmScrollBarClicked, cmScrollBarChanged, cmListItemSelected
from vindauga.constants.event_codes import evBroadcast, evKeyDown, evMouseDown, evMouseAuto, evMouseMove, meDoubleClick
from vindauga.constants.keys import (kbUp, kbDown, kbRight, kbLeft, kbPgDn, kbPgUp, kbHome, kbEnd, kbCtrlPgDn,
                                     kbCtrlPgUp, kbTab, kbShiftTab)

from vindauga.constants.state_flags import sfSelected, sfActive
from vindauga.constants.option_flags import ofFirstClick, ofSelectable
from vindauga.events.event import Event

from vindauga.utilities.input.character_codes import SPECIAL_CHARS
from vindauga.utilities.message import message
from vindauga.utilities.input.key_utils import ctrlToArrow
from vindauga.types.draw_buffer import DrawBuffer
from vindauga.types.palette import Palette
from vindauga.types.rect import Rect
from vindauga.types.view import View
from vindauga.widgets.scroll_bar import ScrollBar

logger = logging.getLogger(__name__)

cmUpdateItemNumber = 901


class GridView(View):
    cpGridView = '\x1A\x1A\x1B\x1C\x1D\x06'

    def __init__(self, bounds: Rect, hScrollBar: Optional[ScrollBar], vScrollBar: Optional[ScrollBar],
                 columnWidths: Sequence[int]):
        super().__init__(bounds)
        self.leftColumn = 0
        self.topRow = 0
        self.focusedColumn = 0
        self.focusedRow = 0
        self.numColumns = 0
        self.numRows = 0
        self.headingMode = False

        self.columnWidth = columnWidths
        self.options |= (ofFirstClick | ofSelectable)
        self.eventMask |= evBroadcast

        if vScrollBar:
            pgStep = self.size.y - 1
            arStep = 1
            vScrollBar.setStep(pgStep, arStep)

        if hScrollBar:
            hScrollBar.setStep(self.size.x, 1)

        self.hScrollBar = hScrollBar
        self.vScrollBar = vScrollBar

    def draw(self):
        b = DrawBuffer()
        focusedColor = self.getColor(3)
        selectedColor = self.getColor(4)

        if self.headingMode:
            normalColor = self.getColor(6)
        elif self.state & (sfSelected | sfActive) == (sfSelected | sfActive):
            normalColor = self.getColor(1)
        else:
            normalColor = self.getColor(2)

        posColumn = 0
        for column in range(self.leftColumn, self.numColumns + 1):
            if posColumn > self.size.x:
                break
            if column < self.numColumns:
                thisWidth = self.columnWidth[column]
            else:
                thisWidth = self.size.x - posColumn + 1
            for i in range(self.size.y):
                row = i + self.topRow
                if self.headingMode:
                    color = normalColor
                    specialChar = 4
                elif ((self.state & (sfSelected | sfActive)) == (sfSelected | sfActive) and
                      self.isSelected(column, row) and self.numRows):
                    color = focusedColor
                    self.setCursor(posColumn + 1, i)
                    specialChar = 0
                elif column < self.numColumns and row < self.numRows and self.isSelected(column, row):
                    color = selectedColor
                    specialChar = 2
                else:
                    color = normalColor
                    specialChar = 4

                b.moveChar(0, ' ', color, thisWidth)
                if column < self.numColumns and row < self.numRows:
                    text = self.getText(column, row, thisWidth)
                    b.moveStr(1, text, color)
                    if self.showMarkers:
                        b.putChar(0, SPECIAL_CHARS[specialChar], color)
                        b.putChar(thisWidth - 2, SPECIAL_CHARS[specialChar + 1], color)
                elif not (i or column):
                    b.moveStr(1, _('<empty>'), self.getColor(1))

                if not self.headingMode and column < self.numColumns - 1 and row < self.numRows:
                    b.moveChar(thisWidth - 1, '│', self.getColor(5), 1)
                self.writeLine(posColumn, i, thisWidth, 1, b)
            posColumn += thisWidth

    def focusItem(self, column: int, row: int):
        self.focusedColumn = column
        if self.hScrollBar and not self.headingMode:
            self.hScrollBar.setValue(column)

        if column < self.leftColumn:
            self.leftColumn = column
        else:
            while self.getColumnPosition(column + 1) > self.size.x:
                self.leftColumn += 1

        self.focusedRow = row

        if self.vScrollBar and not self.headingMode:
            self.vScrollBar.setValue(row)

        if row < self.topRow:
            self.topRow = row
        elif row >= self.topRow + self.size.y:
            self.topRow = row - self.size.y + 1

        if not self.headingMode:
            message(self.owner, evBroadcast, cmUpdateItemNumber, self)

    def focusItemNum(self, column: int, row: int):
        if not self.numRows:
            return
        column = max(min(column, self.numColumns - 1), 0)
        row = max(min(row, self.numRows - 1), 0)
        self.focusItem(column, row)

    def getPalette(self) -> Palette:
        return Palette(self.cpGridView)

    def getText(self, _column: int, _row: int, _maxChars: int) -> str:
        return ''

    def isSelected(self, column: int, row: int) -> bool:
        return column == self.focusedColumn and row == self.focusedRow

    def handleEvent(self, event: Event):
        super().handleEvent(event)

        mouseAutosToSkip = 4

        newColumn = oldColumn = self.focusedColumn
        newRow = oldRow = self.focusedRow

        if event.what == evMouseDown:
            mouse = self.makeLocal(event.mouse.where)
            for newColumn in range(self.leftColumn, self.numColumns):
                if self.getColumnPosition(newColumn + 1) > mouse.x:
                    break

            newRow = mouse.y + self.topRow
            count = 0

            running = True
            while running:
                if newColumn != oldColumn or newRow != oldRow:
                    self.focusItemNum(self.focusedColumn, newRow)
                oldColumn = newColumn
                oldRow = newRow
                mouse = self.makeLocal(event.mouse.where)
                if self.mouseInView(event.mouse.where):
                    for newColumn in range(self.leftColumn, self.numColumns):
                        if self.getColumnPosition(newColumn + 1) > mouse.x:
                            break
                    newRow = mouse.y + self.topRow
                else:
                    if event.what == evMouseAuto:
                        count += 1
                    if count == mouseAutosToSkip:
                        count = 0
                        if mouse.x < 0:
                            newColumn = self.focusedColumn - 1
                        elif mouse.x >= self.size.x:
                            newColumn = self.focusedColumn + 1

                        if mouse.y < 0:
                            newRow = self.focusedRow - 1
                        elif mouse.y >= self.size.y:
                            newRow = self.focusedRow + 1
                running = self.mouseEvent(event, evMouseMove | evMouseAuto)

            self.focusItemNum(newColumn, newRow)
            if (event.mouse.eventFlags & meDoubleClick and self.focusedColumn < self.numColumns and
                    self.focusedRow < self.numRows):
                self.selectItem(self.focusedColumn, self.focusedRow)
            self.clearEvent(event)
        elif event.what == evKeyDown:
            if (event.keyDown.charScan.charCode == ' ' and
                    self.focusedColumn < self.numColumns and self.focusedRow < self.numRows):
                self.selectItem(self.focusedColumn, self.focusedRow)
            else:
                key = ctrlToArrow(event.keyDown.keyCode)
                if key == kbUp:
                    newRow = oldRow - 1
                elif key == kbDown:
                    newRow = oldRow + 1
                elif key == kbRight:
                    newColumn = oldColumn + 1
                elif key == kbLeft:
                    newColumn = oldColumn - 1
                elif key == kbPgDn:
                    newRow = oldRow + self.size.y
                elif key == kbPgUp:
                    newRow = oldRow - self.size.y
                elif key == kbHome:
                    newRow = self.topRow
                    newColumn = self.leftColumn
                elif key == kbEnd:
                    newRow = self.topRow + self.size.y - 1
                    for newColumn in range(self.leftColumn, self.numColumns):
                        if self.getColumnPosition(newColumn + 1) > self.size.x:
                            break
                elif key == kbCtrlPgDn:
                    newRow = self.numRows - 1
                elif key == kbCtrlPgUp:
                    newRow = 0
                elif key == kbTab:
                    newColumn = oldColumn + 1
                    if newColumn >= self.numColumns:
                        newRow = oldRow + 1
                        if newRow >= self.numRows:
                            newRow = 0
                        newColumn = 0
                elif key == kbShiftTab:
                    if oldColumn == 0:
                        if oldRow == 0:
                            oldRow = self.numRows
                        newRow = oldRow - 1
                        oldColumn = self.numColumns
                    newColumn = oldColumn - 1
                else:
                    return
            self.focusItemNum(newColumn, newRow)
            self.clearEvent(event)
        elif event.what == evBroadcast:
            if self.options & ofSelectable:
                if event.message.command == cmScrollBarClicked and event.message.infoPtr in (
                        self.hScrollBar, self.vScrollBar):
                    self.select()
                elif event.message.command == cmScrollBarChanged:
                    if event.message.infoPtr in (self.hScrollBar, self.vScrollBar):
                        self.focusItemNum(self.hScrollBar.value, self.vScrollBar.value)
                        self.drawView()

    def selectItem(self, _column: int, _row: int):
        message(self.owner, evBroadcast, cmListItemSelected, self)

    def setRange(self, columns: int, rows: int):
        self.numColumns = columns
        if self.hScrollBar:
            if self.focusedColumn > columns:
                self.focusedColumn = 0
            self.hScrollBar.setParams(self.focusedColumn, 0, columns - 1, self.hScrollBar.pageStep,
                                      self.hScrollBar.arrowStep)

        self.numRows = rows
        if self.vScrollBar:
            if self.focusedRow > rows:
                self.focusedRow = 0
            self.vScrollBar.setParams(self.focusedRow, 0, rows - 1, self.vScrollBar.pageStep, self.vScrollBar.arrowStep)

    def setState(self, state: int, enable: bool):
        super().setState(state, enable)

        if state & (sfSelected | sfActive):
            if self.hScrollBar:
                if self.getState(sfActive):
                    self.hScrollBar.show()
                else:
                    self.hScrollBar.hide()

            if self.vScrollBar:
                if self.getState(sfActive):
                    self.vScrollBar.show()
                else:
                    self.vScrollBar.hide()
            self.drawView()

    def getColumnPosition(self, column: int) -> int:
        position = 0
        for i in range(self.leftColumn, max(self.numColumns, column)):
            if i == column:
                break
            position += (self.columnWidth[i])
        return position

    def shutdown(self):
        self.hScrollBar = None
        self.vScrollBar = None
        super().shutdown()
