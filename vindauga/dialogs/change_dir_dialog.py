# -*- coding: utf-8 -*-
from gettext import gettext as _
import logging
import os
import pathlib
from typing import Union

from vindauga.constants.buttons import bfDefault, bfNormal
from vindauga.constants.command_codes import cmOK, cmHelp
from vindauga.constants.message_flags import mfError, mfOKButton
from vindauga.constants.event_codes import evCommand
from vindauga.constants.option_flags import ofCentered
from vindauga.constants.std_dialog_commands import (cmChangeDir, cdHelpButton, cdNoLoadDir, cmRevert,
                                                    cmDirSelection)
from vindauga.dialogs.message_box import messageBox
from vindauga.events.event import Event
from vindauga.utilities.filesystem.path_utils import getCurDir, fexpand
from vindauga.types.records.data_record import DataRecord
from vindauga.types.rect import Rect
from vindauga.widgets.button import Button
from vindauga.widgets.dialog import Dialog
from vindauga.widgets.dir_list_box import DirListBox
from vindauga.widgets.history import History
from vindauga.widgets.input_line import InputLine
from vindauga.widgets.label import Label
from vindauga.widgets.scroll_bar import ScrollBar

logger = logging.getLogger(__name__)


class ChangeDirDialog(Dialog):
    changeDirTitle = _('Change Directory')
    dirNameText = _('Directory ~N~ame')
    dirTreeText = _('Directory ~T~ree')
    chDirText = _('~C~hdir')
    okText = _('O~K~')
    helpText = _('~H~elp')
    invalidText = _('Invalid Directory')
    drivesText = _('Drives')

    def __init__(self, options, historyId):
        super().__init__(Rect(16, 2, 64, 20), self.changeDirTitle)
        self.options |= ofCentered
        self.dirInput = InputLine(Rect(3, 3, 30, 4), 68)
        self.insert(self.dirInput)

        self.insert(Label(Rect(2, 2, 17, 3), self.dirNameText, self.dirInput))
        self.insert(History(Rect(30, 3, 33, 4), self.dirInput, historyId))
        sb = ScrollBar(Rect(32, 6, 33, 16))
        self.insert(sb)
        self.dirList = DirListBox(Rect(3, 6, 32, 16), sb)
        self.insert(self.dirList)
        self.insert(Label(Rect(2, 5, 17, 6), self.dirTreeText, self.dirList))

        self.okButton = Button(Rect(35, 6, 45, 8), self.okText, cmOK, bfDefault)
        self.insert(self.okButton)
        self.chDirButton = Button(Rect(35, 9, 45, 11), self.chDirText, cmChangeDir, bfNormal)
        self.insert(self.chDirButton)

        if options & cdHelpButton:
            self.insert(Button(Rect(35, 15, 45, 17), self.helpText, cmHelp, bfNormal))
        if not options & cdNoLoadDir:
            self.setupDialog()
        self.selectNext(False)

    def consumesData(self) -> bool:
        return True

    def getData(self) -> DataRecord:
        return self.dirInput.getData()

    def setData(self, data: DataRecord) -> None:
        self.dirInput.setData(data.value)

    def handleEvent(self, event: Event):
        super().handleEvent(event)
        if event.what == evCommand:
            emc = event.message.command
            if emc == cmRevert:
                curDir = getCurDir()
            elif emc == cmChangeDir:
                p = self.dirList.getList()[self.dirList.focused]
                curDir = p.dir()
                if curDir[-1] != os.sep:
                    curDir += os.sep
            elif emc == cmDirSelection:
                self.chDirButton.makeDefault(event.message.infoPtr)
                self.clearEvent(event)
                return
            else:
                return
            self.dirList.newDirectory(curDir)
            if curDir and curDir[-1] == os.sep:
                curDir = curDir[:-1]
            self.dirInput.setData(curDir)
            self.dirInput.drawView()
            self.dirList.select()
            self.clearEvent(event)

    def valid(self, command: int) -> bool:
        if command != cmOK:
            return True
        rec = self.dirInput.getData()
        path = rec.value
        if path == self.drivesText:
            path = ''
            rec.value = ''

        if not path:
            event = Event(evCommand)
            event.message.command = cmChangeDir
            self.putEvent(event)
            return False

        path = fexpand(path)
        if path and path[-1] == os.sep:
            path = path[:-1]

        if self.changeDir(path):
            messageBox(self.invalidText, mfError, (mfOKButton,))
            return False
        return True

    def setupDialog(self):
        if self.dirList:
            curDir = getCurDir()
            self.dirList.newDirectory(curDir)
            if self.dirInput:
                if curDir and curDir[-1] == os.sep:
                    curDir = curDir[:-1]
                self.dirInput.setData(curDir)
                self.dirInput.drawView()

    @staticmethod
    def changeDir(path: Union[str, pathlib.Path]) -> bool:
        try:
            os.chdir(path)
            return False
        except Exception:
            return True
