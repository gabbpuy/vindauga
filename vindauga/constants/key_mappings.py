# -*- coding: utf-8 -*-
import curses
from dataclasses import dataclass

import vindauga.constants.keys as keys


@dataclass(frozen=True)
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
DELAY_WAKEUP = .03

MALT = keys.kbLeftAlt | keys.kbRightAlt
MCTRL = keys.kbLeftCtrl | keys.kbRightCtrl
MSHIFT = keys.kbLeftShift | keys.kbRightShift

TALT = 0x01

_ = lambda keycode, type, modifiers, key: KeyMap(keycode=keycode, type=type, modifiers=modifiers, key=key)

_keyMappings = (
    _(1, 0, 0, keys.kbCtrlA),
    _(2, 0, 0, keys.kbCtrlB),
    _(3, 0, 0, keys.kbCtrlC),
    _(4, 0, 0, keys.kbCtrlD),
    _(5, 0, 0, keys.kbCtrlE),
    _(6, 0, 0, keys.kbCtrlF),
    _(7, 0, 0, keys.kbCtrlG),
    _(8, 0, 0, keys.kbCtrlH),
    _(8, TALT, 0, keys.kbAltBackSpace),
    #  _(9, 0, 0, kbCtrlI),
    _(9, 0, 0, keys.kbTab),
    # _(9, 0, MSHIFT, kbShiftTab),
    _(curses.KEY_BTAB, 0, 0, keys.kbShiftTab),
    _(9, 0, MCTRL, keys.kbCtrlTab),
    _(10, 0, MCTRL, keys.kbCtrlEnter),
    _(10, 0, 0, keys.kbEnter),
    _(11, 0, 0, keys.kbCtrlK),
    _(12, 0, 0, keys.kbCtrlL),
    _(13, 0, 0, keys.kbEnter),
    _(14, 0, 0, keys.kbCtrlN),
    _(15, 0, 0, keys.kbCtrlO),
    _(16, 0, 0, keys.kbCtrlP),
    _(17, 0, 0, keys.kbCtrlQ),
    _(18, 0, 0, keys.kbCtrlR),
    _(19, 0, 0, keys.kbCtrlS),
    _(20, 0, 0, keys.kbCtrlT),
    _(21, 0, 0, keys.kbCtrlU),
    _(22, 0, 0, keys.kbCtrlV),
    _(23, 0, 0, keys.kbCtrlW),
    _(24, 0, 0, keys.kbCtrlX),
    _(25, 0, 0, keys.kbCtrlY),
    _(26, 0, 0, keys.kbCtrlZ),
    _(27, 0, 0, keys.kbEsc),
    _(31, 0, 0, keys.kbCtrlBackSpace),
    _(63, 0, MCTRL, keys.kbDel),  # ^?
    _(127, 0, 0, keys.kbBackSpace),
    _(127, TALT, 0, keys.kbAltBackSpace),

    # Explicit control codes ^A - ^Z
    _(65, 0, MCTRL, keys.kbCtrlA),
    _(66, 0, MCTRL, keys.kbCtrlB),
    _(67, 0, MCTRL, keys.kbCtrlC),
    _(68, 0, MCTRL, keys.kbCtrlD),
    _(69, 0, MCTRL, keys.kbCtrlE),
    _(70, 0, MCTRL, keys.kbCtrlF),
    _(71, 0, MCTRL, keys.kbCtrlG),
    _(72, 0, MCTRL, keys.kbCtrlH),
    _(73, 0, MCTRL, keys.kbTab),
    _(74, 0, MCTRL, keys.kbEnter),
    _(75, 0, MCTRL, keys.kbCtrlK),
    _(76, 0, MCTRL, keys.kbCtrlL),
    _(77, 0, MCTRL, keys.kbEnter),
    _(78, 0, MCTRL, keys.kbCtrlN),
    _(79, 0, MCTRL, keys.kbCtrlO),
    _(80, 0, MCTRL, keys.kbCtrlP),
    _(81, 0, MCTRL, keys.kbCtrlQ),
    _(82, 0, MCTRL, keys.kbCtrlR),
    _(83, 0, MCTRL, keys.kbCtrlS),
    _(84, 0, MCTRL, keys.kbCtrlT),
    _(85, 0, MCTRL, keys.kbCtrlU),
    _(86, 0, MCTRL, keys.kbCtrlV),
    _(87, 0, MCTRL, keys.kbCtrlW),
    _(88, 0, MCTRL, keys.kbCtrlX),
    _(89, 0, MCTRL, keys.kbCtrlY),
    _(90, 0, MCTRL, keys.kbCtrlZ),

    # alt-letter codes
    _(' ', TALT, 0, keys.kbAltSpace),
    _('0', TALT, 0, keys.kbAlt0),
    _('1', TALT, 0, keys.kbAlt1),
    _('2', TALT, 0, keys.kbAlt2),
    _('3', TALT, 0, keys.kbAlt3),
    _('4', TALT, 0, keys.kbAlt4),
    _('5', TALT, 0, keys.kbAlt5),
    _('6', TALT, 0, keys.kbAlt6),
    _('7', TALT, 0, keys.kbAlt7),
    _('8', TALT, 0, keys.kbAlt8),
    _('9', TALT, 0, keys.kbAlt9),
    _('A', TALT, 0, keys.kbAltA),
    _('B', TALT, 0, keys.kbAltB),
    _('C', TALT, 0, keys.kbAltC),
    _('D', TALT, 0, keys.kbAltD),
    _('E', TALT, 0, keys.kbAltE),
    _('F', TALT, 0, keys.kbAltF),
    _('G', TALT, 0, keys.kbAltG),
    _('H', TALT, 0, keys.kbAltH),
    _('I', TALT, 0, keys.kbAltI),
    _('J', TALT, 0, keys.kbAltJ),
    _('K', TALT, 0, keys.kbAltK),
    _('L', TALT, 0, keys.kbAltL),
    _('M', TALT, 0, keys.kbAltM),
    _('N', TALT, 0, keys.kbAltN),
    _('O', TALT, 0, keys.kbAltO),
    _('P', TALT, 0, keys.kbAltP),
    _('Q', TALT, 0, keys.kbAltQ),
    _('R', TALT, 0, keys.kbAltR),
    _('S', TALT, 0, keys.kbAltS),
    _('T', TALT, 0, keys.kbAltT),
    _('U', TALT, 0, keys.kbAltU),
    _('V', TALT, 0, keys.kbAltV),
    _('W', TALT, 0, keys.kbAltW),
    _('X', TALT, 0, keys.kbAltX),
    _('Y', TALT, 0, keys.kbAltY),
    _('Z', TALT, 0, keys.kbAltZ),

    # escape codes
    _(curses.KEY_DOWN, 0, 0, keys.kbDown),
    _(curses.KEY_UP, 0, 0, keys.kbUp),
    _(curses.KEY_LEFT, 0, 0, keys.kbLeft),
    _(curses.KEY_RIGHT, 0, 0, keys.kbRight),
    _(curses.KEY_HOME, 0, 0, keys.kbHome),
    _(curses.KEY_BACKSPACE, 0, 0, keys.kbBackSpace),
    _(curses.KEY_DC, 0, MCTRL, keys.kbCtrlDel),
    _(curses.KEY_IC, 0, MCTRL, keys.kbCtrlIns),
    _(curses.KEY_NPAGE, 0, MCTRL, keys.kbCtrlPgDn),
    _(curses.KEY_PPAGE, 0, MCTRL, keys.kbCtrlPgUp),
    _(curses.KEY_END, 0, MCTRL, keys.kbCtrlEnd),
    _(curses.KEY_DC, 0, MSHIFT, keys.kbShiftDel),
    _(curses.KEY_IC, 0, MSHIFT, keys.kbShiftIns),
    _(curses.KEY_DC, 0, 0, keys.kbDel),
    _(curses.KEY_IC, 0, 0, keys.kbIns),
    _(curses.KEY_NPAGE, 0, 0, keys.kbPgDn),
    _(curses.KEY_PPAGE, 0, 0, keys.kbPgUp),
    _(curses.KEY_END, 0, 0, keys.kbEnd),
    _(curses.KEY_LEFT, 0, MCTRL, keys.kbCtrlLeft),
    _(curses.KEY_RIGHT, 0, MCTRL, keys.kbCtrlRight),
    _(curses.KEY_UP, 0, MCTRL, keys.kbCtrlUp),
    _(curses.KEY_DOWN, 0, MCTRL, keys.kbCtrlDown),
    _(curses.KEY_HOME, 0, MCTRL, keys.kbCtrlHome),
    _(curses.KEY_LL, 0, 0, keys.kbCtrlPgDn),
    _(curses.KEY_BEG, 0, 0, keys.kbCtrlPgUp),
    _(curses.KEY_COPY, 0, 0, keys.kbCtrlIns),
    _(curses.KEY_SBEG, 0, 0, keys.kbShiftIns),
    _(curses.KEY_SHOME, 0, 0, keys.kbShiftHome),
    _(curses.KEY_SEND, 0, 0, keys.kbShiftEnd),
    _(curses.KEY_SLEFT, 0, 0, keys.kbShiftLeft),
    _(curses.KEY_SRIGHT, 0, 0, keys.kbShiftRight),
    _(curses.KEY_SR, 0, 0, keys.kbShiftUp),
    _(curses.KEY_SF, 0, 0, keys.kbShiftDown),

    _(KEY_F(1), 0, 0, keys.kbF1),
    _(KEY_F(2), 0, 0, keys.kbF2),
    _(KEY_F(3), 0, 0, keys.kbF3),
    _(KEY_F(4), 0, 0, keys.kbF4),
    _(KEY_F(5), 0, 0, keys.kbF5),
    _(KEY_F(6), 0, 0, keys.kbF6),
    _(KEY_F(7), 0, 0, keys.kbF7),
    _(KEY_F(8), 0, 0, keys.kbF8),
    _(KEY_F(9), 0, 0, keys.kbF9),
    _(KEY_F(10), 0, 0, keys.kbF10),
    _(KEY_F(11), 0, 0, keys.kbF11),
    _(KEY_F(12), 0, 0, keys.kbF12),

    _(KEY_F(1), 0, MCTRL, keys.kbCtrlF1),
    _(KEY_F(2), 0, MCTRL, keys.kbCtrlF2),
    _(KEY_F(3), 0, MCTRL, keys.kbCtrlF3),
    _(KEY_F(4), 0, MCTRL, keys.kbCtrlF4),
    _(KEY_F(5), 0, MCTRL, keys.kbCtrlF5),
    _(KEY_F(6), 0, MCTRL, keys.kbCtrlF6),
    _(KEY_F(7), 0, MCTRL, keys.kbCtrlF7),
    _(KEY_F(8), 0, MCTRL, keys.kbCtrlF8),
    _(KEY_F(9), 0, MCTRL, keys.kbCtrlF9),
    _(KEY_F(10), 0, MCTRL, keys.kbCtrlF10),
    _(KEY_F(11), 0, MCTRL, keys.kbCtrlF11),
    _(KEY_F(12), 0, MCTRL, keys.kbCtrlF12),

    _(KEY_F(1), 0, MALT, keys.kbAltF1),
    _(KEY_F(2), 0, MALT, keys.kbAltF2),
    _(KEY_F(3), 0, MALT, keys.kbAltF3),
    _(KEY_F(4), 0, MALT, keys.kbAltF4),
    _(KEY_F(5), 0, MALT, keys.kbAltF5),
    _(KEY_F(6), 0, MALT, keys.kbAltF6),
    _(KEY_F(7), 0, MALT, keys.kbAltF7),
    _(KEY_F(8), 0, MALT, keys.kbAltF8),
    _(KEY_F(9), 0, MALT, keys.kbAltF9),
    _(KEY_F(10), 0, MALT, keys.kbAltF10),
    _(KEY_F(11), 0, MALT, keys.kbAltF11),
    _(KEY_F(12), 0, MALT, keys.kbAltF12),

    _(KEY_F(13), 0, MSHIFT, keys.kbShiftF1),
    _(KEY_F(14), 0, MSHIFT, keys.kbShiftF2),
    _(KEY_F(15), 0, MSHIFT, keys.kbShiftF3),
    _(KEY_F(16), 0, MSHIFT, keys.kbShiftF4),
    _(KEY_F(17), 0, MSHIFT, keys.kbShiftF5),
    _(KEY_F(18), 0, MSHIFT, keys.kbShiftF6),
    _(KEY_F(19), 0, MSHIFT, keys.kbShiftF7),
    _(KEY_F(20), 0, MSHIFT, keys.kbShiftF8),
    _(KEY_F(21), 0, MSHIFT, keys.kbShiftF9),
    _(KEY_F(22), 0, MSHIFT, keys.kbShiftF10),
    _(KEY_F(23), 0, MSHIFT, keys.kbShiftF11),
    _(KEY_F(24), 0, MSHIFT, keys.kbShiftF12),

    # Shift'ed codes in xterm
    _(KEY_F(13), 0, 0, keys.kbShiftF1),
    _(KEY_F(14), 0, 0, keys.kbShiftF2),
    _(KEY_F(15), 0, 0, keys.kbShiftF3),
    _(KEY_F(16), 0, 0, keys.kbShiftF4),
    _(KEY_F(17), 0, 0, keys.kbShiftF5),
    _(KEY_F(18), 0, 0, keys.kbShiftF6),
    _(KEY_F(19), 0, 0, keys.kbShiftF7),
    _(KEY_F(20), 0, 0, keys.kbShiftF8),
    _(KEY_F(21), 0, 0, keys.kbShiftF9),
    _(KEY_F(22), 0, 0, keys.kbShiftF10),
    _(KEY_F(23), 0, 0, keys.kbShiftF11),
    _(KEY_F(24), 0, 0, keys.kbShiftF12),

    # Ctrl'ed codes in xterm
    _(KEY_F(25), 0, 0, keys.kbCtrlF1),
    _(KEY_F(26), 0, 0, keys.kbCtrlF2),
    _(KEY_F(27), 0, 0, keys.kbCtrlF3),
    _(KEY_F(28), 0, 0, keys.kbCtrlF4),
    _(KEY_F(29), 0, 0, keys.kbCtrlF5),
    _(KEY_F(30), 0, 0, keys.kbCtrlF6),
    _(KEY_F(31), 0, 0, keys.kbCtrlF7),
    _(KEY_F(32), 0, 0, keys.kbCtrlF8),
    _(KEY_F(33), 0, 0, keys.kbCtrlF9),
    _(KEY_F(34), 0, 0, keys.kbCtrlF10),
    _(KEY_F(35), 0, 0, keys.kbCtrlF11),
    _(KEY_F(36), 0, 0, keys.kbCtrlF12),

    # Alt'ed (Meta'ed) codes in xterm
    _(KEY_F(37), 0, 0, keys.kbAltF1),
    _(KEY_F(38), 0, 0, keys.kbAltF2),
    _(KEY_F(39), 0, 0, keys.kbAltF3),
    _(KEY_F(40), 0, 0, keys.kbAltF4),
    _(KEY_F(41), 0, 0, keys.kbAltF5),
    _(KEY_F(42), 0, 0, keys.kbAltF6),
    _(KEY_F(43), 0, 0, keys.kbAltF7),
    _(KEY_F(44), 0, 0, keys.kbAltF8),
    _(KEY_F(45), 0, 0, keys.kbAltF9),
    _(KEY_F(46), 0, 0, keys.kbAltF10),
    _(KEY_F(47), 0, 0, keys.kbAltF11),
    _(KEY_F(48), 0, 0, keys.kbAltF12),
)

keyMappings = {(k.keycode, k.type, k.modifiers): k for k in _keyMappings}
showMarkers = False


def kbMapKey(code, eventType: int, modifiers: int) -> int:
    best = keyMappings.get((code, eventType, modifiers))
    
    if best:
        return best.key
    
    if isinstance(code, str):
        code = ord(code)
    
    if code <= 255:
        return code
    # unknown code
    return keys.kbNoKey
