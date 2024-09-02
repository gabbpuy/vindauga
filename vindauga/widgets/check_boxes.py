# -*- coding: utf-8 -*-
from .cluster import Cluster


class CheckBoxes(Cluster):

    button = ' [ ] '

    name = 'CheckBoxes'

    def consumesData(self):
        return True

    def draw(self):
        self.drawMultiBox(self.button, " X")

    def mark(self, item: int):
        return (self._value & (1 << item)) != 0

    def press(self, item: int):
        self._value ^= (1 << item)
