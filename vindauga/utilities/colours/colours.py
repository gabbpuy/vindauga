# -*- coding: utf-8 -*-
from enum import IntEnum
import curses
import array
import json
import logging
from pathlib import Path
import platform
from typing import Dict, List, Tuple, Optional

from vindauga.types.display import Display

logger = logging.getLogger(__name__)
PLATFORM_IS_WINDOWS = platform.system().lower() == 'windows'


class Colours(IntEnum):
    Black = 0
    Blue = 1
    Green = 2
    Cyan = 3
    Red = 4
    Magenta = 5
    Yellow = 6
    White = 7
    Grey = 8
    LightBlue = 9
    LightGreen = 10
    LightCyan = 11
    LightRed = 12
    LightMagenta = 13
    LightYellow = 14
    LightWhite = 15


def colour_256to16(c: int) -> int:
    table = (
        0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15,
        0, 4, 4, 4, 12, 12, 2, 6, 4, 4, 12, 12, 2, 2, 6, 4,
        12, 12, 2, 2, 2, 6, 12, 12, 10, 10, 10, 10, 14, 12, 10, 10,
        10, 10, 10, 14, 1, 5, 4, 4, 12, 12, 3, 8, 4, 4, 12, 12,
        2, 2, 6, 4, 12, 12, 2, 2, 2, 6, 12, 12, 10, 10, 10, 10,
        14, 12, 10, 10, 10, 10, 10, 14, 1, 1, 5, 4, 12, 12, 1, 1,
        5, 4, 12, 12, 3, 3, 8, 4, 12, 12, 2, 2, 2, 6, 12, 12,
        10, 10, 10, 10, 14, 12, 10, 10, 10, 10, 10, 14, 1, 1, 1, 5,
        12, 12, 1, 1, 1, 5, 12, 12, 1, 1, 1, 5, 12, 12, 3, 3,
        3, 7, 12, 12, 10, 10, 10, 10, 14, 12, 10, 10, 10, 10, 10, 14,
        9, 9, 9, 9, 13, 12, 9, 9, 9, 9, 13, 12, 9, 9, 9, 9,
        13, 12, 9, 9, 9, 9, 13, 12, 11, 11, 11, 11, 7, 12, 10, 10,
        10, 10, 10, 14, 9, 9, 9, 9, 9, 13, 9, 9, 9, 9, 9, 13,
        9, 9, 9, 9, 9, 13, 9, 9, 9, 9, 9, 13, 9, 9, 9, 9,
        9, 13, 11, 11, 11, 11, 11, 15, 0, 0, 0, 0, 0, 0, 8, 8,
        8, 8, 8, 8, 7, 7, 7, 7, 7, 7, 15, 15, 15, 15, 15, 15
    )
    return table[c & 0xff]


def colourDistSquared(r1, g1, b1, r2, g2, b2) -> float:
    return (r1 - r2) ** 2 + (g1 - g2) ** 2 + (b1 - b2) ** 2


def colourTo6cube(v) -> int:
    if v < 48:
        return 0
    if v < 114:
        return 1
    return (v - 35) // 40


def colourFindRGB(r: int, g: int, b: int) -> int:
    q2c = (0x00, 0x5f, 0x87, 0xaf, 0xd7, 0xff)
    qr = colourTo6cube(r)
    cr = q2c[qr]
    qg = colourTo6cube(g)
    cg = q2c[qg]
    qb = colourTo6cube(b)
    cb = q2c[qb]

    # If we have hit the colour exactly, return early.
    if cr == r and cg == g and cb == b:
        return 16 + (36 * qr) + (6 * qg) + qb

    # Work out the closest grey (average of RGB).
    grey_avg = (r + g + b) / 3
    if grey_avg > 238:
        grey_idx = 23
    else:
        grey_idx = (grey_avg - 3) / 10
    grey = int(8 + (10 * grey_idx))

    # Is grey or 6x6x6 colour closest? */
    d = colourDistSquared(cr, cg, cb, r, g, b)
    if colourDistSquared(grey, grey, grey, r, g, b) < d:
        idx = 232 + int(grey_idx)
    else:
        idx = 16 + (36 * qr) + (6 * qg) + qb
    return idx


def loadColours() -> List[Dict]:
    jsonPalette = Path(__file__).parent.joinpath('256-colors.json')
    with jsonPalette.open('rt', encoding='utf8') as paletteFP:
        palette = json.load(paletteFP)
    return palette


def initPaletteColours():
    if curses.can_change_color():
        # If we can change colours, set the x-term colour palette
        from .xterm_colors import palette
        for colour in sorted(palette, key=lambda c: c['colorId'])[:curses.COLORS]:
            r = int(colour['rgb']['r'] * 1000 / 256)
            g = int(colour['rgb']['g'] * 1000 / 256)
            b = int(colour['rgb']['b'] * 1000 / 256)
            curses.init_color(colour['colorId'], r, g, b)


def setPalette() -> Tuple[Display, array.array, Optional[array.array]]:
    logger.info('CURSES: Colours: %s, Pairs: %s, Color?: %s, Change?: %s', curses.COLORS, curses.COLOR_PAIRS,
                curses.has_colors(),
                curses.can_change_color())

    initPaletteColours()

    if not curses.has_colors():
        attributeMap = array.array('L', [0] * 128)
        attributeMap[0x07] = curses.A_NORMAL
        attributeMap[0x0f] = curses.A_BOLD
        attributeMap[0x70] = curses.A_REVERSE
        return Display.smMono, attributeMap, None

    attributeMap = array.array('L', [0] * 128)

    if not PLATFORM_IS_WINDOWS:

        colorMap = (Colours.Black,
                    Colours.Cyan,
                    Colours.Green,
                    Colours.Red,
                    Colours.Yellow,
                    Colours.Magenta,
                    Colours.Blue,
                    Colours.White,
                    Colours.Grey,
                    Colours.LightCyan,
                    Colours.LightGreen,
                    Colours.LightRed,
                    Colours.LightYellow,
                    Colours.LightMagenta,
                    Colours.LightBlue,
                    Colours.LightWhite
                    )
    else:
        colorMap = (Colours.Black,
                    Colours.Yellow,
                    Colours.Green,
                    Colours.Cyan,
                    Colours.Red,
                    Colours.Magenta,
                    Colours.Blue,
                    Colours.White,
                    Colours.Grey,
                    Colours.LightYellow,
                    Colours.LightGreen,
                    Colours.LightCyan,
                    Colours.LightRed,
                    Colours.LightMagenta,
                    Colours.LightBlue,
                    Colours.LightWhite
                    )

    if True or curses.COLOR_PAIRS < 257:
        i = 0
        for fore in reversed(colorMap[:8]):
            for back in colorMap[:8]:
                if i:
                    curses.init_pair(i, fore, back)
                i += 1
        if curses.COLORS >= 16:
            # Use bright colours instead of bold
            for fore in reversed(colorMap[8:]):
                for back in colorMap[:8]:
                    curses.init_pair(i, fore, back)
                    i += 1

        for i in range(128):
            back = (i >> 4) & 0x07
            bold = i & 0x08
            fore = i & 0x07
            attribute = 0
            if bold and curses.COLORS >= 16:
                pair = (15 - colorMap[fore]) * 8 + colorMap[back]
            elif bold:
                pair = (7 - colorMap[fore]) * 8 + colorMap[back]
                attribute = curses.A_BOLD
            else:
                pair = (7 - colorMap[fore]) * 8 + colorMap[back]
            attributeMap[i] = curses.color_pair(pair) | attribute
        return Display.smCO80, attributeMap, None

    # Below here has issues due to various bugs in various platforms method of setting color pairs and colors
    # Cygwin lies about colour pairs, it says 65536 pairs but really only 256, setting anything > 32768 causes an error
    # and `color_pair` returns only 256 pairs numbers left shifted by 8
    # Windows color pairs need to be shifted by 16 bits sometimes and cannot change colours... but it has 768 colours
    # But only reports 256 pairs

    lowMap = array.array('L', [0] * 256)
    useBold = False
    totalForeground = 256
    totalBackground = 256
    totalPairs = 65536
    try:
        curses.init_pair(65535, 0, 0)
    except:
        useBold = True
        totalForeground = 128
        totalPairs = 32768

    i = 0
    for fore in range(totalForeground):
        for back in range(totalBackground):
            if i:
                curses.init_pair(i, fore, back)
            i += 1

    for i in range(totalPairs):
        back = (i >> 8) & 0xFF
        fore = i & 0xFF
        bold = 0
        if useBold:
            bold = fore & 0x80
            fore >>= 1

        attributeMap[i] = (curses.color_pair(fore * totalBackground + back))
        if bold:
            attributeMap[i] |= curses.A_BOLD

    colorMap = (Colours.Black,
                Colours.Red,
                Colours.Green,
                Colours.Yellow,
                Colours.Blue,
                Colours.Magenta,
                Colours.Cyan,
                Colours.White,
                Colours.Grey,
                Colours.LightRed,
                Colours.LightGreen,
                Colours.LightYellow,
                Colours.LightBlue,
                Colours.LightMagenta,
                Colours.LightCyan,
                Colours.LightWhite)

    for i in range(256):
        back = (i >> 4) & 0x07
        bold = i & 0x08
        fore = i & 0x07
        attribute = 0
        if bold and curses.COLORS >= 16:
            pair = (colorMap[fore + 8] * totalBackground) + colorMap[back]
        elif bold:
            pair = (colorMap[fore] * totalBackground) + colorMap[back]
            attribute = curses.A_BOLD
        else:
            pair = (colorMap[fore] * totalBackground) + colorMap[back]
        lowMap[i] = curses.color_pair(pair) | attribute
    return Display.smCO256, lowMap, attributeMap
