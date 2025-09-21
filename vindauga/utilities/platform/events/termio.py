# -*- coding: utf-8 -*-
"""
Handles terminal input/output operations and escape sequence parsing
"""
import base64

import string

import os

import time

import logging
from typing import TYPE_CHECKING, Callable

from vindauga.constants.event_codes import (evKeyDown, evMouse, mbLeftButton, mbMiddleButton, mbRightButton, mwUp,
                                            mwDown, evNothing)
import vindauga.constants.keys as Keys
from vindauga.constants.key_mappings import kbMapKey, TALT
from vindauga.events.event import Event
from vindauga.events.key_down_event import KeyDownEvent
from vindauga.events.modded_key_codes import moddedKeyCodes
from vindauga.events.mouse_event import MouseEvent
from vindauga.utilities.platform.adapters.console_ctl import ConsoleCtl
from vindauga.types.key import Key
from vindauga.types.point import Point

from .csi_data import CSIData

from .get_ch_buf import GetChBuf
from .input_getter import InputGetter
from .parse_result import ParseResult
from .input_state import InputState
from .win32_input_mode_unwrapper import Win32InputModeUnwrapper, parse_win32_input_mode_key
from ..codepage.codepage_translator import CodepageTranslator

if TYPE_CHECKING:
    from vindauga.utilities.platform.events.input_state import InputState

logger = logging.getLogger(__name__)

mmAlt = 0x08
mmCtrl = 0x10

# Key mapping for XTerm modifier letters
LETTER_KEY_MAP = {
    ord('A'): Keys.kbUp,
    ord('B'): Keys.kbDown,
    ord('C'): Keys.kbRight,
    ord('D'): Keys.kbLeft,
    ord('E'): Keys.kbNoKey,  # Numpad 5, "KP_Begin"
    ord('F'): Keys.kbEnd,
    ord('H'): Keys.kbHome,
    ord('P'): Keys.kbF1,
    ord('Q'): Keys.kbF2,
    ord('R'): Keys.kbF3,
    ord('S'): Keys.kbF4,
    ord('Z'): Keys.kbTab,
    # Keypad in XTerm (SS3)
    ord('j'): ord('*'),
    ord('k'): ord('+'),
    ord('m'): ord('-'),
    ord('M'): Keys.kbEnter,
    ord('n'): Keys.kbDel,
    ord('o'): ord('/'),
    ord('p'): Keys.kbIns,
    ord('q'): Keys.kbEnd,
    ord('r'): Keys.kbDown,
    ord('s'): Keys.kbPgDn,
    ord('t'): Keys.kbLeft,
    ord('u'): Keys.kbNoKey,  # Numpad 5, "KP_Begin"
    ord('v'): Keys.kbRight,
    ord('w'): Keys.kbHome,
    ord('x'): Keys.kbUp,
    ord('y'): Keys.kbPgUp,
}

CODEPOINT_KEY_MAP = {
    8: Keys.kbBackSpace,
    9: Keys.kbTab,
    13: Keys.kbEnter,
    27: Keys.kbEsc,
    127: Keys.kbBackSpace,
    7399: '0',
    7400: '1',
    7401: '2',
    7402: '3',
    7403: '4',
    7404: '5',
    7405: '6',
    7406: '7',
    7407: '8',
    7408: '9',
    7409: '.',
    7410: '/',
    7411: '*',
    7412: '-',
    7413: '+',
    7414: Keys.kbEnter,
    7415: '=',
    7416: ',',
    7417: Keys.kbLeft,
    7418: Keys.kbRight,
    7419: Keys.kbUp,
    7420: Keys.kbDown,
    7421: Keys.kbPgUp,
    7422: Keys.kbPgDn,
    7423: Keys.kbHome,
    7424: Keys.kbEnd,
    7425: Keys.kbIns,
    7426: Keys.kbDel,
}


class TermIO:
    """
    Handles terminal I/O operations and input parsing
    """
    def parse_event(self, buf: GetChBuf, event: Event, state: InputState) -> ParseResult:
        """
        Parse input event from character buffer
        """
        if buf.get() == 0x1b:
            return self.parse_escape_seq(buf, event, state)
        return ParseResult.Rejected

    def parse_win32_input_mode_key_or_escape_sequence(self, csi: CSIData, input_getter: InputGetter,
                                                      event: Event, state: InputState) -> ParseResult:
        res = parse_win32_input_mode_key(csi, event, state)
        if res == ParseResult.Accepted and event.keyDown == 0x001b:
            unwrapper = Win32InputModeUnwrapper(input_getter, state)
            buf = GetChBuf(unwrapper)
            res = self.parse_escape_seq(buf, event, state)
            if res != ParseResult.Accepted:
                res = ParseResult.Ignored
        return res

    def parse_escape_seq(self, buf: GetChBuf, event: Event, state: InputState) -> ParseResult:
        """
        Parse escape sequence
        Pre: "\x1B" has just been read.
        """
        res = ParseResult.Rejected

        k = buf.get()

        if k == -1:
            return res

        k = chr(k)

        if k == '_':
            # DCS sequences starting with ESC_ - consume but ignore for now
            return ParseResult.Ignored

        elif k == '[':
            # CSI sequences
            next_k = chr(buf.get())
            # These shouldn't normally appear here...
            if next_k == 'M':
                if self.parse_x10_mouse(buf, event, state) == ParseResult.Accepted:
                    return ParseResult.Accepted
                return ParseResult.Ignored
            elif next_k == '<':
                if self.parse_sgr_mouse(buf, event, state) == ParseResult.Accepted:
                    return ParseResult.Accepted
                return ParseResult.Ignored
            else:
                buf.unget()
                csi = CSIData()
                if csi.read_from(buf):
                    if csi.terminator == ord('u'):
                        # FixTerm key - basic implementation
                        return self._parse_fix_term_key(csi, event)
                    elif csi.terminator == ord('R'):
                        # CPR (Cursor Position Report) - basic implementation
                        return self._parse_cpr(csi, state)
                    elif csi.terminator == ord('_'):
                        # DCS sequences (Device Control String) - consume but ignore
                        return self.parse_win32_input_mode_key_or_escape_sequence(csi, buf.in_getter, event, state)
                    else:
                        return self.parse_csi_key(csi, event, state)
        elif k == 'O':
            # SS3 sequences
            return self.parse_ss3_key(buf, event)
        elif k == 'P':
            # DCS sequences - basic implementation
            return self._parse_dcs(buf, state)
        elif k == ']':
            # OSC sequences - basic implementation
            return self._parse_osc(buf, state)
        elif k == '\x1B':
            res = self.parse_escape_seq(buf, event, state)
            if res == ParseResult.Accepted and event.what == evKeyDown:
                event.keyDown.controlKeyState |= Keys.kbLeftAlt
                self.normalize_key(event.keyDown)
        return res

    def parse_csi_key(self, csi: CSIData, event: Event, state: InputState) -> ParseResult:
        """
        Parse CSI key sequence
        """

        terminator = csi.terminator

        if csi.length == 1 and terminator == ord('~'):
            # Single parameter with ~ terminator
            val = csi.get_value(0)
            key_map = {
                1: Keys.kbHome, 2: Keys.kbIns, 3: Keys.kbDel, 4: Keys.kbEnd,
                5: Keys.kbPgUp, 6: Keys.kbPgDn,
                11: Keys.kbF1, 12: Keys.kbF2, 13: Keys.kbF3, 14: Keys.kbF4, 15: Keys.kbF5,
                17: Keys.kbF6, 18: Keys.kbF7, 19: Keys.kbF8, 20: Keys.kbF9, 21: Keys.kbF10,
                23: Keys.kbShiftF1, 24: Keys.kbShiftF2, 25: Keys.kbShiftF3, 26: Keys.kbShiftF4,
                28: Keys.kbShiftF5, 29: Keys.kbShiftF6, 31: Keys.kbShiftF7, 32: Keys.kbShiftF8,
                33: Keys.kbShiftF9, 34: Keys.kbShiftF10,
                200: None,  # Bracketed paste start
                201: None,  # Bracketed paste end
            }

            if val in [200, 201]:
                state.bracketed_paste = (val == 200)
                return ParseResult.Ignored
            elif val in key_map:
                key_event = KeyDownEvent()
                key_event.keyCode = key_map[val]
                if val in [23, 24, 25, 26, 28, 29, 31, 32, 33, 34]:
                    key_event.controlKeyState = Keys.kbShift
                event.what = evKeyDown
                event.keyDown = key_event
                return ParseResult.Accepted
            else:
                return ParseResult.Rejected

        elif csi.length == 1 and csi.get_value(0) == 1:
            # Arrow keys and function keys without modifiers
            if not self.key_from_letter(terminator, 1, event.keyDown):
                return ParseResult.Rejected

        elif csi.length == 2:
            # Two parameters
            mod = csi.get_value(1)
            if csi.get_value(0) == 1:
                # Modified arrow/function keys
                if not self.key_from_letter(terminator, mod, event.keyDown):
                    return ParseResult.Rejected
            elif terminator == ord('~'):
                # Modified special keys
                val = csi.get_value(0)
                key_map = {
                    2: Keys.kbIns, 3: Keys.kbDel, 5: Keys.kbPgUp, 6: Keys.kbPgDn,
                    11: Keys.kbF1, 12: Keys.kbF2, 13: Keys.kbF3, 14: Keys.kbF4, 15: Keys.kbF5,
                    17: Keys.kbF6, 18: Keys.kbF7, 19: Keys.kbF8, 20: Keys.kbF9, 21: Keys.kbF10,
                    23: Keys.kbF11, 24: Keys.kbF12, 29: Keys.kbNoKey,  # Menu key
                }
                if val in key_map:
                    event.keyDown.update(self.key_with_xterm_mods(key_map[val], mod))
            else:
                return ParseResult.Rejected
        elif csi.length == 3 and csi.get_value(0) == 27 and terminator == ord('~'):
            key = csi.get_value(2)
            mod = csi.get_value(1)
            if not self.key_from_codepoint(key, mod, event.keyDown):
                return ParseResult.Ignored
        else:
            return ParseResult.Rejected

        event.what = evKeyDown
        return ParseResult.Accepted

    def parse_ss3_key(self, buf: GetChBuf, event: Event) -> ParseResult:
        """
        Parse SS3 key sequence
        """
        read, mod = buf.get_num()
        if not read:
            return ParseResult.Rejected
        key = buf.last()
        if not self.key_from_letter(key, mod, event.keyDown):
            return ParseResult.Rejected
        event.what = evKeyDown
        return ParseResult.Accepted

    def key_from_letter(self, letter: int, mod: int, key_down: KeyDownEvent) -> bool:
        """
        Convert letter to key with modifiers
        """
        if letter not in LETTER_KEY_MAP:
            return False
        key_code = LETTER_KEY_MAP[letter]
        key_down.update(self.key_with_xterm_mods(key_code, mod))

        if 0x20 <= key_down.keyCode < 0x7F:
            key_down.text[0] = key_down.keyCode
            key_down.textLength = 1
        return True

    def key_with_xterm_mods(self, key_code: int, mods: int) -> KeyDownEvent:
        """
        Create key event with XTerm modifiers
        """
        mods -= 1  # XTermModDefault = 1

        tv_mods = 0
        if mods & 1:  # Shift
            tv_mods |= Keys.kbShift
        if mods & 2:  # Alt
            tv_mods |= Keys.kbLeftAlt
        if mods & 4:  # Ctrl
            tv_mods |= Keys.kbLeftCtrl

        key_event = KeyDownEvent()
        key_event.keyCode = key_code
        key_event.controlKeyState = tv_mods
        term_io.normalize_key(key_event)
        return key_event

    def is_private(self, codepoint: int) -> bool:
        return 0xE000 <= codepoint <= 0xF8FF

    def key_from_codepoint(self, value: int, mods: int, key_down: KeyDownEvent) -> bool:
        key_code = 0
        if value in CODEPOINT_KEY_MAP:
            key_code = CODEPOINT_KEY_MAP[value]
        elif 0x20 <= value < 0x7f:
            key_code = value

        key_down.update(self.key_with_xterm_mods(key_code, mods))
        if 0x20 <= key_down.keyCode < 0x7f or key_down.keyCode == 0x00 and 0x20 <= value and not self.is_private(value):
            codepoint = value if key_down.keyCode == 0 else key_down.keyCode
            bytes_32 = key_down.text.decode('utf-32')
            bytes_8 = bytes_32.encode('utf-8')
            key_down.textLength = len(bytes_8)
            key_down.charScan.charCode = CodepageTranslator().printable_from_utf8(key_down.text)
        return key_down.keyCode != 0 or key_down.textLength != 0

    def normalize_key(self, key_event: KeyDownEvent):
        """
        Normalize key event
        """

        key = Key(key_event.keyCode, key_event.controlKeyState)

        # Check for modifier keys (Shift, Ctrl, Alt)
        new_mods = key.mods & (Keys.kbShift | Keys.kbLeftCtrl | Keys.kbLeftAlt)

        if new_mods != 0:
            largest_mod = 0
            if new_mods & Keys.kbLeftAlt:
                largest_mod = 2
            elif new_mods & Keys.kbLeftCtrl:
                largest_mod = 1

            if key_code := moddedKeyCodes.get(key.code, [0, 0, 0])[largest_mod]:
                key_event.keyCode = key_code
                if key_event.charScan.charCode < ' ':
                    key_event.textLength = 0

        orig_mods = key_event.controlKeyState
        key_event.controlKeyState = (orig_mods | new_mods) & ~(Keys.kbCtrlShift | Keys.kbAltShift)
        if not orig_mods & Keys.kbCtrlShift:
            key_event.controlKeyState |= (new_mods & Keys.kbCtrlShift)
        else:
            key_event.controlKeyState |= (orig_mods & Keys.kbCtrlShift)

        if not orig_mods & Keys.kbAltShift:
            key_event.controlKeyState |= (new_mods & Keys.kbAltShift)
        else:
            key_event.controlKeyState |= (orig_mods & Keys.kbAltShift)

    def mouse_on(self, console_ctl: 'ConsoleCtl') -> None:
        """
        Enable mouse reporting
        """
        # ANSI escape sequences to enable mouse reporting
        """
            1 0 0 0  -> Send Mouse X & Y on button press and release.
            1 0 0 1  -> Use Hilite Mouse Tracking.
            1 0 0 2  -> Use Cell Motion Mouse Tracking.
            1 0 0 3  -> Use All Motion Mouse Tracking.
            1 0 0 5  -> Enable UTF-8 Mouse Mode.
            1 0 0 6  -> Enable SGR Mouse Mode.
            1 0 1 5  -> Enable urxvt Mouse Mode.
        """
        seq = (
            "\x1B[?1001s"  # Save old hilite mouse reporting
            "\x1B[?1000h"  # Enable mouse reporting
            "\x1B[?1002h"  # Enable mouse drag reporting
            "\x1B[?1006h"  # Enable SGR extended mouse reporting
        )
        console_ctl.write(seq)

    def mouse_off(self, console_ctl: 'ConsoleCtl') -> None:
        """

        Disable mouse reporting
        """
        # ANSI escape sequences to disable mouse reporting
        seq = (
            "\x1B[?1006l"  # Disable SGR extended mouse reporting
            "\x1B[?1002l"  # Disable mouse drag reporting
            "\x1B[?1000l"  # Disable mouse reporting
            "\x1B[?1001r"  # Restore old highlight mouse reporting
        )
        console_ctl.write(seq)

    def key_mods_on(self, console_ctl: 'ConsoleCtl') -> None:
        """
        Enable key modifier reporting
        """
        # ANSI escape sequences to enable key modifier reporting
        seq = (
            "\x1B[?1036s"   # Save metaSendsEscape (XTerm).
            "\x1B[?1036h"   # Enable metaSendsEscape (XTerm).
            "\x1B[?2004s"   # Save bracketed paste.
            "\x1B[?2004h"   # Enable bracketed paste.
            "\x1B[>4;1m"    # Enable modifyOtherKeys (XTerm).
            "\x1B[>1u"      # Disambiguate escape codes (Kitty).
            "\x1B[?9001h"   # Enable win32-input-mode (Conpty).
            # far2lEnableSeq  # Enable far2l terminal extensions.
        )
        if term := os.environ.get('TERM'):
            if 'alacritty' in term or 'foot' in term:
                seq += "\x1B]52;;?\x07"
            else:
                seq += (
                    # Check for the 'kitty-query-clipboard_control' capability (XTGETTCAP).
                    "\x1BP+q6b697474792d71756572792d636c6970626f6172645f636f6e74726f6c\x1B\\"
                    # Check for 'allowWindowOps' (XTQALLOWED).
                    "\x1B]60\x1B\\"
                )
        # Clear the screen so the unsupported sequences from above are not displayed
        seq += '\x1B[2J'
        console_ctl.write(seq)

    def key_mods_off(self, console_ctl: 'ConsoleCtl') -> None:
        """
        Disable key modifier reporting
        """
        seq = (
          "\x1B[?9001l" # Disable win32-input-mode (Conpty).
          "\x1B[<u"     # Restore previous keyboard mode (Kitty).
          "\x1B[>4m"    # Reset modifyOtherKeys (XTerm).
          "\x1B[?2004l" # Disable bracketed paste.
          "\x1B[?2004r" # Restore bracketed paste.
          "\x1B[?1036r" # Restore metaSendsEscape (XTerm).
        )
        console_ctl.write(seq)

    def parse_x10_mouse(self, buf: GetChBuf, event: Event, state: InputState) -> ParseResult:
        """
        Parse X10 mouse sequence - basic implementation
        """
        # X10 mouse format: ESC[Mbxy where b=button+32, x=col+32, y=row+32
        but_m = buf.get()
        mod = but_m & (mmAlt | mmCtrl)
        but = (but_m & ~(mmAlt | mmCtrl)) - 32
        if (255 - 32) < but:
            return ParseResult.Rejected

        def get_loc():
            x = buf.get()
            if not 0 <= x <= 255:
                return ParseResult.Rejected

            if x > 32:
                x -= 32
            else:
                x += (256 - 32)
            x -= 1
            return x

        col = get_loc()
        row = get_loc()
        event.what = evMouse
        event.mouse = MouseEvent()
        event.mouse.where = Point(col, row)
        event.mouse.controlKeyState = (Keys.kbLeftAlt if mod & mmAlt else 0) | (Keys.kbLeftCtrl if mod & mmCtrl else 0)
        if but in (0, 32):
            state.buttons |= mbLeftButton
        elif but in (1, 33):
            state.buttons |= mbMiddleButton
        elif but in (2, 34):
            state.buttons |= mbRightButton
        elif but == 3:
            state.buttons = 0
        elif but == 64:
            event.mouse.wheel = mwUp
        elif but == 65:
            event.mouse.wheel = mwDown
        event.mouse.buttons = state.buttons
        return ParseResult.Accepted

    def parse_sgr_mouse(self, buf: GetChBuf, event: Event, state: InputState) -> ParseResult:
        read, but_m = buf.get_num()
        if not read:
            return ParseResult.Rejected
        mod = but_m & (mmAlt | mmCtrl)
        but = but_m & ~(mmAlt | mmCtrl)

        col, row = (buf.get_int()[1], buf.get_int()[1])

        if not (col and row):
            return ParseResult.Rejected

        row = max(row, 1) - 1
        col = max(col, 1) - 1

        type_ = chr(buf.last())

        if type_ not in 'Mm':
            return ParseResult.Rejected

        event.what = evMouse
        event.mouse = MouseEvent()
        event.mouse.where.x = col
        event.mouse.where.y = row
        event.mouse.controlKeyState = (Keys.kbLeftAlt if mod & mmAlt else 0) | (Keys.kbLeftCtrl if mod & mmCtrl else 0)

        if type_ == 'M':  # down / wheel / drag
            if but in (0, 32):
                state.buttons |= mbLeftButton
            elif but in (1, 33):
                state.buttons |= mbMiddleButton
            elif but in (2, 34):
                state.buttons |= mbRightButton
            elif but == 64:
                event.mouse.wheel = mwUp
            elif but == 65:
                event.mouse.wheel = mwDown
        else:
            if but == 0:
                state.buttons &= ~mbLeftButton
            elif but == 1:
                state.buttons &= ~mbMiddleButton
            elif but == 2:
                state.buttons &= ~mbRightButton
        event.mouse.buttons = state.buttons
        return ParseResult.Accepted

    def _parse_fix_term_key(self, csi: CSIData, event: Event) -> ParseResult:
        if csi.length < 1 or csi.terminator != ord('u'):
            return ParseResult.Rejected

        key = csi.get_value(0)
        mod = max(csi.get_value(1), 1) if csi.length > 1 else 1
        if self.key_from_codepoint(key, mod, event.keyDown):
            event.what = event.keyDown
            return ParseResult.Accepted
        return ParseResult.Ignored

    def _read_until_bel_or_st(self, buf: GetChBuf) -> str:
        length: int = 0
        s = []
        while c := buf.get_unbuffered() != -1:
            if c == 0x07:
                break
            if chr(c) == '\\' and s and s[-1] == 0x1b:
                length -= bool(length > 0)
                break
            s.append(c)
        return ''.join(map(chr, s))

    def _parse_cpr(self, csi: CSIData, state: InputState) -> ParseResult:
        """
        Parse Cursor Position Report - basic implementation
        """
        if csi.length != 2:
            return ParseResult.Rejected
        state.got_response = True
        return ParseResult.Ignored

    def _parse_dcs(self, buf: GetChBuf, state: InputState) -> ParseResult:
        """
        Parse DCS sequence
        """
        s = self._read_until_bel_or_st(buf)
        if '726561642d636c6970626f617264' in s:
            state.has_full_osc52 = True
        return ParseResult.Ignored

    def _parse_osc(self, buf: GetChBuf, state: InputState) -> ParseResult:
        """
        Parse OSC sequence
        """
        s = self._read_until_bel_or_st(buf)
        if len(s) > 3 and s[:3] == '52':
            if (begin := s.find(';', 3)) != -1:
                if not state.has_full_osc52:
                    state.has_full_osc52 = True
                else:
                    encoded = s[begin + 1:].encode()
                    decoded = base64.b64decode(encoded).decode()
                    state.put_paste(decoded)
        elif len(s) > 6 and s[3:6] == '60;': # OSC 60
            if 'allowWindowOps' in s[6:]:
                state.has_full_osc52 = True
        return ParseResult.Ignored

    def consume_unprocessed_input(self, console_ctl: ConsoleCtl, input_getter: InputGetter, state: InputState):
        timeout = .2
        seq = '\x1b[6n'
        console_ctl.write(seq)
        ev = Event(evNothing)
        state.got_response = False
        begin = time.time()
        buf = GetChBuf(input_getter)
        while time.time() < begin + timeout and not state.got_response:
            self.parse_event(buf, ev, state)

    def _set_osc52_clipboard(self, console_ctl: ConsoleCtl, text: str, state: InputState) -> bool:
        prefix = "\x1B]52;;"
        suffix = "\x07"
        buf = (
            prefix +
            base64.b64encode(text.encode()).decode() +
            suffix
        )
        console_ctl.write(buf)
        return state.has_full_osc52

    def _request_osc52_clipboard(self, console_ctl: ConsoleCtl, state: InputState) -> bool:
        if state.has_full_osc52:
            seq = "\x1B]52;;?\x07"
            console_ctl.write(seq)
        return state.has_full_osc52

    def set_clipboard_text(self, con: ConsoleCtl, text: str, state: InputState):
        return self._set_osc52_clipboard(con, text, state)

    def request_clipboard_text(self, console_ctl: ConsoleCtl, callback: Callable[[str], None], state: InputState):
        state.put_paste = callback
        self._request_osc52_clipboard(console_ctl, state)


# Create global TermIO instance
term_io = TermIO()
