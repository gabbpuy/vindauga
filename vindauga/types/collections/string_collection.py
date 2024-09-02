# -*- coding: utf-8 -*-
from .sorted_collection import SortedCollection


class StringCollection(SortedCollection):
    name = 'StringCollection'

    def _compare(self, key1: str, key2: str) -> int:
        if key1 == key2:
            return 0
        if key1 < key2:
            return -1
        return 1
