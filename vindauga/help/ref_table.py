# -*- coding: utf-8 -*-
from vindauga.types.collections.sorted_collection import SortedCollection

from .reference import Reference


class RefTable(SortedCollection):
    """
    RefTable is a collection of `Reference` objects used as a symbol
    table. If the topic has not been seen, a forward reference is
    inserted and a fix-up list is started.  When the topic is seen all
    forward references are resolved.  If the topic has been seen already
    the value it has is used.
    """
    def _compare(self, key1, key2) -> int:
        if key1 > key2:
            return 1
        if key1 < key2:
            return -1
        return 0

    def getReference(self, topic: str) -> Reference:
        index = self.search(topic)
        if index >= 0:
            ref = self[index]
        else:
            ref = Reference(topic=topic, resolved=False)
            self.append(ref)
        return ref

    @staticmethod
    def keyOf(item: Reference) -> str:
        return item.topic

    def __readItem(self, fp):
        pass

    def __writeItem(self, fp):
        pass
