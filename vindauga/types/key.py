# -*- coding: utf-8 -*-
from __future__ import annotations

import string

from typing import Union

from dataclasses import dataclass

import vindauga.constants.keys as Keys
from vindauga.constants.keys import kbAltShift, kbCtrlShift, kbNoKey


@dataclass(frozen=True)
class KeyCodeLookupEntry:
    normalKeyCode: Union[int, str] = 0
    shiftState: int = 0

    
_ = KeyCodeLookupEntry


ctrlKeyLookup = [
    _(Keys.kbNoKey, 0),
    _('A', Keys.kbCtrlShift),
    _('B', Keys.kbCtrlShift),
    _('C', Keys.kbCtrlShift),
    _('D', Keys.kbCtrlShift),
    _('E', Keys.kbCtrlShift),
    _('F', Keys.kbCtrlShift),
    _('G', Keys.kbCtrlShift),
    _('H', Keys.kbCtrlShift),
    _('J', Keys.kbCtrlShift),
    _('K', Keys.kbCtrlShift),
    _('L', Keys.kbCtrlShift),
    _('M', Keys.kbCtrlShift),
    _('N', Keys.kbCtrlShift),
    _('O', Keys.kbCtrlShift),
    _('P', Keys.kbCtrlShift),
    _('Q', Keys.kbCtrlShift),
    _('R', Keys.kbCtrlShift),
    _('S', Keys.kbCtrlShift),
    _('T', Keys.kbCtrlShift),
    _('U', Keys.kbCtrlShift),
    _('V', Keys.kbCtrlShift),
    _('W', Keys.kbCtrlShift),
    _('X', Keys.kbCtrlShift),
    _('Y', Keys.kbCtrlShift),
    _('Z', Keys.kbCtrlShift),
]

extKeyLookup = [
    _(Keys.kbNoKey, 0),
    _(Keys.kbEsc, Keys.kbAltShift),
    _(' ', kbAltShift),
    _(Keys.kbNoKey, 0),
    _(Keys.kbIns, Keys.kbCtrlShift),
    _(Keys.kbIns, Keys.kbShift),
    _(Keys.kbDel, Keys.kbCtrlShift),
    _(Keys.kbDel, Keys.kbShift),
    _(Keys.kbNoKey, 0),
    _(Keys.kbNoKey, 0),
    _(Keys.kbNoKey, 0),
    _(Keys.kbNoKey, 0),
    _(Keys.kbNoKey, 0),
    _(Keys.kbNoKey, 0),
    _(Keys.kbBackSpace, Keys.kbAltShift),
    _(Keys.kbTab, Keys.kbShift),
    _('Q', Keys.kbAltShift),
    _('W', Keys.kbAltShift),
    _('E', Keys.kbAltShift),
    _('R', Keys.kbAltShift),
    _('T', Keys.kbAltShift),
    _('Y', Keys.kbAltShift),
    _('U', Keys.kbAltShift),
    _('I', Keys.kbAltShift),
    _('O', Keys.kbAltShift),
    _('P', Keys.kbAltShift),
    _(Keys.kbNoKey, 0),
    _(Keys.kbNoKey, 0),
    _(Keys.kbNoKey, 0),
    _(Keys.kbNoKey, 0),
    _('A', Keys.kbAltShift),
    _('S', Keys.kbAltShift),
    _('D', Keys.kbAltShift),
    _('F', Keys.kbAltShift),
    _('G', Keys.kbAltShift),
    _('H', Keys.kbAltShift),
    _('J', Keys.kbAltShift),
    _('K', Keys.kbAltShift),
    _('L', Keys.kbAltShift),
    _(Keys.kbNoKey, 0),
    _(Keys.kbNoKey, 0),
    _(Keys.kbNoKey, 0),
    _(Keys.kbNoKey, 0),
    _('Z', Keys.kbAltShift),
    _('X', Keys.kbAltShift),
    _('C', Keys.kbAltShift),
    _('V', Keys.kbAltShift),
    _('B', Keys.kbAltShift),
    _('N', Keys.kbAltShift),
    _('M', Keys.kbAltShift),
    _(Keys.kbNoKey, 0),
    _(Keys.kbNoKey, 0),
    _('/', Keys.kbAltShift),
    _(Keys.kbNoKey, 0),
    _('*', Keys.kbAltShift),
    _(Keys.kbNoKey, 0),
    _(Keys.kbNoKey, 0),
    _(Keys.kbNoKey, 0),
    _(Keys.kbF1, 0),
    _(Keys.kbF2, 0),
    _(Keys.kbF3, 0),
    _(Keys.kbF4, 0),
    _(Keys.kbF5, 0),
    _(Keys.kbF6, 0),
    _(Keys.kbF7, 0),
    _(Keys.kbF8, 0),
    _(Keys.kbF9, 0),
    _(Keys.kbF10, 0),
    _(Keys.kbNoKey, 0),
    _(Keys.kbNoKey, 0),
    _(Keys.kbHome, 0),
    _(Keys.kbUp, 0),
    _(Keys.kbPgUp, 0),
    _('-', Keys.kbCtrlShift),
    _(Keys.kbLeft, 0),
    _(Keys.kbNoKey, 0),
    _(Keys.kbRight, 0),
    _(Keys.kbNoKey, 0),
    _('+', Keys.kbCtrlShift),
    _(Keys.kbEnd, 0),
    _(Keys.kbDown, 0),
    _(Keys.kbPgDn, 0),
    _(Keys.kbIns, 0),
    _(Keys.kbDel, 0),
    _(Keys.kbF1, Keys.kbShift),
    _(Keys.kbF2, Keys.kbShift),
    _(Keys.kbF3, Keys.kbShift),
    _(Keys.kbF4, Keys.kbShift),
    _(Keys.kbF5, Keys.kbShift),
    _(Keys.kbF6, Keys.kbShift),
    _(Keys.kbF7, Keys.kbShift),
    _(Keys.kbF8, Keys.kbShift),
    _(Keys.kbF9, Keys.kbShift),
    _(Keys.kbF10, Keys.kbShift),
    _(Keys.kbF1, Keys.kbCtrlShift),
    _(Keys.kbF2, Keys.kbCtrlShift),
    _(Keys.kbF3, Keys.kbCtrlShift),
    _(Keys.kbF4, Keys.kbCtrlShift),
    _(Keys.kbF5, Keys.kbCtrlShift),
    _(Keys.kbF6, Keys.kbCtrlShift),
    _(Keys.kbF7, Keys.kbCtrlShift),
    _(Keys.kbF8, Keys.kbCtrlShift),
    _(Keys.kbF9, Keys.kbCtrlShift),
    _(Keys.kbF10, Keys.kbCtrlShift),
    _(Keys.kbCtrlPrtSc, Keys.kbCtrlShift),
    _(Keys.kbLeft, Keys.kbCtrlShift),
    _(Keys.kbRight, Keys.kbCtrlShift),
    _(Keys.kbEnd, Keys.kbCtrlShift),
    _(Keys.kbPgDn, Keys.kbCtrlShift),
    _(Keys.kbHome, Keys.kbCtrlShift),
    _('1', kbAltShift),
    _('2', Keys.kbAltShift),
    _('3', Keys.kbAltShift),
    _('4', Keys.kbAltShift),
    _('5', Keys.kbAltShift),
    _('6', Keys.kbAltShift),
    _('7', Keys.kbAltShift),
    _('8', Keys.kbAltShift),
    _('9', Keys.kbAltShift),
    _('0', Keys.kbAltShift),
    _('-', Keys.kbAltShift),
    _('=', Keys.kbAltShift),
    _(Keys.kbPgUp, Keys.kbCtrlShift),
    _(Keys.kbF11, 0),
    _(Keys.kbF12, 0),
    _(Keys.kbF11, Keys.kbShift),
    _(Keys.kbF12, Keys.kbShift),
    _(Keys.kbF11, Keys.kbCtrlShift),
    _(Keys.kbF12, Keys.kbCtrlShift),
    _(Keys.kbF11, Keys.kbAltShift),
    _(Keys.kbF12, Keys.kbAltShift),
    _(Keys.kbUp, Keys.kbCtrlShift),
    _(Keys.kbNoKey, 0),
    _(Keys.kbNoKey, 0),
    _(Keys.kbNoKey, 0),
    _(Keys.kbDown, Keys.kbCtrlShift),
    _(Keys.kbNoKey, 0),
    _(Keys.kbNoKey, 0),
    _(Keys.kbTab, Keys.kbCtrlShift),
    _(Keys.kbNoKey, 0),
    _(Keys.kbNoKey, 0),
    _(Keys.kbHome, Keys.kbAltShift),
    _(Keys.kbUp, Keys.kbAltShift),
    _(Keys.kbPgUp, Keys.kbAltShift),
    _(Keys.kbNoKey, 0),
    _(Keys.kbLeft, Keys.kbAltShift),
    _(Keys.kbNoKey, 0),
    _(Keys.kbRight, Keys.kbAltShift),
    _(Keys.kbNoKey, 0),
    _(Keys.kbEnd, Keys.kbAltShift),
    _(Keys.kbDown, Keys.kbAltShift),
    _(Keys.kbPgDn, Keys.kbAltShift),
    _(Keys.kbIns, Keys.kbAltShift),
    _(Keys.kbDel, Keys.kbAltShift),
    _(Keys.kbNoKey, 0),
    _(Keys.kbTab, Keys.kbAltShift),
    _(Keys.kbTab, Keys.kbAltShift),
]

kbCtrlBackEntry = _(Keys.kbBackSpace, Keys.kbCtrlShift)
kbCtrlEnterEntry = _(Keys.kbEnter, Keys.kbCtrlShift)


def isRawCtrlKey(scanCode: int, charCode: int) -> bool:
    scanKeys = "QWERTYUIOP\0\0\0\0ASDFGHJKL\0\0\0\0\0ZXCVBNM"
    return 16 <= scanCode < 51 and scanKeys[scanCode - 16] == charCode - 1 + ord('A')


def isPrintableCharacter(charCode: int) -> bool:
    return chr(charCode) in string.printable


def isKeyPadCharacter(scanCode: int) -> bool:
    return scanCode in {0x35, 0x37, 0x4a, 0x4e}

    
class Key:
    def __init__(self, keyCode: int = 0, shiftState: int = 0):
        if isinstance(keyCode, str):
            keyCode = ord(keyCode)
        code = keyCode
        mods = 0
        if shiftState > 0:
            if shiftState & Keys.kbShift:
                mods |= Keys.kbShift
            if shiftState & Keys.kbCtrlShift:
                mods |= Keys.kbCtrlShift
            if shiftState & Keys.kbAltShift:
                mods |= Keys.kbAltShift
        else:
            mods = 0
            
        scanCode = keyCode >> 8
        charCode = keyCode & 0xFF
        
        entry: KeyCodeLookupEntry = None
        
        if keyCode <= Keys.kbCtrlZ or isRawCtrlKey(scanCode, charCode):
            entry = ctrlKeyLookup[charCode]
        elif charCode == 0:
            if scanCode < len(extKeyLookup):
                entry = extKeyLookup[scanCode]
        elif isPrintableCharacter(charCode):
            if ord('a') <= charCode <= ord('z'):
                code = charCode - ord('a') + ord('A')
            elif not isKeyPadCharacter(scanCode):
                code &= 0xFF
        else:
            if keyCode == Keys.kbCtrlBackSpace:
                entry = kbCtrlBackEntry
            elif keyCode == Keys.kbCtrlEnter:
                entry = kbCtrlEnterEntry
        
        if entry:
            mods |= entry.shiftState
            if entry.normalKeyCode != 0:
                code = entry.normalKeyCode
        
        self.code = code
        self.mods = mods if code != Keys.kbNoKey else Keys.kbNoKey

    def __eq__(self, other: Key):
        return self.code | self.mods << 16 == other.code | other.mods << 16

    def __ne__(self, other: Key):
        return not (self == other)

    def __int__(self) -> int:
        return self.code | self.mods << 16
