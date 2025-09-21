# -*- coding: utf-8 -*-
from unittest import TestCase
from vindauga.types.point import Point


class Test_Point(TestCase):
    """
    Test Point
    """
    def test_constructor(self):
        x = Point()
        y = Point(1, 1)

    def test_Eq(self):
        x = Point(1, 1)
        y = Point(1, 1)
        assert x == y

    def test_Eq_tuple(self):
        x = Point(1, 1)
        assert x == (1, 1)

    def test_Neq(self):
        x = Point(1, 2)
        y = Point(2, 2)
        assert x != y

    def test_Neq_tuple(self):
        x = Point(1, 2)
        assert x != (2, 2)

    def test_add(self):
        x = Point(1, 1)
        y = Point(2, 2)
        z = x + y
        assert z == Point(3, 3)

    def test_sub(self):
        x = Point(1, 1)
        y = Point(2, 2)
        z = y - x
        assert z == x

    def test_iadd(self):
        x = Point(1, 1)
        x += Point(2, 2)
        assert x == Point(3, 3)

    def test_isub(self):
        x = Point(2, 2)
        x -= Point(1, 1)
        assert x == Point(1, 1)
