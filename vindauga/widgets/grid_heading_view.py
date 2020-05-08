# -*- coding: utf-8 -*-
import logging
from vindauga.constants.option_flags import ofSelectable
from vindauga.events.event import Event
from .grid_view import GridView

logger = logging.getLogger(__name__)


class GridHeadingView(GridView):

    def __init__(self, bounds, hScrollBar, vScrollBar, columnWidths, cellText, columns, rows):
        super().__init__(bounds, hScrollBar, vScrollBar, columnWidths)
        self.cellText = cellText
        self.setRange(columns, rows)
        """
        if hScrollBar:
            hScrollBar.maxVal = columns - 1
        if vScrollBar:
            vScrollBar.maxVal = rows - 1
        """

        self.headingMode = True

    def getText(self, column, row, maxChars):
        return self.cellText[row][column][:maxChars]
