# -*- coding: utf-8 -*-
from unittest import TestCase

from vindauga.types.draw_buffer import DrawBuffer


class TestDrawBuffer(TestCase):
    """
    Test Draw Buffer
    """

    def test_moveBuf_no_attr(self):
        """
        Test Move Buf
        """
        b = DrawBuffer()
        b.moveBuf(0, 'abcdefghijk', 0, 5)
        data = b[:10].tolist()
        result = [ord(c) for c in 'abcde\0\0\0\0\0']
        assert data == result, ("_data is", data, "vs", result, len(b))

    def test_moveBuf_with_attr(self):
        """
        Test Move Buf
        """
        b = DrawBuffer()
        b.moveBuf(0, 'abcdefghijk', 0xFF, 5)
        data = b[:10].tolist()
        result = [0xFF0000 | ord(c) for c in 'abcde'] + [0x00] * 5
        assert data == result, ("_data is", data, "vs", result, len(b))

    def test_moveChar(self):
        self.fail()

    def test_moveStr(self):
        self.fail()

    def test_moveCStr(self):
        self.fail()

    def test_putAttribute(self):
        self.fail()

    def test_putChar(self):
        self.fail()

    def test_putCharOnly(self):
        self.fail()
