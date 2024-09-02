# -*- coding: utf-8 -*-
import logging

import wcwidth
from vindauga.types.rect import Rect

from .static_text import StaticText


logger = logging.getLogger(__name__)


class ParamText(StaticText):

    name = 'ParamText'

    def __init__(self, bounds: Rect):
        super().__init__(bounds, ' ')
        self._str = ''

    def getText(self) -> str:
        return self._str or ''

    def __len__(self) -> int:
        return wcwidth.wcswidth(self._str)

    def getTextLen(self) -> int:
        return wcwidth.wcswidth(self._str)

    def setText(self, fmt: str, *args):
        self._str = fmt % args
        self.drawView()

    def setFormatText(self, fmt: str, *args, **kwargs):
        self._str = fmt.format(*args, **kwargs)
        self.drawView()
