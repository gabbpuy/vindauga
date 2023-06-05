# -*- coding: utf-8 -*-
from gettext import gettext as _

from vindauga.constants.command_codes import wnNoNumber, wpCyanWindow
from vindauga.constants.window_flags import wfGrow, wfZoom
from vindauga.gadgets.calendar import Calendar
from vindauga.types.rect import Rect
from vindauga.widgets.window import Window


class CalendarWindow(Window):

    name = 'CalendarWindow'

    def __init__(self):
        super().__init__(Rect(1, 1, 23, 11), _('Calendar'), wnNoNumber)

        r = self.getExtent()
        self.flags &= ~(wfZoom | wfGrow)
        self.growMode = 0

        self.palette = wpCyanWindow
        r.grow(-1, -1)
        self.insert(Calendar(r))
