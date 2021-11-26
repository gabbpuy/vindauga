# -*- coding: utf-8 -*-
from typing import Union
from .status_item import StatusItem


class StatusDef:
    """
    A `StatusDef` object represents a status line definition used by a
    `StatusLine` view to display context-sensitive status lines.
    """

    def __init__(self, minHelpContext, maxHelpContext):
        self.min = minHelpContext
        self.max = maxHelpContext
        self.items = None
        self.next = None

    def __add__(self, other: Union['StatusDef', StatusItem]):
        if isinstance(other, StatusDef):
            return self.__addStatusDef(other)
        elif isinstance(other, StatusItem):
            return self.__addStatusItem(other)
        return self

    def __iter__(self):
        if self.items:
            cur = self.items
            while cur:
                yield cur
                cur = cur.next

    def __addStatusDef(self, other: 'StatusDef'):
        cur = self
        while cur.next:
            cur = cur.next
        cur.next = other
        return self

    def __addStatusItem(self, other: StatusItem):
        si = self
        while si.next:
            si = si.next

        if not si.items:
            si.items = other
        else:
            cur = si.items
            while cur.next:
                cur = cur.next
            cur.next = other
        return self
