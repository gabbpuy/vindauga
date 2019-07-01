# -*- coding: utf-8 -*-
from .collection import Collection


class DirEntry:
    def __init__(self, txt, directory):
        self.displayText = txt
        self.directory = directory

    def dir(self):
        return self.directory

    def text(self):
        return self.displayText


class DirCollection(Collection):
    name = 'DirCollection'
