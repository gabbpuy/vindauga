# -*- coding: utf-8 -*-
from unittest import TestCase

from vindauga.types.collections.collection import Collection


class Test_Collection(TestCase):
    """
    Test Collection
    """
    def test_collection(self):
        t = Collection()

        t.insert(1, 1)
        t.insert(2, 2)
        t.insert(3, 4)

        assert t == [1, 2, 4]

        t.insert(2, 3)

        assert t == [1, 2, 3, 4]
