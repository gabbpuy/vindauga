# -*- coding: utf-8 -*-
import curses
import logging
import platform
from typing import Union

from vindauga.constants.keys import *

logger = logging.getLogger(__name__)
MALT = kbLeftAlt | kbRightAlt
MCTRL = kbLeftCtrl | kbRightCtrl
MSHIFT = kbLeftShift | kbRightShift

PLATFORM_IS_CYGWIN = platform.system().lower().startswith('cygwin')

SHIFT_NAMES = {'KEY_SBEG': curses.KEY_BEG,
               'KEY_SCANCEL': curses.KEY_CANCEL,
               'KEY_SCOMMAND': curses.KEY_COMMAND,
               'KEY_SCOPY': curses.KEY_COPY,
               'KEY_SCREATE': curses.KEY_CREATE,
               'KEY_SDC': curses.KEY_DC,
               'KEY_SDL': curses.KEY_DL,
               'KEY_SEND': curses.KEY_SEND,
               'KEY_SEOL': curses.KEY_EOL,
               'KEY_SEXIT': curses.KEY_EXIT,
               'KEY_SFIND': curses.KEY_FIND,
               'KEY_SHELP': curses.KEY_HELP,
               'KEY_SHOME': curses.KEY_HOME,
               'KEY_SIC': curses.KEY_IC,
               'KEY_SLEFT': curses.KEY_LEFT,
               'KEY_SMESSAGE': curses.KEY_MESSAGE,
               'KEY_SMOVE': curses.KEY_MOVE,
               'KEY_SNEXT': curses.KEY_NEXT,
               'KEY_SOPTIONS': curses.KEY_OPTIONS,
               'KEY_SPREVIOUS': curses.KEY_PREVIOUS,
               'KEY_SPRINT': curses.KEY_PRINT,
               'KEY_SR': curses.KEY_UP,
               'KEY_SF': curses.KEY_DOWN,
               'KEY_SREDO': curses.KEY_REDO,
               'KEY_SREPLACE': curses.KEY_REPLACE,
               'KEY_SRESET': curses.KEY_RESET,
               'KEY_SRIGHT': curses.KEY_RIGHT,
               'KEY_SRSUME': curses.KEY_RESUME,
               'KEY_SSAVE': curses.KEY_SAVE,
               'KEY_SSUSPEND': curses.KEY_SUSPEND,
               'KEY_STAB': 9,  # tab
               'KEY_SUNDO': curses.KEY_UNDO,
               }


def get_key_mapping(code: Union[int, str]) -> Union[tuple[str, int], tuple[int, int]]:
    if isinstance(code, str):
        return code, 0

    s = curses.keyname(code)
    s = str(s, encoding='utf-8')

    if s in SHIFT_NAMES:
        return SHIFT_NAMES[s], MSHIFT
    if s.startswith('^'):
        return ord(s[-1]), MCTRL
    if s.startswith('M-'):
        return ord(s[-1]), MALT
    return code, 0


if PLATFORM_IS_CYGWIN:
    # Cygwin maps modified keys to a set of keys that are 'k<SYMBOL><MASK>'
    CYGWIN_KEYS = {
        'kBEG': curses.KEY_BEG,
        'kCAN': curses.KEY_CANCEL,
        'kCMD': curses.KEY_COMMAND,
        'kCPY': curses.KEY_COPY,
        'kCRT': curses.KEY_CREATE,
        'kDC': curses.KEY_DC,
        'kDN': curses.KEY_DOWN,
        'kEND': curses.KEY_END,
        'kEOL': curses.KEY_EOL,
        'kEXT': curses.KEY_EXIT,
        'kFND': curses.KEY_FIND,
        'kHLP': curses.KEY_HELP,
        'kHOM': curses.KEY_HOME,
        'kIC': curses.KEY_IC,
        'kLFT': curses.KEY_LEFT,
        'kMOV': curses.KEY_MOVE,
        'kMSG': curses.KEY_MESSAGE,
        'kNXT': curses.KEY_NEXT,
        'kOPT': curses.KEY_OPTIONS,
        'kPRT': curses.KEY_PRINT,
        'kPRV': curses.KEY_PREVIOUS,
        'kRDO': curses.KEY_REDO,
        'kRES': curses.KEY_RESET,  # I think
        'kRIT': curses.KEY_RIGHT,
        'kRPL': curses.KEY_REPLACE,
        'kSAV': curses.KEY_SAVE,
        'kSPD': curses.KEY_SUSPEND,
        'kUND': curses.KEY_UNDO,
        'kUP': curses.KEY_UP,
    }

    CYGWIN_MODIFIERS = {
        '3': MALT,
        '4': MALT | MCTRL | MSHIFT,
        '5': MCTRL,
        '6': MCTRL | MSHIFT,
        '7': MCTRL | MALT
    }

    _generic_get = get_key_mapping


    def get_key_mapping(code: Union[int, str]) -> Union[tuple[str, int], tuple[int, int]]:
        if isinstance(code, str):
            return code, 0

        s = curses.keyname(code)
        s = str(s, encoding='utf-8')
        if s in SHIFT_NAMES:
            return _generic_get(code)
        if s[:-1] in CYGWIN_KEYS:
            key = CYGWIN_KEYS[s[:-1]]
            mod = CYGWIN_MODIFIERS[s[-1]]
            return key, mod
        return code, 0
