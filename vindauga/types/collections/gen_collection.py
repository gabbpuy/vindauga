# -*- coding: utf-8 -*-
from .string_collection import StringCollection


class GenCollection(StringCollection):
    name = 'GenCollection'

    def getText(self, index):
        return self[index]

    def getTextLength(self):
        return max(len(s) for s in self)

    getCount = StringCollection.__len__
    indexOfText = StringCollection.indexOf
    firstTextThat = StringCollection.firstThat
