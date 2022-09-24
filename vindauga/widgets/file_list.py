# -*- coding: utf-8 -*-
import fnmatch
import logging
import os

from vindauga.types.collections.file_collection import FileCollection
from vindauga.constants.event_codes import evBroadcast
from vindauga.constants.keys import kbShift
from vindauga.constants.std_dialog_commands import cmFileFocused, cmFileDoubleClicked
from vindauga.misc.message import message
from vindauga.misc.util import isWild, fexpand, splitPath
from vindauga.types.records.directory_search_record import DirectorySearchRecord
from vindauga.types.records.search_record import FA_DIREC, SearchRecord
from vindauga.widgets.sorted_list_box import SortedListBox

logger = logging.getLogger(__name__)


class FileList(SortedListBox):
    tooManyFiles = _('Too many files.')

    def __init__(self, bounds, scrollBar):
        super().__init__(bounds, 2, scrollBar)

    def focusItem(self, item: int):
        super().focusItem(item)
        message(self.owner, evBroadcast, cmFileFocused, self.getList()[item])

    def selectItem(self, item: int):
        message(self.owner, evBroadcast, cmFileDoubleClicked, self.getList()[item])

    def consumesData(self):
        return False

    def _getKey(self, s: str):
        record = SearchRecord()

        if self._shiftState & kbShift or (s and s[0] == '.'):
            record.attr = FA_DIREC
        else:
            record.attr = 0
        record.name = s.upper()
        return record

    def getText(self, item: int, maxChars: int) -> str:
        f = self.getList()[item]
        dest = f.name
        if f.attr & FA_DIREC:
            dest += os.path.sep
        return dest

    def readDirectory(self, path, wildcard=None):
        if wildcard:
            path = os.path.join(path, wildcard)
            return self.readDirectory(path)

        if not path:
            raise RuntimeError

        if not isWild(path):
            path = os.path.join(path, '*')

        path = fexpand(path)
        directory, wildcard = splitPath(path)
        fileList = FileCollection()

        if directory:
            record = DirectorySearchRecord()
            nPath = os.path.abspath(os.path.join(directory, '..'))
            s = os.stat(nPath)
            if s:
                record.setStatInfo('..', s)
            else:
                record.name = '..'
                record.size = 0
                record.time = 0x210000
                record.attr = FA_DIREC
            fileList.append(record)

        root, directories, files = next(os.walk(directory), (directory, [], []))
        for localDir in directories:
            record = DirectorySearchRecord()
            s = os.stat(os.path.join(root, localDir))
            record.setStatInfo(localDir, s)
            fileList.append(record)

        for f in fnmatch.filter(files, wildcard):
            record = DirectorySearchRecord()
            s = os.stat(os.path.join(root, f))
            record.setStatInfo(f, s)
            fileList.append(record)

        self.newList(fileList)
        self.focusItemNum(0)
        if len(fileList):
            message(self.owner, evBroadcast, cmFileFocused, self.getList()[0])
        else:
            noFile = DirectorySearchRecord()
            message(self.owner, evBroadcast, cmFileFocused, noFile)
