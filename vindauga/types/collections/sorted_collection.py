# -*- coding: utf -*-
from functools import cmp_to_key

from .collection import Collection


class SortedCollection(Collection):
    """
    The abstract class `SortedCollection` is a specialized derivative of both
    `Collection`. It implements collections sorted by a key (with or without duplicates).
       
    No instances of `SortedCollection` are allowed. It exists solely as a base
    for other standard or user-defined derived classes.
    """

    name = 'SortedCollection'

    def __init__(self, iterable=()):
        super().__init__(iterable)
        self.sort()

    def __setitem__(self, index, value):
        super().__setitem__(index, value)
        self.sort()

    def insert(self, index, value):
        super().append(value)
        self.sort()

    def append(self, value):
        super().append(value)
        self.sort()

    def sort(self, reverse=False):
        super().sort(key=cmp_to_key(self._compare), reverse=reverse)

    def _compare(self, key1, key2):
        """
        `_compare()` is a function that must be overridden in all
        derived classes.
        :param key1: Key to compare
        :param key2: Key to compare
        :return: -1, 0, 1
        """
        raise NotImplementedError
