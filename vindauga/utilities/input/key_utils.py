# -*- coding: utf-8 -*-
from vindauga.constants.keys import (kbCtrlB, kbLeft, kbCtrlF, kbRight, kbCtrlP, kbUp, kbCtrlN, kbDown,
                                     kbCtrlA, kbHome, kbCtrlE, kbEnd, kbCtrlD, kbDel, kbCtrlQ, kbIns,
                                     kbAltV, kbPgUp, kbCtrlV, kbPgDn, kbCtrlH, kbBackSpace)


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