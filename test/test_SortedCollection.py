# -*- coding: utf-8 -*-
from unittest import TestCase

from vindauga.types.collections.sorted_collection import *


class Test_SortedCollection(TestCase):
	"""
	Test Sorted Collection
	"""
	def test_SortedCollection(self):
		t = SortedCollection()

		t.append(1)
		t.insert(2, 2)
		t.insert(3, 1)

		assert t == [1, 1, 2], ("T is", t)

		t.insert(1, 4)

		assert t == [1, 1, 2, 4], ("T is ", t)
