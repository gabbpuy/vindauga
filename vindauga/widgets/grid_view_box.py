# -*- coding: utf-8 -*-
from dataclasses import dataclass
import logging

from vindauga.constants.event_codes import evMouseDown, evBroadcast, evKeyDown, meDoubleClick
from vindauga.constants.keys import kbEnter
from vindauga.misc.message import message
from .grid_view import GridView, cmListItemSelected

logger = logging.getLogger(__name__)
cmListKeyEnter = 59


@dataclass
class ListRec:
    val: str
    show: bool


class GridViewBox(GridView):

    def __init__(self, bounds, hScrollBar, vScrollBar, columnWidths, cellData, columns, rows, decimalPoint):
        super().__init__(bounds, hScrollBar, vScrollBar, columnWidths)
        self.cellData = cellData or {}
        self.decimalPoint = decimalPoint
        self.setRange(columns, rows)
        if hScrollBar:
            hScrollBar.maxVal = columns - 1
        if vScrollBar:
            vScrollBar.maxVal = rows - 1

    def getText(self, column, row, maxLen):
        data = self.cellData[row, column]
        if data.show:
            try:

                data = '{0:>{w}.{prec}f}'.format(float(data.val),
                                                 w=self.columnWidth[column] - 2,
                                                 prec=self.decimalPoint[column]
                                                 )
            except ValueError:
                data = data.val
            return data
        return ''

    def handleEvent(self, event):
        if event.what == evMouseDown and event.mouse.eventFlags & meDoubleClick:
            self.clearEvent(event)
            message(self.owner, evBroadcast, cmListItemSelected, self)
        elif event.what == evKeyDown and event.keyDown.keyCode == kbEnter:
            self.clearEvent(event)
            message(self.owner, evBroadcast, cmListKeyEnter, self)

        super().handleEvent(event)

    def putData(self, text):
        self.cellData[self.focusedRow, self.focusedColumn] = ListRec(val=text, show=True)
        self.draw()
