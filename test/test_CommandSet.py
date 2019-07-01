# -*- coding: utf-8 -*-
from unittest import TestCase

from vindauga.types.command_set import CommandSet


class Test_CommandSet(TestCase):
    """
    Test Command Set
    """
    def test_Constructor(self):
        tc = CommandSet()

    def test_isEmpty(self):
        tc = CommandSet()
        assert tc.isEmpty()

    def test_enableCommand(self):
        tc = CommandSet()
        tc.enableCmd(1)

    def test_has(self):
        tc = CommandSet()
        tc.enableCmd(1)
        assert tc.has(1)

    def test_disableCommand(self):
        tc = CommandSet()
        tc.enableCmd(1)
        tc.enableCmd(2)
        tc.disableCmd(1)

        assert tc.has(2)
        assert not tc.has(1)

    def test_eq(self):
        tc1 = CommandSet()
        tc1.enableCmd(1)

        tc2 = CommandSet()
        tc2.enableCmd(1)

        assert tc1 == tc2

    def test_ne(self):
        tc1 = CommandSet()
        tc1.enableCmd(1)

        tc2 = CommandSet()
        tc2.enableCmd(2)

        assert tc1 != tc2

    def test_ConstuctorFromInstance(self):
        tc = CommandSet()
        tc.enableCmd(1)

        tc2 = CommandSet(tc)

        assert tc2 == tc

        tc.enableCmd(2)

        assert tc2 != tc
