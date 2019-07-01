# -*- coding: utf-8 -*-
import datetime

from vindauga.constants.event_codes import evMouseAuto, evKeyboard, evMouse, evMouseDown
from vindauga.constants.keys import kbDown, kbUp
from vindauga.constants.option_flags import ofSelectable
from vindauga.constants.state_flags import sfSelected
from vindauga.types.draw_buffer import DrawBuffer
from vindauga.types.view import View

monthNames = [_(s)
              for s in ('',
                        'January', 'February', 'March', 'April', 'May', 'June',
                        'July', 'August', 'September', 'October', 'November', 'December')
              ]

daysInMonth = [
    0, 31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31
]


def dayOfWeek(day, month, year):
    dd = datetime.date(year, month, day)
    return dd.isoweekday() % 7


class Calendar(View):
    name = 'Calendar'

    def __init__(self, r):
        super().__init__(r)
        self.options |= ofSelectable
        self.eventMask |= evMouseAuto

        self.now = datetime.date.today()

        self.year = self.now.year
        self.curYear = self.year
        self.month = self.now.month
        self.curMonth = self.month
        self.curDay = self.now.day
        self.drawView()

    def draw(self):
        current = 1 - dayOfWeek(1, self.month, self.year)
        days = daysInMonth[self.month]
        if self.month == 2:
            if (self.year % 4) == 0:
                days += 1

        buf = DrawBuffer()

        color = self.getColor(6)
        boldColor = self.getColor(7)

        buf.moveChar(0, ' ', color, 22)
        s1 = ' ▲ {:>9} {:4d} ▼ '.format(monthNames[self.month], self.year)
        buf.moveStr(0, s1, self.getColor(8))
        self.writeLine(0, 0, 22, 1, buf)

        buf.moveChar(0, ' ', color, 22)
        buf.moveStr(0, 'Su Mo Tu We Th Fr Sa', self.getColor(5))
        self.writeLine(0, 1, 22, 1, buf)

        for i in range(1, 7):
            buf.moveChar(0, ' ', color, 22)
            for j in range(7):
                if current < 1 or current > days:
                    buf.moveStr(j * 3, '   ', color)
                else:
                    s2 = '{:2d}'.format(current)

                    if (self.year == self.curYear and
                            self.month == self.curMonth and
                            current == self.curDay):
                        buf.moveStr(j * 3, s2, boldColor)
                    else:
                        buf.moveStr(j * 3, s2, color)
                current += 1

            self.writeLine(0, i + 1, 22, 1, buf)

    def handleEvent(self, event):
        super().handleEvent(event)
        if self.state & sfSelected:
            if (event.what & evMouse) and (evMouseDown or evMouseAuto):
                point = self.makeLocal(event.mouse.where)
                if point.y == 0:
                    if point.x == 18:
                        self.month += 1
                        if self.month > 12:
                            self.year += 1
                            self.month = 1
                        self.drawView()
                        self.clearEvent(event)
                    elif point.x == 1:
                        self.month -= 1
                        if self.month < 1:
                            self.year -= 1
                            self.month = 12
                        self.drawView()
                        self.clearEvent(event)
            elif event.what == evKeyboard:
                if event.keyDown.keyCode == '+' or event.keyDown.keyCode == kbDown:
                    self.month += 1
                    if self.month > 12:
                        self.year += 1
                        self.month = 1
                    self.drawView()
                    self.clearEvent(event)
                elif (event.keyDown.keyCode == '-' or
                      event.keyDown.keyCode == kbUp):
                    self.month -= 1
                    if self.month < 1:
                        self.year -= 1
                        self.month = 12
                    self.drawView()
                    self.clearEvent(event)
