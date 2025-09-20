# -*- coding: utf-8 -*-
from collections import deque
import logging
import time
from typing import TYPE_CHECKING

from vindauga.constants.event_codes import evMouse, evNothing, evKeyboard
from vindauga.constants.keys import kbIns, kbInsState
from vindauga.events.mouse_event import MouseEvent

from .platform import Platform
from .screen_cell.screen_cell import ScreenCell

if TYPE_CHECKING:
    from vindauga.events.event import Event

logger = logging.getLogger(__name__)


class HardwareInfo:
    eventQ_Size = 24

    def __init__(self):
        self.__insertState: bool = False
        self.__platform: Platform = Platform()
        self.__consoleHandle = []
        self.__consoleMode: int = 0
        self.__pendingEvent: int = 0
        self.__irBuffer = None
        self.__crInfo = None
        self.__sbInfo = None
        self.__eventQ: deque = deque()
        self.pendingEvent: int = 0
        self.alwaysFlush = False

    def setCaretSize(self, size: int):
        self.__platform.set_caret_size(size)

    def setCaretPosition(self, x: int, y: int):
        self.__platform.set_caret_position(x, y)

    def getCaretSize(self):
        return self.__platform.get_caret_size()

    def isCaretVisible(self):
        return self.__platform.is_caret_visible()

    def getScreenRows(self):
        return self.__platform.get_screen_rows()

    def getScreenCols(self):
        return self.__platform.get_screen_cols()

    def getScreenMode(self):
        return self.__platform.get_screen_mode()

    def setScreenMode(self, mode: int):
        pass

    def clearScreen(self, w: int, h: int):
        self.__platform.clear_screen()

    def screenWrite(self, x: int, y: int, buf: list[ScreenCell], length: int):
        self.__platform.screen_write(x, y, buf, length)
        if self.alwaysFlush:
            self.flushScreen()

    def allocateScreenBuffer(self) -> list[ScreenCell]:
        return self.__platform.reload_screen_info()

    def freeScreenBuffer(self, _buffer: list[ScreenCell]):
        self.__platform.free_screen_buffer()

    def getButtonCount(self) -> int:
        return 2

    def cursorOn(self):
        pass

    def cursorOff(self):
        pass

    def flushScreen(self):
        self.__platform.flush_screen()

    def setupConsole(self):
        self.__platform.setup_console()

    def restoreConsole(self):
        self.__platform.restore_console()

    def __getPendingEvent(self, event: 'Event', mouse: bool) -> bool:
        # Look for the first event matching the mouse criteria
        if any((evt := ev) and bool(ev.what & evMouse) == mouse for ev in self.__eventQ):
            event.setFrom(evt)
            self.__eventQ.remove(evt)
            return True
        return False

    def __new_event(self):
        from vindauga.events.event import Event
        return Event(evNothing)

    def getMouseEvent(self) -> MouseEvent | None:
        event = self.__new_event()
        if self.__getPendingEvent(event, True):
            return event.mouse
        return None

    def getKeyEvent(self, event: 'Event') -> bool:
        self.__readEvents()
        if self.__getPendingEvent(event, False):
            if event.what & evKeyboard:
                if event.keyDown.keyCode == kbIns:
                    self.__insertState = not self.__insertState
                if self.__insertState:
                    event.keyDown.controlKeyState |= kbInsState
            return event.what != evNothing
        return False

    def __readEvents(self):
        """
        Read events from platform and add them to the queue.
        """
        if not self.__eventQ:
            while len(self.__eventQ) < self.eventQ_Size:
                event = self.__new_event()
                if self.__platform.get_event(event):
                    self.__eventQ.append(event)
                else:
                    break

    def waitForEvents(self, timeoutMs: int):
        if not self.__eventQ:
            self.flushScreen()
            self.__platform.wait_for_events(timeoutMs)

    def interruptEventWait(self):
        self.__platform.interrupt_event_wait()

    def setClipboardText(self, text: str):
        self.__platform.set_clipboard_text(text)

    def requestClipboardText(self):
        self.__platform.request_clipboard_text()
        
    def getTickCount(self) -> float:
        """
        Get tick count for timing
        """
        return time.time()

    def clearPendingEvent(self):
        self.pendingEvent = None

    def resize(self, width: int, height: int):
        self.__platform.resize(width, height)


# Create singleton instance
hardware_info = HardwareInfo()
