# -*- coding: utf-8 -*-
from vindauga.constants.scrollbar_codes import sbHorizontal, sbVertical, sbHandleKeyboard
from vindauga.constants.option_flags import ofTileable
from vindauga.constants.std_dialog_commands import cmChangeDir
from vindauga.widgets.file_viewer import FileViewer
from vindauga.widgets.program import Program
from vindauga.widgets.window import Window

hlChangeDir = cmChangeDir


class FileWindow(Window):
    winNumber = 0
    name = "FileWindow"

    def __init__(self, filename):
        super().__init__(Program.desktop.getExtent(), filename, FileWindow.winNumber)
        FileWindow.winNumber += 1
        self.options |= ofTileable
        r = self.getExtent()
        r.grow(-1, -1)
        self.insert(FileViewer(r,
                               self.standardScrollBar(sbHorizontal | sbHandleKeyboard),
                               self.standardScrollBar(sbVertical | sbHandleKeyboard),
                               filename))
