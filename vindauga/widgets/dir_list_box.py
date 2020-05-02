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
        self.dir: pathlib.Path = pathlib.Path()
        self.drives = []
        self.cur = 0
        self.dirList = DirCollection()
        self.letters = self.__getDriveLetters()

    def getText(self, item, maxChars):
        return self.dirList[item].text()[:maxChars]

    def isSelected(self, item):
        return item is self.cur

    def selectItem(self, item):
        logger.info('selectItem: %s, %s', item, len(self.dirList))
        message(self.owner, evCommand, cmChangeDir, self.dirList[item])

    def newDirectory(self, directory):
        self.dir = pathlib.Path(directory).absolute()
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

    def showDirs(self, collection: DirCollection):
        # todo: Put the `Path` into the DirEntry instead of the string.
        logger.info('showDirs(): %s', self.dir)
        try:
            _root, subDirs, _files = next(os.walk(self.dir))
        except StopIteration:
            subDirs = []
        n = 0

        parents = list(reversed(self.dir.parents))

        if parents:
            path = parents[0]
            collection.append(DirEntry(str(path), str(path)))
            for n, path in enumerate(parents[1:], 1):
                collection.append(DirEntry(('  ' * (n - 1)) + self.pathDir + path.name, str(path)))

        icon = self.pathDir if subDirs else self.firstAndOnlyDir
        path = self.dir
        collection.append(DirEntry(('  ' * n) + icon + path.name, str(path)))
        n += 1

        self.cur = len(collection) - 1

        if not subDirs:
            return

        subDirs = sorted(subDirs)
        named_dirs = zip(self.__dirNames(subDirs), subDirs)
        for name, subDir in named_dirs:
            path: pathlib.Path = self.dir.joinpath(subDir)
            name = ('  ' * n) + name + subDir
            collection.append(DirEntry(name, str(path)))

    @staticmethod
    def __getDriveLetters():
        if not PLATFORM_IS_WINDOWS:
            return

        size = kernel.GetLogicalDriveStringsW(0, None)
        driveList = ctypes.create_string_buffer(size)
        buffSize = kernel.GetLogicalDriveStringsW(size, driveList)
        # Ignore terminator
        letters = driveList.raw[:buffSize].decode('utf-16-le')
        letters = letters.split('\x00')
        return letters

    def __dirNames(self, subDirs):
        if len(subDirs) == 1:
            return [self.firstAndOnlyDir]
        return [self.firstDir] + (len(subDirs) - 2) * [self.middleDir] + [self.lastDir]
