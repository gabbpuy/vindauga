# -*- coding: utf-8 -*-
from __future__ import annotations
from vindauga.constants.event_codes import maxCharSize

from .char_scan_type import CharScanType


class KeyDownEvent:
    __slots__ = ('charScan', 'controlKeyState', '__keyCode', 'text', 'textLength')

    def __init__(self):
        self.charScan = CharScanType()
        self.controlKeyState = 0
        self.text = bytearray(maxCharSize)
        self.textLength = 0

    def update(self, other:KeyDownEvent):
        self.charScan = other.charScan
        self.controlKeyState = other.controlKeyState
        self.text = other.text
        self.textLength = other.textLength

    @classmethod
    def create(cls, char, modifier, text=None):
        c = cls()
        c.keyCode = char  # This will also set charScan via the setter
        c.controlKeyState = modifier
        if text:
            if isinstance(text, str):
                text = text.encode('utf-8')
            text_len = min(len(text), maxCharSize)
            c.text[:text_len] = text[:text_len]
            c.textLength = text_len
        return c

    @property
    def keyCode(self):
        return int(self.charScan)

    @keyCode.setter
    def keyCode(self, value):
        # Also set charScan
        cs = self.charScan
        if isinstance(value, str):
            value = ord(value)
        cs.charCode = chr(value & 0xFF)
        cs.scanCode = (value >> 8) & 0xFF

    def getText(self) -> str:
        if self.textLength == 0:
            return ""
        return self.text[:self.textLength].decode('utf-8', errors='ignore')

    def __repr__(self):
        return f'<KeyEvent: {self.charScan}::{self.keyCode:x} control:{self.controlKeyState:x}>'
