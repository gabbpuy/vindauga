# -*- coding: utf-8 -*-
import datetime
from dataclasses import dataclass
from functools import total_ordering
import os
import stat

from .search_record import SearchRecord, FA_DIREC, FA_ARCH


@total_ordering
class DirectorySearchRecord:

    def __init__(self):
        self._statSet = False
        self._attr = FA_ARCH
        self._name = ''
        self._size  = 0
        self._time = 0

    def setStatInfo(self, filename: str, s: os.stat_result):
        self._statSet = True
        if stat.S_ISDIR(s.st_mode):
            self._attr |= FA_DIREC
        self._name = filename
        self._size = s.st_size
        self._time = datetime.datetime.fromtimestamp(s.st_mtime)

    @property
    def attr(self):
        if not self._statSet:
            self._setStat()
        return self._attr

    @property
    def size(self):
        if not self._statSet:
            self._setStat()
        return self._size

    @property
    def time(self):
        if not self._statSet:
            self._setStat()
        return self._time

    @property
    def name(self):
        return os.path.basename(self._name)

    def _setStat(self):
        if self._name:
            _stat = os.stat(self._name)
            self.setStatInfo(self._name, _stat)

    # Sort, directories first, then files
    def __lt__(self, other) -> bool:
        if self.attr & FA_DIREC and not other.attr & FA_DIREC:
            return True
        if self.attr == other.attr:
            return self.name.lower() < other.name.lower()
        return self.attr < other.attr

    def __eq__(self, other) -> bool:
        return self.attr == other.attr and self.name.lower() == other.name.lower()

    def __gt__(self, other) -> bool:
        return not self.__lt__(other)
