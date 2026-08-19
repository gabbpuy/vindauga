# -*- coding: utf-8 -*-
import logging
import os
import pathlib
import platform
import re
from typing import List

from vindauga.types.collections.dir_collection import DirCollection, DirEntry
from vindauga.constants.std_dialog_commands import cmChangeDir, cmDirSelection, cmDirFocused
from vindauga.constants.event_codes import evCommand, evBroadcast
from vindauga.constants.state_flags import sfFocused
from vindauga.utilities.message import message
from vindauga.types.rect import Rect

from .list_box import ListBox
from .scroll_bar import ScrollBar

PLATFORM_IS_WINDOWS = platform.system().lower() == 'windows'
PLATFORM_IS_CYGWIN = platform.system().lower().startswith('cygwin')

if PLATFORM_IS_WINDOWS:
    import ctypes
    from ctypes import windll

    kernel = windll.kernel32

logger = logging.getLogger(__name__)


class DirListBox(ListBox):
    pathDir = '└─┬'
    firstDir = '└┬─'
    firstAndOnlyDir = '└──'
    middleDir = ' ├─'
    lastDir = ' └─'
    graphics = '└├─'
    drives = 'Drives'

    def __init__(self, bounds: Rect, scrollBar: ScrollBar):
        super().__init__(bounds, 1, scrollBar)
        self.dir: pathlib.Path = pathlib.Path()
        self.drives = []
        self.cur = 0
        self.dirList = DirCollection()
        self.letters = self.__getDriveLetters()

    def getText(self, item: int, maxChars: int) -> str:
        return self.dirList[item].text()[:maxChars]

    def isSelected(self, item: int) -> bool:
        return item is self.cur

    def focusItem(self, item: int):
        super().focusItem(item)
        if self.dirList and 0 <= item < len(self.dirList):
            message(self.owner, evBroadcast, cmDirFocused, self.dirList[item])

    def selectItem(self, item: int):
        message(self.owner, evCommand, cmChangeDir, self.dirList[item])

    @staticmethod
    def __absolute(directory: str) -> pathlib.Path:
        if PLATFORM_IS_CYGWIN:
            directory = re.sub(r'^([A-Za-z]):', r'/cygdrive/\1', directory)
        return pathlib.Path(directory).resolve()

    def newDirectory(self, directory: str):
        self.dir = self.__absolute(directory)
        self.dirList = DirCollection()
        self.showDrives(self.dirList)
        self.showDirs(self.dirList)
        self.newList(self.dirList)
        self.focusItem(self.cur)

    def setState(self, state: int, enable: bool):
        super().setState(state, enable)
        if state & sfFocused:
            message(self.owner, evCommand, cmDirSelection, enable)

    def showDrives(self, collection: DirCollection):
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
    def __getDriveLetters() -> List[str]:
        if not PLATFORM_IS_WINDOWS:
            return []

        size = kernel.GetLogicalDriveStringsW(0, None)
        # `size` is a count of WCHARs, not bytes -- use a unicode buffer so ctypes allocates
        # the correct (size * sizeof(wchar)) byte capacity. A plain create_string_buffer(size)
        # allocates `size` *bytes*, half of what's needed for a UTF-16 string, and the
        # GetLogicalDriveStringsW call below then overflows it -- a native access violation
        # that crashes the whole process with no Python traceback.
        driveList = ctypes.create_unicode_buffer(size)
        buffSize = kernel.GetLogicalDriveStringsW(size, driveList)
        # Slicing a ctypes c_wchar array already returns a decoded str; unlike
        # create_string_buffer's result, a unicode buffer has no .raw attribute to decode by
        # hand, and doesn't need one.
        letters = driveList[:buffSize]
        letters = letters.split('\x00')
        return letters

    def __dirNames(self, subDirs: List[str]) -> List[str]:
        if len(subDirs) == 1:
            return [self.firstAndOnlyDir]
        return [self.firstDir] + (len(subDirs) - 2) * [self.middleDir] + [self.lastDir]
