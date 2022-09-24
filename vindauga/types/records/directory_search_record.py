# -*- coding: utf-8 -*-
import datetime
from dataclasses import dataclass
from functools import  total_ordering
import os
import stat

from .search_record import SearchRecord, FA_DIREC, FA_ARCH


@total_ordering
@dataclass
class DirectorySearchRecord(SearchRecord):

    def setStatInfo(self, filename: str, s: os.stat_result):
        self.attr = FA_ARCH
        if stat.S_ISDIR(s.st_mode):
            self.attr |= FA_DIREC

        self.name = filename
        self.size = s.st_size
        self.time = datetime.datetime.fromtimestamp(s.st_mtime)

    # Sort, directories first, then files
    def __lt__(self, other):
        if self.attr & FA_DIREC and not other.attr & FA_DIREC:
            return True
        if self.attr == other.attr:
            return self.name.lower() < other.name.lower()
        return self.attr < other.attr

    def __eq__(self, other):
        return self.attr == other.attr and self.name.lower() == other.name.lower()

    def __gt__(self, other):
        return not self.__lt__(other)
