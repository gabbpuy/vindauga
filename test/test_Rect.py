# -*- coding: utf-8 -*-
from unittest import TestCase

from vindauga.types.point import Point
from vindauga.types.rect import Rect


class Test_Rect(TestCase):
    """
    Test Rect
    """
    def test_constructor(self):
        r = Rect(1, 1, 2, 2)

    def test_eq(self):
        r = Rect(1, 1, 2, 2)
        assert r == Rect(1, 1, 2, 2)

    def test_neq(self):
        r = Rect(1, 1, 2, 2)
        assert r != Rect(2, 2, 3, 3)

    def test_move(self):
        r = Rect(1, 1, 2, 2)
        r.move(1, 1)
        assert r == Rect(2, 2, 3, 3)

    def test_grow(self):
        r = Rect(1, 1, 2, 2)
        r.grow(1, 1)
        assert r == Rect(0, 0, 3, 3)

    def test_intersect(self):
        r = Rect(0, 0, 4, 4)
        r.intersect(Rect(1, 1, 2, 2))

        assert r == Rect(1, 1, 2, 2)

    def test_union(self):
        r = Rect(0, 0, 2, 2)
        r.union(Rect(1, 1, 3, 3))
        assert r == Rect(0, 0, 3, 3)

    def test_contains(self):
        r = Rect(0, 0, 4, 4)
        p = Point(1, 2)
        assert p in r

    def test_isEmpty(self):
        r = Rect(4, 4, 3, 3, )
        assert r.isEmpty()
