# -*- coding: utf-8 -*-
from dataclasses import dataclass
from .collection import Collection


@dataclass(frozen=True)
class DirEntry:
    displayText: str
    directory: str

    def dir(self):
        return self.directory

    def text(self):
        return self.displayText

    def __repr__(self):
        return f'<DirEntry: {self.directory}>'


class DirCollection(Collection):
    name = 'DirCollection'
