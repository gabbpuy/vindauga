# -*- coding: utf-8 -*-
import logging

from .sorted_collection import SortedCollection

logger = logging.getLogger(__name__)

FA_DIREC = 0x02


class FileCollection(SortedCollection):
    name = 'FileCollection'

    def _compare(self, key1, key2):
        if key1 is key2:
            return 0

        if key1.name.lower() == key2.name.lower():
            return 0

        if key1.name == '..':
            return -1

        if key2.name == '..':
            return 1

        if (key1.attr & FA_DIREC) and (not key2.attr & FA_DIREC):
            return -1

        if (key2.attr & FA_DIREC) and (not key1.attr & FA_DIREC):
            return 1

        if key1.name.lower() == key2.name.lower():
            return 0

        if key1.name.lower() < key2.name.lower():
            return -1
        return 1

    def search(self, key):
        i = 0

        if any((file := i) for i, entry in enumerate(self) if entry == key):
            return file
        return len(self) + 1
