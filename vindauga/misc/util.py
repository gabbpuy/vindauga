# -*- coding: utf-8 -*-
import logging
import os

from vindauga.constants.keys import (kbCtrlB, kbLeft, kbCtrlF, kbRight, kbCtrlP, kbUp, kbCtrlN, kbDown,
                                     kbCtrlA, kbHome, kbCtrlE, kbEnd, kbCtrlD, kbDel, kbCtrlQ, kbIns,
                                     kbAltV, kbPgUp, kbCtrlV, kbPgDn, kbCtrlH, kbBackSpace)

logger = logging.getLogger(__name__)

fexpand = os.path.abspath


def splitPath(path):
    dirname, filename = os.path.split(path)
    if not dirname:
        dirname = '.'
    if dirname[-1] != os.path.sep:
        dirname += os.path.sep

    return dirname, filename


def ctrlToArrow(keyCode):
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


def getCurDir():
    theDir = os.getcwd()
    if not theDir.endswith(os.path.sep):
        theDir += os.path.sep
    return theDir


def isWild(f):
    return any(c in {'?', '*'} for c in reversed(f))


def relativePath(path):
    return not os.path.isabs(path)


def validFileName(fileName):
    if os.path.exists(fileName):
        return os.access(fileName, os.R_OK)
    try:
        with open(fileName, 'w'):
            pass
        os.remove(fileName)
        return True
    except IOError:
        return False


def pathValid(path):
    return os.path.isdir(os.path.dirname(path))


def nameLength(name):
    """
    Remove the '~' from strings and count the letters.
    :param name: String to count
    :return: length of name without '~'
    """
    return len(name) - name.count('~')


def clamp(val, minVal, maxVal):
    """
    Clamp a value between minVal and maxVal

    :param val: Incoming value
    :param minVal: bottom of range
    :param maxVal: top of range
    :return: clamped value
    """
    return max(minVal, min(val, maxVal))
