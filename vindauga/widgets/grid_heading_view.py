# -*- coding: utf-8 -*-
import logging
from typing import Optional, Sequence

from vindauga.constants.event_codes import evMouseDown, meDoubleClick
from vindauga.events.event import Event
from vindauga.types.rect import Rect
from vindauga.widgets.grid_view_box import GridViewBox

from .grid_view import GridView

logger = logging.getLogger(__name__)


class GridHeadingView(GridView):
    icon = {
        False: ' ▲',
        True: ' ▼'
    }

    def __init__(self, bounds: Rect, columnWidths: Sequence[int], cellText: Sequence[str], columns: int, rows: int,
                 widget: Optional[GridViewBox] = None):
        self.headingMode = True
        super().__init__(bounds, None, None, columnWidths)
        self.cellText = list((list(c) for c in cellText))
        self.setRange(columns, rows)
        self.widget = widget
        self.sortedColumn = -1
        self.reversed = False

    def getText(self, column: int, row: int, maxChars: int) -> str:
        return self.cellText[row][column][:maxChars]

    def handleEvent(self, event: Event):
        if not self.widget:
            super().handleEvent(event)
            return

        newColumn = -1

        if event.what == evMouseDown and event.mouse.eventFlags & meDoubleClick:
            mouse = self.makeLocal(event.mouse.where)
            for newColumn in range(self.leftColumn, self.numColumns):
                if self.getColumnPosition(newColumn + 1) > mouse.x:
                    break
            if newColumn == self.sortedColumn:
                self.reversed = not self.reversed
            else:
                self.reversed = False

            self.sortData(newColumn)
            if self.sortedColumn >= 0:
                self.cellText[-1][self.sortedColumn] = self.cellText[-1][self.sortedColumn][:-2]

            self.sortedColumn = newColumn
            self.cellText[-1][self.sortedColumn] = self.cellText[-1][self.sortedColumn] + self.icon[self.reversed]
            self.draw()
            self.clearEvent(event)
        else:
            super().handleEvent(event)

    def reshape(self, data: list):
        """
        Reshape the 1D list into an m row x n column list
        """
        r = self.widget.numRows
        c = self.widget.numColumns

        if r * c != len(data):
            raise ValueError('Invalid new shape')
        return [data[tr * c:(tr + 1) * c] for tr in range(0, r)]

    def sortData(self, newColumn: int):
        reshaped = sorted(self.reshape(list(self.widget.cellData.values())), key=lambda x: x[newColumn].val,
                          reverse=self.reversed)
        for i in range(self.widget.numRows):
            for j in range(self.widget.numColumns):
                self.widget.cellData[i, j] = reshaped[i][j]
        self.widget.draw()
