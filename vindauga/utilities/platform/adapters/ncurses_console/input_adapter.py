# -*- coding: utf-8 -*-
import atexit
import copy
import curses
import logging

from vindauga.constants.event_codes import evKeyDown, mbLeftButton, mbMiddleButton, mbRightButton, mwUp, mwDown
import vindauga.constants.keys as Keys
from vindauga.constants.event_codes import evMouse
from vindauga.events.key_down_event import KeyDownEvent
from vindauga.events.mouse_event import MouseEvent
from vindauga.utilities.platform.adapters.console_ctl import ConsoleCtl
from vindauga.utilities.platform.adapters.input_adapter import InputAdapter
from vindauga.utilities.platform.codepage.codepage_translator import CodepageTranslator
from vindauga.utilities.platform.events.get_ch_buf import GetChBuf
from vindauga.utilities.platform.events.input_state import InputState
from vindauga.utilities.platform.events.parse_result import ParseResult
from vindauga.utilities.platform.events.sys_manual_event import SysHandle
from vindauga.utilities.platform.events.termio import term_io
from vindauga.utilities.platform.events.utf8_handler import utf8_bytes_left

from .ncurses_input_getter import NcursesInputGetter

logger = logging.getLogger(__name__)

_ = KeyDownEvent.create

FROM_NON_PRINTABLE_ASCII = [
    _('@', Keys.kbLeftCtrl, b'@'),  # ^@, Null
    _(Keys.kbCtrlA, Keys.kbLeftCtrl),  # ^A
    _(Keys.kbCtrlB, Keys.kbLeftCtrl),  # ^B
    _(Keys.kbCtrlC, Keys.kbLeftCtrl),  # ^C
    _(Keys.kbCtrlD, Keys.kbLeftCtrl),  # ^D
    _(Keys.kbCtrlE, Keys.kbLeftCtrl),  # ^E
    _(Keys.kbCtrlF, Keys.kbLeftCtrl),  # ^F
    _(Keys.kbCtrlG, Keys.kbLeftCtrl),  # ^G
    _(Keys.kbBackSpace, 0),  # ^H, Backspace
    _(Keys.kbTab, 0),  # ^I, Tab
    _(Keys.kbEnter, 0),  # ^J, Line Feed
    _(Keys.kbCtrlK, Keys.kbLeftCtrl),  # ^K
    _(Keys.kbCtrlL, Keys.kbLeftCtrl),  # ^L
    _(Keys.kbEnter, 0),  # ^M, Carriage Return
    _(Keys.kbCtrlN, Keys.kbLeftCtrl),  # ^N
    _(Keys.kbCtrlO, Keys.kbLeftCtrl),  # ^O
    _(Keys.kbCtrlP, Keys.kbLeftCtrl),  # ^P
    _(Keys.kbCtrlQ, Keys.kbLeftCtrl),  # ^Q
    _(Keys.kbCtrlR, Keys.kbLeftCtrl),  # ^R
    _(Keys.kbCtrlS, Keys.kbLeftCtrl),  # ^S
    _(Keys.kbCtrlT, Keys.kbLeftCtrl),  # ^T
    _(Keys.kbCtrlU, Keys.kbLeftCtrl),  # ^U
    _(Keys.kbCtrlV, Keys.kbLeftCtrl),  # ^V
    _(Keys.kbCtrlW, Keys.kbLeftCtrl),  # ^W
    _(Keys.kbCtrlX, Keys.kbLeftCtrl),  # ^X
    _(Keys.kbCtrlY, Keys.kbLeftCtrl),  # ^Y
    _(Keys.kbCtrlZ, Keys.kbLeftCtrl),  # ^Z
    _(Keys.kbEsc, 0),  # ^[, Escape
    _('\\', Keys.kbLeftCtrl, b'\\'),  # ^\, File Separator
    _(']', Keys.kbLeftCtrl, b']'),  # ^], Group Separator
    _('^', Keys.kbLeftCtrl, b'^'),  # ^^, Record Separator
    _('_', Keys.kbLeftCtrl, b'_'),  # ^_, Unit Separator
]

FROM_CURSES_KEY_CODE = {
    # Basic navigation keys
    curses.KEY_DOWN: _(Keys.kbDown, 0),
    curses.KEY_UP: _(Keys.kbUp, 0),
    curses.KEY_LEFT: _(Keys.kbLeft, 0),
    curses.KEY_RIGHT: _(Keys.kbRight, 0),
    curses.KEY_HOME: _(Keys.kbHome, 0),
    curses.KEY_BACKSPACE: _(Keys.kbBackSpace, 0),
    curses.KEY_DC: _(Keys.kbDel, 0),
    curses.KEY_IC: _(Keys.kbIns, 0),
    curses.KEY_NPAGE: _(Keys.kbPgDn, 0),
    curses.KEY_PPAGE: _(Keys.kbPgUp, 0),
    curses.KEY_END: _(Keys.kbEnd, 0),
    curses.KEY_ENTER: _(Keys.kbEnter, 0),

    # Shift keys
    curses.KEY_SF: _(Keys.kbDown, Keys.kbShift),  # KEY_SF = Shift+Down
    curses.KEY_SR: _(Keys.kbUp, Keys.kbShift),  # KEY_SR = Shift+Up
    curses.KEY_BTAB: _(Keys.kbShiftTab, Keys.kbShift),  # Backtab
    curses.KEY_SDC: _(Keys.kbShiftDel, Keys.kbShift),  # Shift+Del
    curses.KEY_SEND: _(Keys.kbEnd, Keys.kbShift),  # Shift+End
    curses.KEY_SHOME: _(Keys.kbHome, Keys.kbShift),  # Shift+Home
    curses.KEY_SIC: _(Keys.kbShiftIns, Keys.kbShift),  # Shift+Ins
    curses.KEY_SLEFT: _(Keys.kbLeft, Keys.kbShift),  # Shift+Left
    curses.KEY_SRIGHT: _(Keys.kbRight, Keys.kbShift),  # Shift+Right
    curses.KEY_SUSPEND: _(Keys.kbCtrlZ, Keys.kbLeftCtrl),  # Suspend
    curses.KEY_SPREVIOUS: _(Keys.kbPgUp, Keys.kbShift),  # Shift+PgUp
    curses.KEY_SNEXT: _(Keys.kbPgDn, Keys.kbShift),  # Shift+PgDn

    # Keypad keys
    curses.KEY_A1: _(Keys.kbHome, 0),  # Upper left of keypad
    curses.KEY_A3: _(Keys.kbPgUp, 0),  # Upper right of keypad
    curses.KEY_C1: _(Keys.kbEnd, 0),  # Lower left of keypad
    curses.KEY_C3: _(Keys.kbPgDn, 0),  # Lower right of keypad

    # Function keys F1-F12
    curses.KEY_F1: _(Keys.kbF1, 0),
    curses.KEY_F2: _(Keys.kbF2, 0),
    curses.KEY_F3: _(Keys.kbF3, 0),
    curses.KEY_F4: _(Keys.kbF4, 0),
    curses.KEY_F5: _(Keys.kbF5, 0),
    curses.KEY_F6: _(Keys.kbF6, 0),
    curses.KEY_F7: _(Keys.kbF7, 0),
    curses.KEY_F8: _(Keys.kbF8, 0),
    curses.KEY_F9: _(Keys.kbF9, 0),
    curses.KEY_F10: _(Keys.kbF10, 0),
    curses.KEY_F11: _(Keys.kbF11, 0),
    curses.KEY_F12: _(Keys.kbF12, 0),
}

# Dynamic function key mapping - add Shift+F1-F12, Ctrl+F1-F12, Alt+F1-F12
for i in range(1, 13):
    # Shift+F1-F12 (F13-F24)
    key_code = getattr(curses, f'KEY_F{i + 12}', None)
    if key_code:
        FROM_CURSES_KEY_CODE[key_code] = _(getattr(Keys, f'kbShiftF{i}'), Keys.kbShift)

    # Ctrl+F1-F12 (F25-F36)
    key_code = getattr(curses, f'KEY_F{i + 24}', None)
    if key_code:
        FROM_CURSES_KEY_CODE[key_code] = _(getattr(Keys, f'kbCtrlF{i}'), Keys.kbLeftCtrl)

    # Ctrl+Shift+F1-F12 (F37-F48)
    key_code = getattr(curses, f'KEY_F{i + 36}', None)
    if key_code:
        FROM_CURSES_KEY_CODE[key_code] = _(getattr(Keys, f'kbCtrlF{i}'), Keys.kbShift | Keys.kbLeftCtrl)

    # Alt+F1-F12 (F49-F60)
    key_code = getattr(curses, f'KEY_F{i + 48}', None)
    if key_code:
        FROM_CURSES_KEY_CODE[key_code] = _(getattr(Keys, f'kbAltF{i}'), Keys.kbLeftAlt)

FROM_CURSES_HIGH_KEY = {
    # Alt+key combinations (3 = Alt)
    "kDC3": _(Keys.kbAltDel, Keys.kbLeftAlt),
    "kEND3": _(Keys.kbAltEnd, Keys.kbLeftAlt),
    "kHOM3": _(Keys.kbAltHome, Keys.kbLeftAlt),
    "kIC3": _(Keys.kbAltIns, Keys.kbLeftAlt),
    "kLFT3": _(Keys.kbAltLeft, Keys.kbLeftAlt),
    "kNXT3": _(Keys.kbAltPgDn, Keys.kbLeftAlt),
    "kPRV3": _(Keys.kbAltPgUp, Keys.kbLeftAlt),
    "kRIT3": _(Keys.kbAltRight, Keys.kbLeftAlt),
    "kUP3": _(Keys.kbAltUp, Keys.kbLeftAlt),
    "kDN3": _(Keys.kbAltDown, Keys.kbLeftAlt),

    # Shift+Alt+key combinations (4 = Shift+Alt)
    "kDC4": _(Keys.kbAltDel, Keys.kbShift | Keys.kbLeftAlt),
    "kEND4": _(Keys.kbAltEnd, Keys.kbShift | Keys.kbLeftAlt),
    "kHOM4": _(Keys.kbAltHome, Keys.kbShift | Keys.kbLeftAlt),
    "kIC4": _(Keys.kbAltIns, Keys.kbShift | Keys.kbLeftAlt),
    "kLFT4": _(Keys.kbAltLeft, Keys.kbShift | Keys.kbLeftAlt),
    "kNXT4": _(Keys.kbAltPgDn, Keys.kbShift | Keys.kbLeftAlt),
    "kPRV4": _(Keys.kbAltPgUp, Keys.kbShift | Keys.kbLeftAlt),
    "kRIT4": _(Keys.kbAltRight, Keys.kbShift | Keys.kbLeftAlt),
    "kUP4": _(Keys.kbAltUp, Keys.kbShift | Keys.kbLeftAlt),
    "kDN4": _(Keys.kbAltDown, Keys.kbShift | Keys.kbLeftAlt),

    # Ctrl+key combinations (5 = Ctrl)
    "kDC5": _(Keys.kbCtrlDel, Keys.kbLeftCtrl),
    "kEND5": _(Keys.kbCtrlEnd, Keys.kbLeftCtrl),
    "kHOM5": _(Keys.kbCtrlHome, Keys.kbLeftCtrl),
    "kIC5": _(Keys.kbCtrlIns, Keys.kbLeftCtrl),
    "kLFT5": _(Keys.kbCtrlLeft, Keys.kbLeftCtrl),
    "kNXT5": _(Keys.kbCtrlPgDn, Keys.kbLeftCtrl),
    "kPRV5": _(Keys.kbCtrlPgUp, Keys.kbLeftCtrl),
    "kRIT5": _(Keys.kbCtrlRight, Keys.kbLeftCtrl),
    "kUP5": _(Keys.kbCtrlUp, Keys.kbLeftCtrl),
    "kDN5": _(Keys.kbCtrlDown, Keys.kbLeftCtrl),

    # Ctrl+Shift+key combinations (6 = Ctrl+Shift)
    "kDC6": _(Keys.kbCtrlDel, Keys.kbLeftCtrl | Keys.kbShift),
    "kEND6": _(Keys.kbCtrlEnd, Keys.kbLeftCtrl | Keys.kbShift),
    "kHOM6": _(Keys.kbCtrlHome, Keys.kbLeftCtrl | Keys.kbShift),
    "kIC6": _(Keys.kbCtrlIns, Keys.kbLeftCtrl | Keys.kbShift),
    "kLFT6": _(Keys.kbCtrlLeft, Keys.kbLeftCtrl | Keys.kbShift),
    "kNXT6": _(Keys.kbCtrlPgDn, Keys.kbLeftCtrl | Keys.kbShift),
    "kPRV6": _(Keys.kbCtrlPgUp, Keys.kbLeftCtrl | Keys.kbShift),
    "kRIT6": _(Keys.kbCtrlRight, Keys.kbLeftCtrl | Keys.kbShift),
    "kUP6": _(Keys.kbCtrlUp, Keys.kbLeftCtrl | Keys.kbShift),
    "kDN6": _(Keys.kbCtrlDown, Keys.kbLeftCtrl | Keys.kbShift),

    # Ctrl+Alt+key combinations (7 = Ctrl+Alt)
    "kDC7": _(Keys.kbAltDel, Keys.kbLeftCtrl | Keys.kbLeftAlt),
    "kEND7": _(Keys.kbAltEnd, Keys.kbLeftCtrl | Keys.kbLeftAlt),
    "kHOM7": _(Keys.kbAltHome, Keys.kbLeftCtrl | Keys.kbLeftAlt),
    "kIC7": _(Keys.kbAltIns, Keys.kbLeftCtrl | Keys.kbLeftAlt),
    "kLFT7": _(Keys.kbAltLeft, Keys.kbLeftCtrl | Keys.kbLeftAlt),
    "kNXT7": _(Keys.kbAltPgDn, Keys.kbLeftCtrl | Keys.kbLeftAlt),
    "kPRV7": _(Keys.kbAltPgUp, Keys.kbLeftCtrl | Keys.kbLeftAlt),
    "kRIT7": _(Keys.kbAltRight, Keys.kbLeftCtrl | Keys.kbLeftAlt),
    "kUP7": _(Keys.kbAltUp, Keys.kbLeftCtrl | Keys.kbLeftAlt),
    "kDN7": _(Keys.kbAltDown, Keys.kbLeftCtrl | Keys.kbLeftAlt),

    # Keypad keys
    "kpCMA": _('+', 0, b'+'),  # Keypad comma (sometimes +)
    "kpADD": _('+', 0, b'+'),  # Keypad +
    "kpSUB": _('-', 0, b'-'),  # Keypad -
    "kpMUL": _('*', 0, b'*'),  # Keypad *
    "kpDIV": _('/', 0, b'/'),  # Keypad /
    "kpZRO": _('0', 0, b'0'),  # Keypad 0
    "kpDOT": _('.', 0, b'.'),  # Keypad .

    # Additional keypad navigation
    "ka2": _(Keys.kbUp, 0),  # Keypad up arrow
    "kb1": _(Keys.kbLeft, 0),  # Keypad left arrow
    "kb3": _(Keys.kbRight, 0),  # Keypad right arrow
    "kc2": _(Keys.kbDown, 0),  # Keypad down arrow
}


class NcursesInputAdapter(InputAdapter):
    """
    NCurses-based input adapter
    """
    KEY_ESC = 0x1B
    READ_TIMEOUT_MS = 10

    def __init__(self, console_ctl: ConsoleCtl, display, input_state: InputState, mouse_enabled: bool = True):
        super().__init__(SysHandle(-1))

        self._console_ctl = console_ctl
        self._display = display
        self._input_state = input_state
        self._mouse_enabled = mouse_enabled
        self._stdscr = None
        self._input_getter = None
        self._initialize_ncurses_input()
        logger.info('NCursesInputAdapter initialized')

    def _initialize_ncurses_input(self):
        """
        Initialize ncurses input
        """
        try:
            # Get stdscr from display if available
            self._stdscr = self._display._stdscr
            # Capture all keyboard input
            curses.raw()
            # Disable echoing of pressed keys
            curses.noecho()
            # No need for ncurses to translate CR into LF
            curses.nonl()
            # Allow capturing function keys
            self._stdscr.keypad(True)
            # Make getch practically non-blocking with readTimeoutMs timeout
            self._stdscr.timeout(self.READ_TIMEOUT_MS)
            curses.set_escdelay(10)
            # NOTE: Do not call term_io.key_mods_on() for ncurses!
            # Ncurses handles all keyboard processing and the enhanced
            # keyboard protocols interfere with ncurses key translation
            # term_io.key_mods_on(self._console_ctl)
            # Enable mouse events if requested
            if self._mouse_enabled:
                term_io.mouse_on(self._console_ctl)

            self._input_getter = NcursesInputGetter(self._stdscr)

            # Register console restoration on exit
            atexit.register(self._restore_console)

        except Exception as e:
            logger.error("Failed to initialize ncurses input: %s", e)

    def _restore_console(self):
        """
        Restore console to normal state on exit
        """
        if self._stdscr:
            if self._mouse_enabled:
                term_io.mouse_off(self._console_ctl)
            # NOTE: Do not call term_io.key_mods_off() since we didn't call key_mods_on()
            term_io.consume_unprocessed_input(self._console_ctl, self._input_getter, self._input_state)

    def has_pending_events(self) -> bool:
        """
        Check if input events are pending
        """
        if not self._input_getter:
            return False
        return self._input_getter.has_pending()

    def get_nonblock(self) -> int:
        """
        Non-blocking character get
        """
        if not self._input_getter or not self._stdscr:
            return -1

        self._stdscr.timeout(0)
        k = self._input_getter.get()
        self._stdscr.timeout(self.READ_TIMEOUT_MS)
        return k

    def get_event(self, event) -> bool:
        """
        Get next input event
        """
        if not self._input_getter:
            return False

        buf = GetChBuf(self._input_getter)
        result = term_io.parse_event(buf, event, self._input_state)

        if result == ParseResult.Rejected:
            buf.reject()
        elif result == ParseResult.Accepted:
            return True
        elif result == ParseResult.Ignored:
            return False

        k = self._input_getter.get()

        if k == curses.KEY_RESIZE:
            return False
        if k == curses.KEY_MOUSE:
            mouse_result = self._parse_curses_mouse(event)
            return mouse_result

        if k != curses.ERR:
            return self._process_key_event(k, event)
        return False

    def _process_key_event(self, k: int, event) -> bool:
        """
        Process key event
        """
        keys = [k]
        num_keys = 1
        event.what = evKeyDown
        alt = False

        if keys[0] == self.KEY_ESC:
            alt = self._detect_alt(keys)

        if keys[0] < 32:
            event.keyDown = copy.copy(FROM_NON_PRINTABLE_ASCII[keys[0]])
        elif keys[0] == 127:
            # ^?, Delete  
            event.keyDown = KeyDownEvent.create(Keys.kbBackSpace, 0)
        elif curses.KEY_MIN < keys[0] < curses.KEY_MAX:
            if keys[0] in FROM_CURSES_KEY_CODE:
                event.keyDown = copy.copy(FROM_CURSES_KEY_CODE[keys[0]])
        elif curses.KEY_MAX < keys[0]:
            # Use keyname() to get string representation for high keys
            key_name = curses.keyname(keys[0])
            if key_name in FROM_CURSES_HIGH_KEY:
                event.keyDown = copy.copy(FROM_CURSES_HIGH_KEY[key_name])

        # If it hasn't been transformed by any of the previous tables,
        # and it's not a curses key, treat it like a printable character.
        if event.keyDown.keyCode == Keys.kbNoKey and keys[0] < curses.KEY_MIN:
            num_keys = self._parse_printable_char(event.keyDown, keys, num_keys)

        if alt:
            event.keyDown.controlKeyState |= Keys.kbLeftAlt
            term_io.normalize_key(event.keyDown)

        if self._input_state.bracketed_paste:
            event.keyDown.controlKeyState |= Keys.kbPaste

        # Only set event.what if we successfully processed the key
        is_valid = bool(event.keyDown.keyCode != Keys.kbNoKey or event.keyDown.textLength)
        return is_valid

    def _detect_alt(self, keys: list) -> bool:
        """
        Detect Alt key combinations
        """
        k = self.get_nonblock()
        if k != curses.ERR:
            keys[0] = k
            return True
        return False

    def _parse_printable_char(self, key_event: KeyDownEvent, keys: list, num_keys) -> int:
        """
        Parse printable character
        """
        # Convert character to UTF-8 bytes

        num_keys = self._read_utf8_char(keys, num_keys)

        key_event.text = bytearray(keys[:num_keys])
        key_event.textLength = num_keys

        try:
            text_str = key_event.text.decode('utf-8')
            key_event.charScan.charCode = CodepageTranslator().from_utf8(text_str)
        except UnicodeDecodeError:
            logger.error('Failed to decode UTF-8 text: %s', key_event.text)

        if key_event.keyCode <= Keys.kbCtrlZ:
            key_event.keyCode = Keys.kbNoKey
        return num_keys

    def _read_utf8_char(self, keys: list, num_keys: int) -> int:
        """
        Unicode characters are sent by the terminal byte by byte ...
        """
        num_keys += utf8_bytes_left(keys[0])

        for i in range(1, num_keys):
            keys[i] = self._input_getter.get()
            if keys[i] == curses.ERR:
                return i
        return num_keys

    def _parse_curses_mouse(self, event) -> bool:
        """
        Parse mouse event from ncurses
        """
        try:
            mouse_info = curses.getmouse()

            if mouse_info and len(mouse_info) >= 5:
                _, x, y, z, button_state = mouse_info

                event.what = evMouse
                mouse_event = MouseEvent()
                mouse_event.where.x = x
                mouse_event.where.y = y

                if button_state & curses.BUTTON1_PRESSED:
                    self._input_state.buttons |= mbLeftButton
                if button_state & curses.BUTTON1_RELEASED:
                    self._input_state.buttons &= ~mbLeftButton
                if button_state & curses.BUTTON2_PRESSED:
                    self._input_state.buttons |= mbMiddleButton
                if button_state & curses.BUTTON2_RELEASED:
                    self._input_state.buttons &= ~mbMiddleButton
                if button_state & curses.BUTTON3_PRESSED:
                    self._input_state.buttons |= mbRightButton
                if button_state & curses.BUTTON3_RELEASED:
                    self._input_state.buttons &= ~mbRightButton

                mouse_event.buttons = self._input_state.buttons

                # Mouse wheel support
                if hasattr(curses, 'BUTTON4_PRESSED') and (button_state & curses.BUTTON4_PRESSED):
                    mouse_event.wheel = mwUp
                elif hasattr(curses, 'BUTTON5_PRESSED') and (button_state & curses.BUTTON5_PRESSED):
                    mouse_event.wheel = mwDown

                event.mouse = mouse_event
                return True
        except curses.error as e:
            pass

        for parse_mouse in (
                term_io.parse_sgr_mouse,
                term_io.parse_x10_mouse,
        ):
            try:
                buf = GetChBuf(self._input_getter)
                result = parse_mouse(buf, event, self._input_state)
                if result == ParseResult.Rejected:
                    buf.reject()
                    continue
                if result == ParseResult.Ignored:
                    return False

                return True
            except Exception as e:
                logger.exception('Failed to parse mouse: %s', e)
        return False
