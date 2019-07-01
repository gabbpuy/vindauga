# -*- coding: utf-8 -*-
import logging
import os

from vindauga.constants.command_codes import *
from vindauga.constants.edit_command_codes import *
from vindauga.constants.event_codes import *
from vindauga.types.draw_buffer import BufferArray
from vindauga.misc.message import message
from vindauga.misc.util import fexpand
from .editor import Editor

logger = logging.getLogger('vindauga.widgets.file_editor')


class FileEditor(Editor):

    backupExt = '~'

    def __init__(self, bounds, hScrollBar, vScrollBar, indicator, filename):
        super().__init__(bounds, hScrollBar, vScrollBar, indicator, 0)

        if not filename:
            self.fileName = ''
        else:
            self.fileName = filename
            self.filename = fexpand(filename)

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

    def initBuffer(self):
        self.buffer = BufferArray([0] * self.bufSize)

    def loadFile(self):
        try:
            f = open(self.fileName, 'rt', encoding='utf-8')
        except OSError:
            logger.exception('Load File')
            self.setBufLen(0)
            return True

        fBuffer = f.read()
        fSize = len(fBuffer)
        self.setBufSize(fSize)
        self.buffer[-fSize:] = BufferArray(ord(c) for c in fBuffer)
        self.setBufLen(fSize)
        return True

    def save(self):
        if self.fileName:
            return self.saveAs()
        return self.saveFile()

    def saveAs(self):
        res = False

        if self.editorDialog(edSaveAs, self.fileName) != cmCancel:
            fexpand(self.fileName)
            message(self.owner, evBroadcast, cmUpdateTitle, None)
            res = self.saveFile()
            if self.isClipboard():
                self.fileName = ''

        return res

    @staticmethod
    def writeBlock(f, buf, bytes):
        while bytes:
            written = f.write(buf)
            bytes -= written
            buf = buf[written:]

    def saveFile(self):
        if self.editorFlags & efBackupFiles:
            backupName = '{}{}'.format(self.fileName, self.backupExt)
            os.rename(self.fileName, backupName)

        try:
            with open(self.fileName, 'wt') as f:
                self.writeBlock(f, self.buffer, self.curPtr)
                self.writeBlock(f, self.buffer[self.curPtr + self.gapLen:],
                                self.bufLen - self.curPtr)
        except:
            self.editorDialog(edCreateError, self.fileName)
            return False

        self.modified = False
        self.update(ufUpdate)
        return True

    def setBufSize(self, newSize):
        logger.info('setBufSize(%s) [%s]', newSize, self.bufSize)
        if newSize == 0:
            newSize = 0x1000
        else:
            newSize = (newSize + 0xFFF) & 0xFFFFF000

        if newSize != self.bufSize:
            temp = self.buffer
            nn = min(newSize, self.bufSize)
            self.buffer = BufferArray(temp[:nn])
            self.buffer.extend([0] * (newSize - nn))
            n = self.bufLen - self.curPtr + self.delCount
            self.buffer[newSize - n: newSize] = temp[self.bufSize - n: self.bufSize]
            self.bufSize = newSize
            self.gapLen = self.bufSize - self.bufLen
        logger.info('setBufSize(%s) -> %s, %s, %s', newSize, self.bufSize, self.gapLen, len(self.buffer))
        return True

    def shutdown(self):
        self.setCmdState(cmSave, False)
        self.setCmdState(cmSaveAs, False)
        super().shutdown()

    def updateCommands(self):
        super().updateCommands()
        self.setCmdState(cmSave, True)
        self.setCmdState(cmSaveAs, True)

    def valid(self, command):
        if command == cmValid:
            return self.isValid

        if self.modified:
            if not self.fileName:
                d = edSaveUntitled
            else:
                d = edSaveModify

            dd = self.editorDialog(d, self.fileName)
            if dd == cmYes:
                return self.save()
            elif dd == cmNo:
                self.modified = False
                return True
            elif dd == cmCancel:
                return False
        return False
