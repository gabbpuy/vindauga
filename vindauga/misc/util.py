# -*- coding: utf-8 -*-
import logging
import os
from typing import Tuple

import wcwidth

from vindauga.constants.keys import (kbCtrlB, kbLeft, kbCtrlF, kbRight, kbCtrlP, kbUp, kbCtrlN, kbDown,
                                     kbCtrlA, kbHome, kbCtrlE, kbEnd, kbCtrlD, kbDel, kbCtrlQ, kbIns,
                                     kbAltV, kbPgUp, kbCtrlV, kbPgDn, kbCtrlH, kbBackSpace)

logger = logging.getLogger(__name__)


def fexpand(path: str) -> str:
    return os.path.normpath(os.path.expanduser(path))


def splitPath(path) -> Tuple[str, str]:
    dirname, filename = os.path.split(path)
    if not dirname:
        dirname = '.'
    if not dirname.endswith(os.path.sep):
        dirname += os.path.sep

    return dirname, filename


def ctrlToArrow(keyCode: int) -> int:
    """
    Map control keys to directions

    :param keyCode: Keycode to check
    :return: Key or None
    """
    ctrlCodes = {kbCtrlB: kbLeft,
                 kbCtrlF: kbRight,
                 kbCtrlP: kbUp,
                 kbCtrlN: kbDown,
                 kbCtrlA: kbHome,
                 kbCtrlE: kbEnd,
                 kbCtrlD: kbDel,
                 kbCtrlQ: kbIns,
                 kbAltV: kbPgUp,
                 kbCtrlV: kbPgDn,
                 kbCtrlH: kbBackSpace
                 }
    return ctrlCodes.get(keyCode, keyCode)


def hotKey(s):
    """
    Return the hotkey from a '~T~ilde' formatted string

    :param s: String
    :return: The escaped character or None
    """
    head, _, tail = s.partition('~')
    if tail:
        return tail[0].upper()
    return None


def getCurDir() -> str:
    theDir = os.path.normpath(os.getcwd())
    if not theDir.endswith(os.path.sep):
        theDir += os.path.sep
    return theDir


def isWild(f: str) -> bool:
    return any(c in {'?', '*'} for c in reversed(f))


def isRelativePath(path) -> bool:
    return not os.path.isabs(path)


def isValidFileName(fileName) -> bool:
    if os.path.exists(fileName):
        return os.access(fileName, os.R_OK)
    try:
        with open(fileName, 'w'):
            pass
        os.remove(fileName)
        return True
    except IOError:
        return False


def isDirectory(path) -> bool:
    return os.path.isdir(os.path.dirname(path))


def nameLength(name: str) -> int:
    """
    Remove the '~' from strings and count the letters.
    :param name: String to count
    :return: length of name without '~'
    """
    return wcwidth.wcswidth(name) - name.count('~')


def clamp(val, minVal, maxVal):
    """
    Clamp a value between minVal and maxVal

    :param val: Incoming value
    :param minVal: bottom of range
    :param maxVal: top of range
    :return: clamped value
    """
    return max(minVal, min(val, maxVal))
