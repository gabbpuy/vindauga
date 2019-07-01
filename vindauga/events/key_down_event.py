# -*- coding: utf-8 -*-
from .char_scan_event import CharScanEvent


class KeyDownEvent:
    __slots__ = ('charScan', 'controlKeyState', '__keyCode')

    def __init__(self):
        self.charScan = CharScanEvent()
        self.controlKeyState = 0
        self.__keyCode = 0

    @property
    def keyCode(self):
        return self.__keyCode

    @keyCode.setter
    def keyCode(self, value):
        self.__keyCode = value
        # Also set charScan
        cs = self.charScan
        if isinstance(value, str):
            value = ord(value)
        cs.charCode = chr(value & 0xFF)
        cs.scanCode = (value >> 8) & 0xFF

    def __repr__(self):
        return '<KeyEvent: {}::{:x}>'.format(self.charScan, self.keyCode)
