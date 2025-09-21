# -*- coding: utf-8 -*-
from vindauga.constants.option_flags import ofFramed
from vindauga.utilities.math_utils import clamp
from vindauga.types.rect import Rect

from .param_text import ParamText


class Gauge(ParamText):
    FILL_CHAR = '█'
    BACK_CHAR = ' '
    # Partial 1/8 fills
    FILL_CHARS = '▏▎▍▌▋▊▉'

    name = 'Gauge'

    def __init__(self, bounds: Rect):
        super().__init__(bounds)
        self.options |= ofFramed
        self.currentValue = 0
        self.maxValue = 0

    def setParams(self, value: float, maxValue: float):
        self.maxValue = maxValue
        self.setValue(value)

    def setValue(self, value: float):
        self.currentValue = clamp(value, 0, self.maxValue)
        fill = self.currentValue * self.size.x / self.maxValue
        dill = int(fill)
        diff = fill - dill
        buffer = self.FILL_CHAR * dill
        if diff > .125:
            f = int(diff * 8) - 1
            buffer += self.FILL_CHARS[f]

        buffer = buffer.ljust(self.size.x, self.BACK_CHAR)
        self.setText(buffer)

    def getValue(self) -> float:
        return self.currentValue
