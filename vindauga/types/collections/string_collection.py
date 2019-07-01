# -*- coding: utf-8 -*-
from .sorted_collection import SortedCollection


class StringCollection(SortedCollection):

    def _compare(self, key1, key2):
        if key1 == key2:
            return 0
        if key1 < key2:
            return -1
        return 1
