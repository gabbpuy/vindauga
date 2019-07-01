# -*- coding: utf-8 -*-
import logging
from .static_text import StaticText

logger = logging.getLogger('vindauga.widgets.param_text')


class ParamText(StaticText):

    name = 'ParamText'

    def __init__(self, bounds):
        super().__init__(bounds, 0)
        self._str = ''

    def getText(self):
        return self._str or ''

    def __len__(self):
        return len(self._str)

    def getTextLen(self):
        return len(self)

    def setText(self, fmt, *args):
        self._str = fmt % args
        logger.info('Text is "%s" from %s, %s', self._str, fmt, args)
        self.drawView()

    def setFormatText(self, fmt, *args, **kwargs):
        self._str = fmt.format(*args, **kwargs)
        logger.info('Text is "%s" from %s, %s, %s', self._str, fmt, args, kwargs)
        self.drawView()
