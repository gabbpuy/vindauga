# -*- coding: utf-8 -*-
import logging
import os

from vindauga.constants.buttons import bfDefault, bfNormal
from vindauga.constants.command_codes import cmOK, cmCancel
from vindauga.constants.message_flags import mfError, mfOKButton
from vindauga.constants.event_codes import evCommand, evBroadcast
from vindauga.constants.option_flags import ofCentered
from vindauga.constants.std_dialog_commands import (cmFileOpen, cmFileReplace, cmFileClear, cmFileDoubleClicked,
                                                    cmFileInit)
from vindauga.dialogs.message_box import messageBox
from vindauga.misc.util import relativePath, isWild, splitPath, validFileName, getCurDir, pathValid, fexpand, nameLength
from vindauga.types.rect import Rect
from vindauga.widgets.button import Button
from vindauga.widgets.dialog import Dialog
from vindauga.widgets.file_info_pane import FileInfoPane
from vindauga.widgets.file_input_line import FileInputLine
from vindauga.widgets.file_list import FileList
from vindauga.widgets.history import History
from vindauga.widgets.label import Label
from vindauga.widgets.scroll_bar import ScrollBar

logger = logging.getLogger(__name__)

ffOpen = 0x0001
ffSaveAs = 0x0002

cmOpenDialogOpen = 100
cmOpenDialogReplace = 101

fdOKButton = 0x0001  # Put an OK button in the dialog
fdOpenButton = 0x0002  # Put an Open button in the dialog
fdReplaceButton = 0x0004  # Put a Replace button in the dialog
fdClearButton = 0x0008  # Put a Clear button in the dialog
fdHelpButton = 0x0010  # Put a Help button in the dialog
fdNoLoadDir = 0x0100  # Do not load the current directory contents into the dialog at Init. This means you intend to
# __change the WildCard by using SetData or store the dialog on a stream.


class FileDialog(Dialog):
    filesText = _('~F~iles')
    openText = _('~O~pen')
    okText = _('O~K~')
    replaceText = _('~R~eplace')
    clearText = _('~C~lear')
    cancelText = _('Cancel')
    helpText = _('~H~elp')
    invalidDriveText = _('Invalid drive or directory')
    invalidFileText = _('Invalid file name.')

    def __init__(self, wildCard, title, inputLabel, options, histId):
        super().__init__(Rect(15, 1, 64, 20), title)

        self.directory = ''
        self.options |= ofCentered
        self.wildCard = wildCard
        self.filename = FileInputLine(Rect(3, 3, 31, 4), 79)
        self.filename.setData(self.wildCard)
        self.insert(self.filename)

        self.insert(Label(Rect(2, 2, 3 + nameLength(inputLabel), 3), inputLabel, self.filename))
        self.insert(History(Rect(31, 3, 34, 4), self.filename, histId))

        sb = ScrollBar(Rect(3, 14, 34, 15))
        self.insert(sb)
        self.fileList = FileList(Rect(3, 6, 34, 14), sb)
        self.insert(self.fileList)
        self.insert(Label(Rect(2, 5, 8, 6), self.filesText, self.fileList))

        opt = bfDefault
        r = Rect(35, 3, 46, 5)

        if options & fdOpenButton:
            self.insert(Button(r, self.openText, cmFileOpen, opt))
            opt = bfNormal
            r.topLeft.y += 3
            r.bottomRight.x += 3

        if options & fdOKButton:
            self.insert(Button(r, self.okText, cmFileOpen, opt))
            opt = bfNormal
            r.topLeft.y += 3
            r.bottomRight.y += 3

        if options & fdReplaceButton:
            self.insert(Button(r, self.replaceText, cmFileReplace, opt))
            r.topLeft.y += 3
            r.bottomRight.y += 3

        if options & fdClearButton:
            self.insert(Button(r, self.clearText, cmFileClear, opt))
            r.topLeft.y += 3
            r.bottomRight.y += 3

        self.insert(FileInfoPane(Rect(1, 16, 48, 18)))

        self.selectNext(False)
        if not (options & fdNoLoadDir):
            self._readCurrentDirectory()

    def getFilename(self):
        buf = self.filename.getDataString().strip()
        if relativePath(buf):
            buf = os.path.join(self.directory, buf)
        return fexpand(buf)

    def handleEvent(self, event):
        super().handleEvent(event)
        if event.what == evCommand:
            if event.message.command in {cmFileOpen, cmFileReplace, cmFileClear}:
                self.endModal(event.message.command)
                self.clearEvent(event)
        elif event.what == evBroadcast and event.message.command == cmFileDoubleClicked:
            event.what = evCommand
            event.message.command = cmOK
            self.putEvent(event)
            self.clearEvent(event)

    def setData(self, data):
        super().setData(data)
        if data and isWild(data):
            self.valid(cmFileInit)
            self.filename.select()

    def getData(self):
        return self.getFilename()

    def valid(self, command):
        if not command:
            return True

        if super().valid(command):
            if command not in (cmCancel, cmFileClear):
                filename = self.getFilename()
                if isWild(filename):
                    path, name = splitPath(filename)
                    if self.checkDirectory(path):
                        self.directory = path
                        self.wildCard = name
                        if command != cmFileInit:
                            self.fileList.select()
                        self.fileList.readDirectory(self.directory, self.wildCard)
                elif os.path.isdir(filename):
                    if self.checkDirectory(filename):
                        self.directory = filename
                        if command != cmFileInit:
                            self.fileList.select()
                        self.fileList.readDirectory(self.directory, self.wildCard)
                elif validFileName(filename):
                    return True
                else:
                    messageBox(self.invalidFileText, mfError, [mfOKButton])
                    return False
            else:
                return True
        return False

    def shutdown(self):
        self.filename = None
        self.fileList = None
        super().shutdown()

    def _readCurrentDirectory(self):
        self.directory = getCurDir()
        self.fileList.readDirectory(self.wildCard)

    def checkDirectory(self, pth):
        if pathValid(pth):
            return True

        messageBox(self.invalidDriveText, mfError, [mfOKButton])
        self.filename.select()
        return False
