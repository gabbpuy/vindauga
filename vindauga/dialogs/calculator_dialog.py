# -*- coding: utf-8 -*-
from gettext import gettext as _
from vindauga.constants.buttons import bfNormal, bfBroadcast
from vindauga.constants.option_flags import ofSelectable, ofFirstClick
from vindauga.gadgets.calculator import Calculator, cmCalcButton
from vindauga.types.rect import Rect
from vindauga.widgets.button import Button
from vindauga.widgets.dialog import Dialog


calcButtons = [
    'C', '←', '%', '±',
    '7', '8', '9', '÷',
    '4', '5', '6', '×',
    '1', '2', '3', '-',
    '0', '.', '=', '+'
]


class CalculatorDialog(Dialog):
    def __init__(self):
        super().__init__(Rect(5, 3, 29, 19), _('Calculator'))
        self.options |= ofFirstClick

        for i, c in enumerate(calcButtons):
            x = (i % 4) * 5 + 2
            y = (i // 4) * 2 + 4
            r = Rect(x, y, x + 5, y + 2)

            tv = Button(r, c, cmCalcButton, bfNormal | bfBroadcast)
            tv.options &= ~ofSelectable
            self.insert(tv)

        r = Rect(3, 2, 21, 3)
        self.insert(Calculator(r))
