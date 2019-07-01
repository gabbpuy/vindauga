# -*- coding: utf-8 -*_
from .cluster import Cluster


class RadioButtons(Cluster):

    name = 'RadioButtons'
    button = ' ( ) '

    def draw(self):
        self.drawMultiBox(self.button, ' ○')

    def mark(self, item):
        return item == self._value

    def press(self, item):
        self._value = item

    def movedTo(self, item):
        self._value = item

    def setData(self, rec):
        super().setData(rec)
        self._sel = self._value

    def consumesData(self):
        return True
