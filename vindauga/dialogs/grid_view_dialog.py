# -*- coding: utf-8 -*-
from typing import Any, Optional, Sequence

from vindauga.constants.command_codes import cmListItemSelected
from vindauga.constants.grow_flags import gfGrowHiX, gfGrowHiY, gfGrowAll
from vindauga.constants.event_codes import evMouseDown, evKeyDown, evBroadcast
from vindauga.constants.keys import kbEnter, kbEsc
from vindauga.constants.option_flags import ofCentered, ofSelectable
from vindauga.constants.state_flags import sfSelected
from vindauga.events.event import Event
from vindauga.types.rect import Rect
from vindauga.widgets.dialog import Dialog
from vindauga.widgets.grid_heading_view import GridHeadingView
from vindauga.widgets.grid_view import cmUpdateItemNumber
from vindauga.widgets.grid_view_box import GridViewBox, cmListKeyEnter
from vindauga.widgets.input_line import InputLine
from vindauga.widgets.scroll_bar import ScrollBar


class GridViewDialog(Dialog):
    def __init__(self, bounds: Rect, title: str, headings: Sequence[str], headRows: int, gridData: Any,
                 columns: int, rows: int, columnWidth: Sequence[int], decimalPoint: Optional[Sequence[int]]):
        super().__init__(bounds, title)
        self.options |= ofCentered
        maxStr = 30

        r = Rect(1, 3, self.size.x - 2, self.size.y - 3)

        self.hScrollBar = ScrollBar(Rect(r.topLeft.x, r.bottomRight.y, r.bottomRight.x, r.bottomRight.y + 1))
        self.vScrollBar = ScrollBar(Rect(r.bottomRight.x, r.topLeft.y, r.bottomRight.x + 1, r.bottomRight.y))

        self.listBox = GridViewBox(r, self.hScrollBar, self.vScrollBar, columnWidth, gridData, columns, rows,
                                   decimalPoint)
        self.listBox.growMode = gfGrowHiX | gfGrowHiY
        self.headingBox = GridHeadingView(Rect(r.topLeft.x, r.topLeft.y - headRows, r.bottomRight.x, r.topLeft.y),
                                          columnWidth, headings, columns, headRows, self.listBox)
        self.headingBox.growMode = gfGrowHiX

        self.inputLine = InputLine(Rect(r.topLeft.x, r.topLeft.y, r.topLeft.x + columnWidth[0] - 1,
                                        r.topLeft.y + 1), maxStr)
        self.inputLine.hide()

        self.itemNumber = InputLine(
            Rect(r.bottomRight.x - 10, r.bottomRight.y + 1, r.bottomRight.x - 1, r.bottomRight.y + 2), 5)
        self.itemNumber.options &= ~ofSelectable
        self.itemNumber.growMode |= gfGrowAll
        self.itemNumber.setData(f'{self.listBox.focusedRow:2d},{self.listBox.focusedColumn:2d}')

        self.insert(self.hScrollBar)
        self.insert(self.vScrollBar)
        self.insert(self.headingBox)
        self.insert(self.listBox)
        self.insert(self.inputLine)
        self.insert(self.itemNumber)

    def handleEvent(self, event: Event):
        what = event.what

        if what == evMouseDown:
            if self.inputLine.state & sfSelected:
                self.inputLine.hide()
        elif what == evKeyDown:
            kc = event.keyDown.keyCode
            if self.inputLine.state & sfSelected:
                if kc == kbEsc:
                    self.inputLine.hide()
                    self.clearEvent(event)
                elif kc == kbEnter:
                    work = self.inputLine.getData()
                    self.listBox.putData(work.value)
                    self.inputLine.hide()
                    self.clearEvent(event)
        elif what == evBroadcast:
            emc = event.message.command
            if emc == cmListItemSelected:
                if self.inputLine.state & sfSelected:
                    self.inputLine.hide()
                else:
                    # Show empty line input
                    listBox: GridViewBox = event.message.infoPtr
                    mouseY = listBox.cursor.y
                    mouseX = listBox.cursor.x
                    self.inputLine.growTo(listBox.columnWidth[listBox.focusedColumn] - 1, 1)
                    self.inputLine.moveTo(mouseX, mouseY + 3)
                    # self.inputLine.setData('')
                    self.inputLine.setData(
                        listBox.getText(listBox.focusedColumn, listBox.focusedRow, self.inputLine.maxLen))
                    self.inputLine.show()
                self.clearEvent(event)
            elif emc == cmListKeyEnter:
                listBox: GridViewBox = event.message.infoPtr
                mouseY = listBox.cursor.y
                mouseX = listBox.cursor.x
                self.inputLine.growTo(listBox.columnWidth[listBox.focusedColumn] - 1, 1)
                self.inputLine.moveTo(mouseX, mouseY + 3)
                self.inputLine.setData(listBox.getText(listBox.focusedColumn, listBox.focusedRow,
                                                       self.inputLine.maxLen))
                self.inputLine.show()
                self.clearEvent(event)
            elif emc == cmUpdateItemNumber:
                self.itemNumber.setData(f'{self.listBox.focusedRow:2d},{self.listBox.focusedColumn:2d}')
                self.itemNumber.draw()
                self.clearEvent(event)
        super().handleEvent(event)
