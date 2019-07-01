# -*- coding: utf-8 -*-
import logging
import os
import pathlib
import platform

from vindauga.types.collections.dir_collection import DirCollection, DirEntry
from vindauga.constants.std_dialog_commands import cmChangeDir, cmDirSelection
from vindauga.constants.event_codes import evCommand
from vindauga.constants.state_flags import sfFocused
from vindauga.misc.message import message
from .list_box import ListBox

PLATFORM_IS_WINDOWS = platform.system().lower() == 'windows'
if PLATFORM_IS_WINDOWS:
    import ctypes
    from ctypes import windll
    kernel = windll.kernel32

logger = logging.getLogger('vindauga.widgets.dir_list_box')


class DirListBox(ListBox):
    pathDir = '└─┬'
    firstDir = '└┬─'
    firstAndOnlyDir = '└──'
    middleDir = ' ├─'
    lastDir = ' └─'
    graphics = '└├─'
    drives = 'Drives'

    def __init__(self, bounds, scrollBar):
        super().__init__(bounds, 1, scrollBar)
        self.dir = ''
        self.drives = []
        self.cur = 0
        self.dirList = DirCollection()
        self.letters = self.__getDriveLetters()

    def getText(self, item, maxChars):
        return self.dirList[item].text()[:maxChars]

    def isSelected(self, item):
        return item is self.cur

    def selectItem(self, item):
        message(self.owner, evCommand, cmChangeDir, self.dirList[item])

    def newDirectory(self, directory):
        self.dir = os.path.normpath(directory)
        self.dirList = DirCollection()
        self.showDrives(self.dirList)
        self.showDirs(self.dirList)
        self.newList(self.dirList)
        self.focusItem(self.cur)

    def setState(self, state, enable):
        super().setState(state, enable)
        if state & sfFocused:
            message(self.owner, evCommand, cmDirSelection, enable)

    def showDrives(self, collection):
        logger.info('showDrives: %s', self.dir)
        if not PLATFORM_IS_WINDOWS:
            return
        # Letters is a null delimited string...
        for letter in self.letters:
            collection.append(DirEntry(letter[:2], letter))

    def __getDriveLetters(self):
        if not PLATFORM_IS_WINDOWS:
            return

        size = kernel.GetLogicalDriveStringsW(0, None)
        driveList = ctypes.create_string_buffer(size)
        buffSize = kernel.GetLogicalDriveStringsW(size, driveList)
        # Ignore terminator
        letters = driveList.raw[:buffSize].decode('utf-16-le')
        letters = letters.split('\x00')
        return letters

    def showDirs(self, collection: DirCollection):
        logger.info('showDirs(): %s', self.dir)
        try:
            _root, items, _files = next(os.walk(self.dir))
        except StopIteration:
            items = []
        # Ascending tree
        n = 0
        bits = pathlib.PurePath(self.dir).parts
        bits = self.dir.split(os.sep)
        for i in range(len(bits)):
            pathDir = self.pathDir
            if i == len(bits) - 1 and not items:
                pathDir = self.firstAndOnlyDir
            if i and bits[i]:
                collection.append(DirEntry(('  ' * n) + pathDir + bits[i], bits[0] or '/' + os.path.join(*bits[:i + 1])))
                n += 1
            elif not i:
                if PLATFORM_IS_WINDOWS:
                    collection.append(DirEntry(bits[0], bits[0]))
                else:
                    collection.append(DirEntry('/', '/'))
        self.cur = len(collection) - 1

        items = sorted(items)
        for item in items:
            path = os.path.join(self.dir, item)
            if os.path.isdir(path):
                if item == items[0] and item != items[-1]:
                    name = self.firstDir
                elif item == items[0]:
                    name = self.firstAndOnlyDir
                elif item == items[-1]:
                    name = self.lastDir
                else:
                    name = self.middleDir
                name = ('  ' * n) + name + item
                if name:
                    collection.append(DirEntry(name, path))
