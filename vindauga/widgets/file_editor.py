# -*- coding: utf-8 -*-
import logging
import os
from pathlib import Path
from typing import Optional, Union, IO

from vindauga.constants.command_codes import *
from vindauga.constants.edit_command_codes import *
from vindauga.constants.event_codes import *
# BufferArray no longer needed - using strings for buffers now
from vindauga.types.rect import Rect
from vindauga.utilities.message import message
from vindauga.utilities.filesystem.path_utils import fexpand

from .editor import Editor
from .indicator import Indicator
from .scroll_bar import ScrollBar


logger = logging.getLogger(__name__)


class FileEditor(Editor):

    backupExt = '~'

    def __init__(self, bounds: Rect, hScrollBar: ScrollBar, vScrollBar: ScrollBar, indicator: Optional[Indicator],
                 filename: Optional[Union[str, Path]]):
        super().__init__(bounds, hScrollBar, vScrollBar, indicator, 0)

        if not filename:
            self.fileName = ''
        else:
            self.fileName = fexpand(filename)

            if self.isValid:
                self.isValid = self.loadFile()

    def doneBuffer(self):
        self.buffer = None

    def handleEvent(self, event):
        super().handleEvent(event)

        what = event.what

        if what == evCommand:
            c = event.message.command
            if c == cmSave:
                self.save()
            elif c == cmSaveAs:
                self.saveAs()
            else:
                return
            self.clearEvent(event)

    def loadFile(self):
        try:
            f = open(self.fileName, 'rt', encoding='utf-8')
        except OSError:
            logger.exception('Load File')
            self.setBufLen(0)
            return True

        # Read file content as string - matches new Editor string buffer
        content = f.read()
        self.buffer = content
        self.setBufLen(len(self.buffer))
        return True

    def save(self):
        if not self.fileName:
            return self.saveAs()
        return self.saveFile()

    def saveAs(self):
        res = False

        result, data = Editor.editorDialog(edSaveAs, self.fileName)
        if result != cmCancel:
            self.fileName = data
            fexpand(self.fileName)
            message(self.owner, evBroadcast, cmUpdateTitle, None)
            res = self.saveFile()
            if self.isClipboard():
                self.fileName = ''
        return res


    def saveFile(self):
        try:
            if self.editorFlags & efBackupFiles:
                backupName = f'{self.fileName}{self.backupExt}'
                if os.path.exists(backupName):
                    os.unlink(backupName)
                os.rename(self.fileName, backupName)
        except FileNotFoundError:
            pass

        try:
            with open(self.fileName, 'wt', encoding='utf-8') as f:
                # Write content before gap
                before_gap = self.buffer[:self.curPtr]
                f.write(before_gap)

                # Write content after gap
                after_gap_start = self.curPtr + self.gapLen
                after_gap = self.buffer[after_gap_start:after_gap_start + (self.bufLen - self.curPtr)]
                f.write(after_gap)
        except Exception as e:
            logger.exception('saveFile')
            Editor.editorDialog(edCreateError, self.fileName)
            return False

        self.modified = False
        self.update(ufUpdate)
        return True

    def shutdown(self):
        self.setCmdState(cmSave, False)
        self.setCmdState(cmSaveAs, False)
        super().shutdown()

    def updateCommands(self):
        super().updateCommands()
        self.setCmdState(cmSave, True)
        self.setCmdState(cmSaveAs, True)

    def valid(self, command: int) -> bool:
        if command == cmValid:
            return self.isValid

        if self.modified:
            if not self.fileName:
                d = edSaveUntitled
            else:
                d = edSaveModify

            dd = Editor.editorDialog(d, self.fileName)
            if dd == cmYes:
                return self.save()
            elif dd == cmNo:
                self.modified = False
                return True
            elif dd == cmCancel:
                return False
        return True
