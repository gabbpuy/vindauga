# -*- coding: utf-8 -*-
from dataclasses import dataclass
import datetime
from functools import total_ordering

FA_ARCH = 0x01
FA_DIREC = 0x02
FA_RDONLY = 0x04


@total_ordering
@dataclass
class SearchRecord:
    attr: int = 0
    time: datetime.datetime = 0
    size: int = 0
    name: str = ''

    def __eq__(self, other):
        return self.name == other.name

    def __lt__(self, other):
        return self.name < other.name

    def __gt__(self, other):
        return self.name > other.name
