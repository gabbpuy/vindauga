# -*- coding: utf-8 -*-
from gettext import gettext as _
import itertools
import textwrap

import unicodedata

from vindauga.types.collections.string_collection import StringCollection
from vindauga.utilities.text.text import Text
from vindauga.constants.message_flags import mfError, mfOKButton
from vindauga.constants.grow_flags import gfGrowHiX, gfGrowHiY
from vindauga.constants.state_flags import sfExposed
from vindauga.dialogs.message_box import messageBox
from vindauga.types.draw_buffer import DrawBuffer
from vindauga.types.rect import Rect

from .scroll_bar import ScrollBar
from .scroller import Scroller




class FileViewer(Scroller):
    name = 'FileViewer'

    def __init__(self, bounds: Rect, hScrollBar: ScrollBar, vScrollBar: ScrollBar, fileName: str, wrap: bool = True):
        super().__init__(bounds, hScrollBar, vScrollBar)
        self.growMode = gfGrowHiX | gfGrowHiY
        self.fileLines = None
        self.isValid = True
        self.fileName = fileName
        self.wrap = wrap
        self.readFile(fileName)

    def draw(self):
        c = self.getColor(0x0301)
        for i in range(self.size.y):
            b = DrawBuffer()
            b.moveChar(0, ' ', c, self.size.x)
            if self.delta.y + i < len(self.fileLines):
                p = self.fileLines[self.delta.y + i]
                if p:
                    s = unicodedata.normalize('NFC', p.rstrip('\n\r'))
                    b.moveStr(0, s, c, maxWidth=self.size.x, strOffset=self.delta.x)
            self.writeBuf(0, i, self.size.x, 1, b)

    def scrollDraw(self):
        super().scrollDraw()
        self.draw()

    def readFile(self, fName: str):
        self._limit.x = 0
        self.fileName = fName
        self.fileLines = StringCollection()

        try:
            fileToView = open(fName, 'rt', encoding='utf-8')
        except OSError:
            messageBox(_('Invalid drive or directory'), mfError, [mfOKButton,])
            self.isValid = False
            return

        lines = fileToView.readlines()
        if self.wrap:
            wrapped = (
                textwrap.wrap(line + '\n', self.size.x - 1, expand_tabs=True, tabsize=4)
                for line in lines)
            lines = itertools.chain(*wrapped)

        self.fileLines.extend(lines)
        self._limit.y = len(self.fileLines)
        if self.fileLines:
            self._limit.x = max(Text.width(line.rstrip('\n\r')) for line in self.fileLines)

    def setState(self, state: int, enable: bool):
        super().setState(state, enable)
        if enable and (state & sfExposed):
            self.setLimit(self._limit.x, self._limit.y)

    def valid(self, command: int) -> bool:
        return self.isValid
