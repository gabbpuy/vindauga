# -*- coding: utf-8 -*-
from pathlib import Path
from typing import Optional, Union

from vindauga.constants.edit_command_codes import cmUpdateTitle
from vindauga.constants.event_codes import evBroadcast
from vindauga.constants.option_flags import ofTileable
from vindauga.types.point import Point
from vindauga.types.rect import Rect
from .file_editor import FileEditor
from .indicator import Indicator
from .scroll_bar import ScrollBar
from .window import Window

minEditWinSize = Point(24, 6)


class EditWindow(Window):

    clipboardTitle = _('Clipboard')
    untitled = _('Untitled')

    def __init__(self, bounds: Rect, fileName: Optional[Union[str, Path]], windowNumber: int):
        super().__init__(bounds, '', windowNumber)
        self.min = None
        self.options |= ofTileable

        self.hScrollBar = ScrollBar(Rect(18, self.size.y - 1, self.size.x - 2, self.size.y))
        self.hScrollBar.hide()
        self.insert(self.hScrollBar)

        self.vScrollBar = ScrollBar(Rect(self.size.x - 1, 1, self.size.x, self.size.y - 1))
        self.vScrollBar.hide()
        self.insert(self.vScrollBar)

        self.indicator = Indicator(Rect(2, self.size.y - 1, 16, self.size.y))
        self.indicator.hide()
        self.insert(self.indicator)

        r = self.getExtent()
        r.grow(-1, -1)
        self.editor = FileEditor(r, self.hScrollBar, self.vScrollBar, self.indicator, fileName)
        self.insert(self.editor)

    def close(self):
        if self.editor.isClipboard():
            self.hide()
        else:
            super().close()

    def getTitle(self, *args):
        if self.editor.isClipboard():
            return self.clipboardTitle
        elif not self.editor.fileName:
            return self.untitled
        return self.editor.fileName

    def handleEvent(self, event):
        super().handleEvent(event)

        if event.what == evBroadcast and event.message.command == cmUpdateTitle:
            if self.frame:
                self.frame.drawView()
            self.clearEvent(event)

    def sizeLimits(self, minLimit, maxLimit):
        super().sizeLimits(minLimit, maxLimit)
        self.min = minEditWinSize
