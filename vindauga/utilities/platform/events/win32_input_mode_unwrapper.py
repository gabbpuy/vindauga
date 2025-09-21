# -*- coding: utf-8 -*-
from vindauga.constants.event_codes import evNothing
from vindauga.events.event import Event
from vindauga.utilities.platform.adapters.windows_console.utilities import KEY_EVENT_RECORD, get_win32_key

from .get_ch_buf import GetChBuf
from .input_getter import InputGetter
from .input_state import InputState
from .csi_data import CSIData
from .parse_result import ParseResult


def parse_win32_input_mode_key(csi: CSIData, event: Event, input_state: InputState) -> ParseResult:
    from .termio import term_io
    k_event = KEY_EVENT_RECORD()
    k_event.wVirtualKeyCode = csi.get_value(0, 0)
    k_event.wVirtualScanCode = csi.get_value(1, 0)
    k_event.uCharCode = csi.get_value(2, 0)
    k_event.bKeyDown = csi.get_value(3, 0)
    k_event.dwControlKeyState = csi.get_value(4, 0)
    k_event.wRepeatCount = csi.get_value(5, 1)

    if k_event.bKeyDown and get_win32_key(k_event, event, input_state):
        term_io.normalize_key(event.keyDown)
        return ParseResult.Accepted
    return ParseResult.Ignored


class Win32InputModeUnwrapper(InputGetter):
    def __init__(self, input_getter: InputGetter, input_state: InputState):
        super().__init__()
        self.input_getter = input_getter
        self.input_state = input_state
        self.unget_size = 0
        self.unget_buffer = []

    def get(self):

        if self.unget_size > 0:
            self.unget_size -= 1
            return self.unget_buffer.pop()
        buf = GetChBuf(self.input_getter)
        csi = CSIData()
        event = Event(evNothing)
        if (buf.get() == 0x1B and buf.get() == ord('[')
            and csi.read_from(buf) and csi.terminator == ord('_')
            and parse_win32_input_mode_key(csi, event, self.input_state) == ParseResult.Accepted
            and event.keyDown.charScan.scanCode == 0
            and event.keyDown.textLength == 1):
            return event.keyDown.text[0]
        buf.reject()
        return -1

    def unget(self, key: int):
        self.unget_buffer.append(key)
        self.unget_size += 1
