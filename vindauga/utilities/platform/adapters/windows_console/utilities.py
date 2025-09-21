# -*- coding: utf-8 -*-
import ctypes
import sys

from vindauga.constants.event_codes import evKeyDown
from vindauga.constants.keys import kbShift, kbCtrlShift, kbAltShift, kbScrollState, kbNumState, kbCapsState, \
    kbEnhanced, kbCtrlZ, kbNoKey, kbLeft, kbLeftCtrl, kbRightAlt
from vindauga.events.event import Event
from vindauga.utilities.platform.codepage.codepage_translator import CodepageTranslator
from vindauga.utilities.platform.events.input_state import InputState

from .scan_code_tables import ALT_CVT, NORMAL_CVT, CTRL_CVT, SHIFT_CVT

VK_MENU = 0x12


class KEY_EVENT_RECORD(ctypes.Structure):
    _fields_ = [
        ('bKeyDown', ctypes.c_bool),
        ('wRepeatCount', ctypes.c_short),
        ('wVirtualKeyCode', ctypes.c_short),
        ('wVirtualScanCode', ctypes.c_short),
        ('uChar', ctypes.c_wchar),
        ('dwControlKeyState', ctypes.c_long)
    ]


def get_win32_key_text(key_event: KEY_EVENT_RECORD, event: Event, input_state: InputState) -> bool:
    ch = key_event.uChar
    event.keyDown.textLength = 0

    if 0x20 <= ord(ch) and ord(ch) != 0x7f:
        if sys.platform == 'win32':
            import pywin32.kernel32 as kernel32

            if 0xD800 <= ch <= 0xD8FF:
                input_state.surrogate = ch
                return False

            utf16 = [ch, 0]
            if input_state.surrogate:
                if 0xd800 <= ch <= 0xdFFF:
                    utf16[1] = ch
                    utf16[0] = input_state.surrogate
                input_state.surrogate = 0

            event.keyDown.textLength = kernel32.wide_char_to_multi_byte(
                kernel32.CP_UTF8, 0, utf16, 2 if utf16[1] else 1,
                event.keyDown.text, len(event.keyDown.text),
                None, None
            )
        else:
            if ch < 0xD800 or (0xDFFF < ch < 0x10FFFF):
                bytes_32 = ch.decode('utf-32')
                bytes_8 = bytes_32.encode('utf-8')
                event.keyDown.textLength = len(bytes_8)
    return True


def get_win32_key(key_event: KEY_EVENT_RECORD, event: Event, input_state: InputState) -> bool:
    if not get_win32_key_text(key_event, event, input_state):
        return False

    event.what = evKeyDown
    event.keyDown.charScan.scanCode = key_event.wVirtualScanCode
    event.keyDown.charScan.charCode = chr(ord(key_event.uChar) & 0x7F)
    event.keyDown.controlKeyState = (
            key_event.dwControlKeyState & (
        kbShift | kbCtrlShift | kbAltShift | kbScrollState | kbNumState | kbCapsState | kbEnhanced
    ))

    if event.keyDown.textLength:
        event.keyDown.charScan.charCode = CodepageTranslator().from_utf8(event.keyDown.getText())
        if key_event.wVirtualKeyCode == VK_MENU:
            event.keyDown.charScan.scanCode = 0
        if event.keyDown.charScan.charCode == 0 or event.keyDown.keyCode <= kbCtrlZ:
            event.keyDown.keyCode = kbNoKey

    if event.keyDown.keyCode in (0x2a00, 0x1d00, 0x3600, 0x3800, 0x3a00, 0x5b00, 0x5c00):
        # Throw away standalone meta keys
        event.keyDown.keyCode = kbNoKey
    elif (event.keyDown.controlKeyState & kbLeftCtrl and
          event.keyDown.controlKeyState & kbRightAlt and
          event.keyDown.textLength == 0):
        # Throw away Ctrl+Alt with no key because that's probably AltGr
        event.keyDown.keyCode = kbNoKey
    elif (event.keyDown.controlKeyState & kbCtrlShift and
          event.keyDown.controlKeyState & kbAltShift and
          event.keyDown.textLength != 0):
        # there's some text so AltGr - remove Ctrl + Alt modifiers
        event.keyDown.controlKeyState &= ~(kbCtrlShift | kbAltShift)
    elif key_event.wVirtualScanCode < 89:
        index = key_event.wVirtualScanCode
        key_code = 0
        if event.keyDown.controlKeyState & kbAltShift and ALT_CVT[index]:
            key_code = ALT_CVT[index]
        elif event.keyDown.controlKeyState & kbCtrlShift and CTRL_CVT[index]:
            key_code = CTRL_CVT[index]
        elif event.keyDown.controlKeyState & kbShift and SHIFT_CVT[index]:
            key_code = SHIFT_CVT[index]
        elif not (event.keyDown.controlKeyState & (kbShift | kbCtrlShift | kbAltShift)) and NORMAL_CVT.get(index):
            key_code = NORMAL_CVT[index]

        if key_code != 0:
            event.keyDown.keyCode = key_code
            if event.keyDown.charScan.charCode < ' ':
                event.keyDown.textLength = 0
            elif event.keyDown.charScan.charCode < 0x7F and not event.keyDown.textLength:
                event.keyDown.textLength = 1
                event.keyDown.text[0] = event.keyDown.charScan.charCode

    return bool(event.keyDown.keyCode != kbNoKey or event.keyDown.textLength)
