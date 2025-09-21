# -*- coding: utf-8 -*-
from unittest import TestCase

from vindauga.types.collections.gen_collection import GenCollection


class Test_GenCollection(TestCase):
    """
    Test Collection
    """
    def test_gen_collection(self):
        t = GenCollection()

        t.insert(1, '1')
        t.insert(2, '2')
        t.insert(3, '4')

        assert t == ['1', '2', '4']

    def test_gen_collection_text_length(self):
        t = GenCollection()

        t.insert(1, '1')
        t.insert(2, '22')
        t.insert(3, '4444')

        assert t.getTextLength() == 4

    def test_gen_collection_text_length_empty(self):
        t = GenCollection()

        assert t.getTextLength() == 0
