# -*- coding: utf-8 -*-
# SPECIAL_CHARS = cp437ToUnicode('\x4B\xAE\x1A\x1B\x20\x20')
SPECIAL_CHARS = 'K«→←  '

altCodes1 = "QWERTYUIOP\x00\x00\x00\x00ASDFGHJKL\x00\x00\x00\x00\x00ZXCVBNM"
altCodes2 = "1234567890-="


def getAltChar(keyCode):
    if isinstance(keyCode, str):
        keyCode = ord(keyCode)

    if not (keyCode & 0xFF):
        tmp = keyCode >> 8

        if tmp == 2:
            return '\xF0'  # Alt-Space
        elif 0x10 <= tmp <= 0x33:
            return altCodes1[tmp - 0x10]  # alt-letter
        elif 0x78 <= tmp <= 0x84:
            return altCodes2[tmp - 0x78]  # alt-number
    return 0


def getAltCode(c):
    if not c:
        return 0

    if isinstance(c, int):
        c = chr(c)

    c = c.upper()

    if c == '\xF0':
        return 0x200  # Alt-Space

    if c in altCodes1:
        return (altCodes1.find(c) + 0x10) << 8

    if c in altCodes2:
        return (altCodes2.find(c) + 0x78) << 8

    return 0


def low(w):
    return w & 0xFF


def hi(w):
    return (w >> 8) & 0xFF


def getCtrlChar(keyCode):
    if low(keyCode) and (low(keyCode) <= (ord('Z') - ord('A') + 1)):
        return chr(low(keyCode) + ord('A') - 1)
    return 0


def getCtrlCode(ch):
    return getAltCode(ch) | [ch, ch & ~0x20][ord('a') <= ch <= ord('z')]
