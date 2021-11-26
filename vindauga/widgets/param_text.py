# -*- coding: utf-8 -*-
import logging
from .static_text import StaticText

logger = logging.getLogger(__name__)


class ParamText(StaticText):

    name = 'ParamText'

    def __init__(self, bounds):
        super().__init__(bounds, ' ')
        self._str = ''

    def getText(self):
        return self._str or ''

    def __len__(self):
        return len(self._str)

    def getTextLen(self):
        return len(self._str)

    def setText(self, fmt, *args):
        self._str = fmt % args
        self.drawView()

    def setFormatText(self, fmt, *args, **kwargs):
        self._str = fmt.format(*args, **kwargs)
        self.drawView()
