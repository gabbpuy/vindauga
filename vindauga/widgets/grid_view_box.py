# -*- coding: utf-8 -*-
from dataclasses import dataclass
import logging
from typing import Sequence

from vindauga.constants.event_codes import evMouseDown, evBroadcast, evKeyDown, meDoubleClick
from vindauga.constants.keys import kbEnter
from vindauga.events.event import Event
from vindauga.utilities.message import message
from vindauga.types.rect import Rect

from .grid_view import GridView, cmListItemSelected
from .scroll_bar import ScrollBar


logger = logging.getLogger(__name__)
cmListKeyEnter = 59


@dataclass
class ListRec:
    val: str
    show: bool


class GridViewBox(GridView):

    def __init__(self, bounds: Rect, hScrollBar: ScrollBar, vScrollBar: ScrollBar, columnWidths: Sequence[int],
                 cellData: dict, columns: int, rows: int, decimalPoint: Sequence[int]):
        super().__init__(bounds, hScrollBar, vScrollBar, columnWidths)
        self.cellData = cellData or {}
        self.decimalPoint = decimalPoint or [0,] * columns
        self.setRange(columns, rows)
        if hScrollBar:
            hScrollBar.maxVal = columns - 1
        if vScrollBar:
            vScrollBar.maxVal = rows - 1

    def getText(self, column: int, row: int, maxLen: int) -> str:
        data = self.cellData[row, column]
        if data.show:
            try:
                data = f'{float(data.val):>{self.columnWidth[column] - 2}.{self.decimalPoint[column]}f}'
            except ValueError:
                data = data.val
            return data
        return ''

    def handleEvent(self, event: Event):
        if event.what == evMouseDown and event.mouse.eventFlags & meDoubleClick:
            self.clearEvent(event)
            message(self.owner, evBroadcast, cmListItemSelected, self)
        elif event.what == evKeyDown and event.keyDown.keyCode == kbEnter:
            self.clearEvent(event)
            message(self.owner, evBroadcast, cmListKeyEnter, self)

        super().handleEvent(event)

    def putData(self, text: str):
        self.cellData[self.focusedRow, self.focusedColumn] = ListRec(val=text, show=True)
        self.draw()
