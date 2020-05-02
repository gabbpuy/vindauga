# -*- coding: utf-8 -*-
import curses
from dataclasses import dataclass

from vindauga.constants.keys import *


@dataclass
class KeyMap:
    keycode: int
    type: int
    modifiers: int
    key: int


def KEY_F(num):
    return curses.KEY_F0 + num


DELAY_AUTOCLICK_FIRST = .400
DELAY_AUTOCLICK_NEXT = .100
DELAY_DOUBLECLICK = .300
DELAY_ESCAPE = .400
DELAY_WAKEUP = .05

MALT = kbLeftAlt | kbRightAlt
MCTRL = kbLeftCtrl | kbRightCtrl
MSHIFT = kbLeftShift | kbRightShift

TALT = 0x01

_ = lambda a, b, c, d: KeyMap(keycode=a, type=b, modifiers=c, key=d)

_keyMappings = (
    _(1, 0, 0, kbCtrlA),
    _(2, 0, 0, kbCtrlB),
    _(3, 0, 0, kbCtrlC),
    _(4, 0, 0, kbCtrlD),
    _(5, 0, 0, kbCtrlE),
    _(6, 0, 0, kbCtrlF),
    _(7, 0, 0, kbCtrlG),
    _(8, 0, 0, kbCtrlH),
    _(8, TALT, 0, kbAltBackSpace),
#    _(9, 0, 0, kbCtrlI),
    _(9, 0, 0, kbTab),
    _(9, 0, MSHIFT, kbShiftTab),
#    _(10, 0, 0, kbCtrlJ),
    _(10, 0, 0, kbEnter),
    _(11, 0, 0, kbCtrlK),
    _(12, 0, 0, kbCtrlL),
#    _(13, 0, 0, kbCtrlM),
    _(13, 0, 0, kbEnter),
    _(14, 0, 0, kbCtrlN),
    _(15, 0, 0, kbCtrlO),
    _(16, 0, 0, kbCtrlP),
    _(17, 0, 0, kbCtrlQ),
    _(18, 0, 0, kbCtrlR),
    _(19, 0, 0, kbCtrlS),
    _(20, 0, 0, kbCtrlT),
    _(21, 0, 0, kbCtrlU),
    _(22, 0, 0, kbCtrlV),
    _(23, 0, 0, kbCtrlW),
    _(24, 0, 0, kbCtrlX),
    _(25, 0, 0, kbCtrlY),
    _(26, 0, 0, kbCtrlZ),
    _(27, 0, 0, kbEsc),
    _(31, 0, 0, kbCtrlBackSpace),
    _(127, 0, 0, kbBackSpace),
    _(127, TALT, 0, kbAltBackSpace),

    # alt-letter codes
    _(' ', TALT, 0, kbAltSpace),
    _('0', TALT, 0, kbAlt0),
    _('1', TALT, 0, kbAlt1),
    _('2', TALT, 0, kbAlt2),
    _('3', TALT, 0, kbAlt3),
    _('4', TALT, 0, kbAlt4),
    _('5', TALT, 0, kbAlt5),
    _('6', TALT, 0, kbAlt6),
    _('7', TALT, 0, kbAlt7),
    _('8', TALT, 0, kbAlt8),
    _('9', TALT, 0, kbAlt9),
    _('A', TALT, 0, kbAltA),
    _('B', TALT, 0, kbAltB),
    _('C', TALT, 0, kbAltC),
    _('D', TALT, 0, kbAltD),
    _('E', TALT, 0, kbAltE),
    _('F', TALT, 0, kbAltF),
    _('G', TALT, 0, kbAltG),
    _('H', TALT, 0, kbAltH),
    _('I', TALT, 0, kbAltI),
    _('J', TALT, 0, kbAltJ),
    _('K', TALT, 0, kbAltK),
    _('L', TALT, 0, kbAltL),
    _('M', TALT, 0, kbAltM),
    _('N', TALT, 0, kbAltN),
    _('O', TALT, 0, kbAltO),
    _('P', TALT, 0, kbAltP),
    _('Q', TALT, 0, kbAltQ),
    _('R', TALT, 0, kbAltR),
    _('S', TALT, 0, kbAltS),
    _('T', TALT, 0, kbAltT),
    _('U', TALT, 0, kbAltU),
    _('V', TALT, 0, kbAltV),
    _('W', TALT, 0, kbAltW),
    _('X', TALT, 0, kbAltX),
    _('Y', TALT, 0, kbAltY),
    _('Z', TALT, 0, kbAltZ),


    # escape codes
    _(curses.KEY_DOWN, 0, 0, kbDown),
    _(curses.KEY_UP, 0, 0, kbUp),
    _(curses.KEY_LEFT, 0, 0, kbLeft),
    _(curses.KEY_RIGHT, 0, 0, kbRight),
    _(curses.KEY_HOME, 0, 0, kbHome),
    _(curses.KEY_BACKSPACE, 0, 0, kbBackSpace),
    _(curses.KEY_DC, 0, MCTRL, kbCtrlDel),
    _(curses.KEY_IC, 0, MCTRL, kbCtrlIns),
    _(curses.KEY_NPAGE, 0, MCTRL, kbCtrlPgDn),
    _(curses.KEY_PPAGE, 0, MCTRL, kbCtrlPgUp),
    _(curses.KEY_END, 0, MCTRL, kbCtrlEnd),
    _(curses.KEY_DC, 0, MSHIFT, kbShiftDel),
    _(curses.KEY_IC, 0, MSHIFT, kbShiftIns),
    _(curses.KEY_DC, 0, 0, kbDel),
    _(curses.KEY_IC, 0, 0, kbIns),
    _(curses.KEY_NPAGE, 0, 0, kbPgDn),
    _(curses.KEY_PPAGE, 0, 0, kbPgUp),
    _(curses.KEY_END, 0, 0, kbEnd),
    _(curses.KEY_LEFT, 0, MCTRL, kbCtrlLeft),
    _(curses.KEY_RIGHT, 0, MCTRL, kbCtrlRight),
    _(curses.KEY_HOME, 0, MCTRL, kbCtrlHome),
    _(curses.KEY_LL, 0, 0, kbCtrlPgDn),
    _(curses.KEY_BEG, 0, 0, kbCtrlPgUp),
    _(curses.KEY_COPY, 0, 0, kbCtrlIns),
    _(curses.KEY_SBEG, 0, 0, kbShiftIns),

    _(KEY_F(1), 0, 0, kbF1),
    _(KEY_F(2), 0, 0, kbF2),
    _(KEY_F(3), 0, 0, kbF3),
    _(KEY_F(4), 0, 0, kbF4),
    _(KEY_F(5), 0, 0, kbF5),
    _(KEY_F(6), 0, 0, kbF6),
    _(KEY_F(7), 0, 0, kbF7),
    _(KEY_F(8), 0, 0, kbF8),
    _(KEY_F(9), 0, 0, kbF9),
    _(KEY_F(10), 0, 0, kbF10),
    _(KEY_F(11), 0, 0, kbF11),
    _(KEY_F(12), 0, 0, kbF12),

    _(KEY_F(1), 0, MCTRL, kbCtrlF1),
    _(KEY_F(2), 0, MCTRL, kbCtrlF2),
    _(KEY_F(3), 0, MCTRL, kbCtrlF3),
    _(KEY_F(4), 0, MCTRL, kbCtrlF4),
    _(KEY_F(5), 0, MCTRL, kbCtrlF5),
    _(KEY_F(6), 0, MCTRL, kbCtrlF6),
    _(KEY_F(7), 0, MCTRL, kbCtrlF7),
    _(KEY_F(8), 0, MCTRL, kbCtrlF8),
    _(KEY_F(9), 0, MCTRL, kbCtrlF9),
    _(KEY_F(10), 0, MCTRL, kbCtrlF10),
    _(KEY_F(11), 0, MCTRL, kbCtrlF11),
    _(KEY_F(12), 0, MCTRL, kbCtrlF12),

    _(KEY_F(1), 0, MALT, kbAltF1),
    _(KEY_F(2), 0, MALT, kbAltF2),
    _(KEY_F(3), 0, MALT, kbAltF3),
    _(KEY_F(4), 0, MALT, kbAltF4),
    _(KEY_F(5), 0, MALT, kbAltF5),
    _(KEY_F(6), 0, MALT, kbAltF6),
    _(KEY_F(7), 0, MALT, kbAltF7),
    _(KEY_F(8), 0, MALT, kbAltF8),
    _(KEY_F(9), 0, MALT, kbAltF9),
    _(KEY_F(10), 0, MALT, kbAltF10),
    _(KEY_F(11), 0, MALT, kbAltF11),
    _(KEY_F(12), 0, MALT, kbAltF12),

    _(KEY_F(13), 0, MSHIFT, kbShiftF1),
    _(KEY_F(14), 0, MSHIFT, kbShiftF2),
    _(KEY_F(15), 0, MSHIFT, kbShiftF3),
    _(KEY_F(16), 0, MSHIFT, kbShiftF4),
    _(KEY_F(17), 0, MSHIFT, kbShiftF5),
    _(KEY_F(18), 0, MSHIFT, kbShiftF6),
    _(KEY_F(19), 0, MSHIFT, kbShiftF7),
    _(KEY_F(20), 0, MSHIFT, kbShiftF8),
    _(KEY_F(21), 0, MSHIFT, kbShiftF9),
    _(KEY_F(22), 0, MSHIFT, kbShiftF10),
    _(KEY_F(23), 0, MSHIFT, kbShiftF11),
    _(KEY_F(24), 0, MSHIFT, kbShiftF12),

    # Shift'ed codes in xterm
    _(KEY_F(13), 0, 0, kbShiftF1),
    _(KEY_F(14), 0, 0, kbShiftF2),
    _(KEY_F(15), 0, 0, kbShiftF3),
    _(KEY_F(16), 0, 0, kbShiftF4),
    _(KEY_F(17), 0, 0, kbShiftF5),
    _(KEY_F(18), 0, 0, kbShiftF6),
    _(KEY_F(19), 0, 0, kbShiftF7),
    _(KEY_F(20), 0, 0, kbShiftF8),
    _(KEY_F(21), 0, 0, kbShiftF9),
    _(KEY_F(22), 0, 0, kbShiftF10),
    _(KEY_F(23), 0, 0, kbShiftF11),
    _(KEY_F(24), 0, 0, kbShiftF12),

    # Ctrl'ed codes in xterm
    _(KEY_F(25), 0, 0, kbCtrlF1),
    _(KEY_F(26), 0, 0, kbCtrlF2),
    _(KEY_F(27), 0, 0, kbCtrlF3),
    _(KEY_F(28), 0, 0, kbCtrlF4),
    _(KEY_F(29), 0, 0, kbCtrlF5),
    _(KEY_F(30), 0, 0, kbCtrlF6),
    _(KEY_F(31), 0, 0, kbCtrlF7),
    _(KEY_F(32), 0, 0, kbCtrlF8),
    _(KEY_F(33), 0, 0, kbCtrlF9),
    _(KEY_F(34), 0, 0, kbCtrlF10),
    _(KEY_F(35), 0, 0, kbCtrlF11),
    _(KEY_F(36), 0, 0, kbCtrlF12),

    # Alt'ed (Meta'ed) codes in xterm
    _(KEY_F(37), 0, 0, kbAltF1),
    _(KEY_F(38), 0, 0, kbAltF2),
    _(KEY_F(39), 0, 0, kbAltF3),
    _(KEY_F(40), 0, 0, kbAltF4),
    _(KEY_F(41), 0, 0, kbAltF5),
    _(KEY_F(42), 0, 0, kbAltF6),
    _(KEY_F(43), 0, 0, kbAltF7),
    _(KEY_F(44), 0, 0, kbAltF8),
    _(KEY_F(45), 0, 0, kbAltF9),
    _(KEY_F(46), 0, 0, kbAltF10),
    _(KEY_F(47), 0, 0, kbAltF11),
    _(KEY_F(48), 0, 0, kbAltF12),
)

keyMappings = {(k.keycode, k.type, k.modifiers): k for k in _keyMappings}
showMarkers = False
