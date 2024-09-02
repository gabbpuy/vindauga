# -*- coding: utf-8 -*_
from vindauga.types.records.data_record import DataRecord

from .cluster import Cluster


class RadioButtons(Cluster):

    name = 'RadioButtons'
    button = ' ( ) '

    def draw(self):
        self.drawMultiBox(self.button, ' ○')

    def mark(self, item: int) -> bool:
        return item == self._value

    def press(self, item: int):
        self._value = item

    def movedTo(self, item: int):
        self._value = item

    def setData(self, rec: DataRecord):
        super().setData(rec)
        self._sel = self._value

    def consumesData(self) -> bool:
        return True
