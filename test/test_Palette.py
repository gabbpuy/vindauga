# -*- coding: utf-8 -*-
from unittest import TestCase

from vindauga.types.palette import Palette


class Test_Palette(TestCase):
    """
    Test Palette
    """
    def test_Constructor(self):
        data = '\x00\x01\x02\x03\x04\x05\x06\x07\x08\x09'
        p = Palette(data)

    def test_ConstructorFromInstance(self):
        data = '\x00\x01\x02\x03\x04\x05\x06\x07\x08\x09'
        p = Palette(data)
        p2 = Palette(p)

        for i in range(1, 11):
            assert p[i] == p2[i]

    def test_index(self):
        data = '\x00\x01\x02\x03\x04\x05\x06\x07\x08\x09'
        p = Palette(data)

        for i in range(1, 11):
            assert p[i] == i - 1
