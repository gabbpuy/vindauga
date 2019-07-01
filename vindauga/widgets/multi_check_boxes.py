# -*- coding: utf-8 -*-
from vindauga.types.records.data_record import DataRecord

from .cluster import Cluster


# Constant    Value  Meaning
#
# cfOneBit    0x0101 1 bit per checkbox
# cfTwoBits   0x0203 2 bits per check box
# cfFourBits  0x040f 4 bits per check box
# cfEightBits 0x08ff 8 bits per check box

cfOneBit = 0x0101
cfTwoBits = 0x0203
cfFourBits = 0x040F
cfEightBits = 0x08FF


class MultiCheckBoxes(Cluster):
    name = "MultiCheckBoxes"

    def __init__(self, bounds, strings, aSelRange, aFlags, aStates):
        super().__init__(bounds, strings)

        self.__selRange = aSelRange

        # Multi state check boxes use the cfXXXX constants to specify how many
        # bits in the value field represent the state of each check box.
        #
        # The high-order word of the constant indicates the number of bits used
        # for each check box, and the low-order word holds a bit mask used to
        # read those bits.
        #
        # For example, cfTwoBits indicates that value uses two bits for each
        # check box (making a maximum of 16 check boxes in the cluster), and
        # masks each check box's values with the mask 0x03.
        self.__flags = aFlags
        self.__states = aStates

    def draw(self):
        self.drawMultiBox(" [ ] ", self.__states)

    def consumesData(self):
        return True

    def multiMark(self, item):
        return ((self._value & ((self.__flags & 0xFF) << (item * (self.__flags >> 8)))) >>
                (item * (self.__flags >> 8)))

    def getData(self):
        rec = DataRecord()
        p = self._value
        self.drawView()
        rec.value = p
        return rec

    def press(self, item):
        flo = self.__flags & 0xFF
        fhi = self.__flags >> 8

        curState = (self._value & (flo << (item * fhi))) >> (item * fhi)
        curState -= 1

        if curState >= self.__selRange or curState < 0:
            curState = self.__selRange - 1

        self._value = ((self._value & ~(flo << (item * fhi))) | (curState << (item * fhi)))

    def setData(self, p):
        self._value = p
        self.drawView()
