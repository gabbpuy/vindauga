# -*- coding: utf-8 -*-
from __future__ import annotations
import logging

from vindauga.events.mouse_event import MouseEvent
import vindauga.constants.event_codes as event_codes
from vindauga.constants.keys import kbPaste, kbEnter, kbTab
from vindauga.mouse.mouse import Mouse
from vindauga.utilities.platform.system_interface import systemInterface
from vindauga.utilities.text.text import Text
from vindauga.types.screen import Screen

logger = logging.getLogger(__name__)


class EventQueue:
    """
    EventQueue
    """
    def __init__(self):
        self.mouseEvents = True  # Assume mouse is available
        self.pendingMouseUp = False
        self.lastMouse = MouseEvent()
        self.curMouse = MouseEvent()
        self.downMouse = MouseEvent()
        self.downTicks = 0
        self.mouseReverse = False
        self.doubleDelay = 8  # Double-click timing delay
        self.repeatDelay = 8
        self.autoTicks = 0
        self.autoDelay = 0

        # Key event handling
        self.minPasteEventCount = 4  # Minimum consecutive text events to detect paste
        self.keyEventQueue = []  # Queue for batched key events
        self.keyEventCount = 0
        self.keyEventIndex = 0
        self.pasteState = False
        self.pasteText = None
        self.pasteTextLength = 0
        self.pasteTextIndex = 0
        self._shouldSkipLf: bool = False

        self.resume()

    def getMouseEvent(self, event) -> None:
        """
        Get mouse event
        """
        if self.mouseEvents:
            if self.pendingMouseUp:
                event.what = event_codes.evMouseUp
                event.mouse.copy(self.lastMouse)
                self.lastMouse.buttons = 0
                self.pendingMouseUp = False
                return

            if not self.getMouseState(event):
                return

            event.mouse.eventFlags = 0

            if event.mouse.buttons == 0 and self.lastMouse.buttons != 0:
                if event.mouse.where == self.lastMouse.where:
                    event.what = event_codes.evMouseUp
                    buttons = self.lastMouse.buttons
                    # Make a copy to avoid shared object issues
                    self.lastMouse.copy(event.mouse)
                    event.mouse.buttons = buttons
                else:
                    event.what = event_codes.evMouseMove
                    up = event.mouse
                    where = up.where
                    event.mouse = self.lastMouse
                    event.mouse.where = where
                    event.mouse.eventFlags |= event_codes.meMouseMoved
                    up.buttons = self.lastMouse.buttons
                    self.lastMouse = up
                    self.pendingMouseUp = True
                return

            if event.mouse.buttons != 0 and self.lastMouse.buttons == 0:
                if (event.mouse.buttons == self.downMouse.buttons and
                        event.mouse.where == self.downMouse.where and
                        event.what - self.downTicks <= self.doubleDelay):
                    if not (self.downMouse.eventFlags & (event_codes.meDoubleClick | event_codes.meTripleClick)):
                        event.mouse.eventFlags |= event_codes.meDoubleClick
                    elif self.downMouse.eventFlags & event_codes.meDoubleClick:
                        event.mouse.eventFlags &= ~event_codes.meDoubleClick
                        event.mouse.eventFlags |= event_codes.meTripleClick

                self.downMouse.copy(event.mouse)
                self.autoTicks = self.downTicks = event.what
                self.autoDelay = self.repeatDelay
                event.what = event_codes.evMouseDown
                self.lastMouse.copy(event.mouse)
                return

            event.mouse.buttons = self.lastMouse.buttons

            if event.mouse.wheel != 0:
                event.what = event_codes.evMouseWheel
                self.lastMouse.copy(event.mouse)
                return

            if event.mouse.where != self.lastMouse.where:
                event.what = event_codes.evMouseMove
                event.mouse.eventFlags |= event_codes.meMouseMoved
                self.lastMouse.copy(event.mouse)
                return

            if event.mouse.buttons != 0 and event.what - self.autoTicks > self.autoDelay:
                self.autoTicks = event.what
                self.autoDelay = 1
                event.what = event_codes.evMouseAuto
                self.lastMouse.copy(event.mouse)
                return

        event.what = event_codes.evNothing

    def getMouseState(self, event) -> bool:
        """
        Get mouse state
        """
        event.what = event_codes.evNothing
        mouse_event = systemInterface.getMouseEvent()
        if not mouse_event:
            return False

        self.curMouse.copy(mouse_event)

        if self.mouseReverse and self.curMouse.buttons != 0 and self.curMouse.buttons != 3:
            self.curMouse.buttons ^= 3

        event.what = systemInterface.getTickCount()
        event.mouse.copy(self.curMouse)
        return True

    def getKeyEvent(self, event) -> None:
        """
        Get keyboard event with paste handling and line ending conversion.
        """
        self.getKeyOrPasteEvent(event)

        if self._shouldSkipLf:
            self._shouldSkipLf = False
            # Skip a LF, since we had previously read a CR
            if (event.what == event_codes.evKeyDown and
                    (event.keyDown.controlKeyState & kbPaste) != 0 and
                    ((event.keyDown.textLength == 0 and event.keyDown.charScan.charCode == '\n') or
                     (event.keyDown.textLength == 1 and event.keyDown.text and event.keyDown.text[0] == '\n'))):
                self.getKeyOrPasteEvent(event)

        if event.what == event_codes.evKeyDown and (event.keyDown.controlKeyState & kbPaste) != 0:
            if event.keyDown.textLength == 0:
                event.keyDown.text[0] = chr(event.keyDown.charScan.charCode)
                event.keyDown.textLength = 1
            # Convert CR and CRLF into LF
            if event.keyDown.textLength and event.keyDown.text[0] == '\r':
                event.keyDown.text = '\n'
                self._shouldSkipLf = True
            event.keyDown.keyCode = 0

    def waitForEvents(self, timeoutMs: int) -> None:
        """
        Wait for events with timeout.
        """
        # Only wait if no paste text and no queued key events
        if self.pasteText is None and self.keyEventCount == 0:
            systemInterface.waitForEvents(timeoutMs)

    def suspend(self) -> None:
        """
        Suspend event processing.
        """
        Mouse.suspend()

    def resume(self) -> None:
        """
        Resume event processing.
        """
        if not Mouse.present():
            Mouse.resume()
        if not Mouse.present():
            return
        mouse = Mouse.getEvent(self.curMouse)
        if mouse:
            self.lastMouse.copy(mouse)
        self.mouseEvents = True
        if Screen.screen:
            Mouse.setRange(Screen.screen.screenWidth - 1, Screen.screen.screenHeight - 1)

    def wakeUp(self) -> None:
        """
        Wake up event loop (thread-safe).
        """
        systemInterface.interruptEventWait()

    def readKeyPress(self, event) -> bool:
        """
        Read a single key press from hardware
        """
        if not systemInterface.getKeyEvent(event):
            event.what = event_codes.evNothing
        return event.what != event_codes.evNothing

    def isTextEvent(self, event) -> bool:
        """
        Check if event is a text event (for paste detection).
        """
        return (event.what == event_codes.evKeyDown and
                (event.keyDown.textLength != 0 or
                 event.keyDown.keyCode == kbEnter or
                 event.keyDown.keyCode == kbTab))

    def getPasteEvent(self, event) -> bool:
        """
        Get next event from paste text buffer.
        """
        if self.pasteText and self.pasteTextIndex < self.pasteTextLength:
            # Get remaining text from current index
            remaining_text = self.pasteText[self.pasteTextIndex:]
            if remaining_text:
                # Use Text.next() to properly handle unicode characters
                success, next_index = Text.next(remaining_text, 0)
                if success:
                    # Extract the character sequence
                    char_sequence = remaining_text[:next_index]
                    event.what = event_codes.evKeyDown
                    event.keyDown.keyCode = 0
                    event.keyDown.controlKeyState = kbPaste
                    event.keyDown.text = char_sequence
                    event.keyDown.textLength = len(char_sequence)
                    self.pasteTextIndex += next_index
                    return True

            # End of paste text
            self.pasteText = None
            self.pasteTextLength = 0
            self.pasteTextIndex = 0
        return False

    def setPasteText(self, text: str) -> None:
        """
        Set text for paste operations.
        """
        self.pasteText = text
        self.pasteTextLength = len(text)
        self.pasteTextIndex = 0

    def __createEvent(self):
        from vindauga.events.event import Event
        return Event(event_codes.evNothing)

    def getKeyOrPasteEvent(self, event) -> None:
        """
        Get key event or paste event
        """
        if self.getPasteEvent(event):
            return

        if self.keyEventCount == 0:
            # Read multiple events to detect paste sequences
            self.keyEventQueue = []
            firstNonText = self.minPasteEventCount

            for i in range(self.minPasteEventCount):
                keyEvent = self.__createEvent()
                if not self.readKeyPress(keyEvent):
                    break
                self.keyEventQueue.append(keyEvent)
                self.keyEventCount += 1
                if not self.isTextEvent(keyEvent):
                    firstNonText = i
                    break

            # If we receive consecutive text events, this might be a paste
            if (self.keyEventCount == self.minPasteEventCount and
                    firstNonText == self.minPasteEventCount):
                self.pasteState = True

            if self.pasteState:
                # Mark events as paste events
                for i in range(min(self.keyEventCount, firstNonText)):
                    self.keyEventQueue[i].keyDown.controlKeyState |= kbPaste

            if (self.keyEventCount < self.minPasteEventCount or
                    firstNonText < self.minPasteEventCount):
                self.pasteState = False

            self.keyEventIndex = 0

        if self.keyEventCount != 0:
            event.setFrom(self.keyEventQueue[self.keyEventIndex])
            self.keyEventIndex += 1
            self.keyEventCount -= 1
        else:
            event.what = event_codes.evNothing


# Create singleton instance
event_queue = EventQueue()
