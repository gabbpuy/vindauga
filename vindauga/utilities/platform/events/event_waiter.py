# -*- coding: utf-8 -*-
from __future__ import annotations

from functools import singledispatchmethod
import logging
import math
import time
from typing import TYPE_CHECKING

from vindauga.constants.event_codes import evNothing
from .event_source import EventSource
from .poll_data import PollData
from .poll_handles import poll_handles
from .poll_state import PollState
from .sys_manual_event import SysManualEvent
from .wake_up_event_source import WakeUpEventSource

if TYPE_CHECKING:
    from vindauga.events.event import Event

logger = logging.getLogger(__name__)


class EventWaiter:
    def __init__(self):
        self.__sources: list[EventSource] = []
        self.__poll_data = PollData()
        self.__wakeup: WakeUpEventSource = None
        self.__ready_event = None
        self.__ready_event_present: bool = False
        self.__wakeup = None
        if handle := SysManualEvent.create_handle():
            self.__wakeup = WakeUpEventSource(handle, None, None)
            self.add_source(self.__wakeup)

    def __remove_source(self, size: int):
        self.__sources = self.__sources[size:]
        self.__poll_data.erase(size)

    def __poll_sources(self, timeout_ms: int):
        for i in range(len(self.__poll_data)):
            source = self.__sources[i]
            has_pending = source.has_pending_events()
            self.__poll_data.states[i] = (
                PollState.Ready if has_pending else PollState.Nothing
            )
            if self.__poll_data.states[i] != PollState.Nothing:
                break
        
        # Always poll handles to check for fresh input, even if no pending events
        poll_handles(self.__poll_data, timeout_ms)
        
        # Clean up disconnected sources
        i = 0
        while i < len(self.__poll_data):
            if self.__poll_data.states[i] == PollState.Disconnect:
                self.__remove_source(i)
            else:
                i += 1

    @staticmethod
    def __new_event() -> 'Event':
        from vindauga.events.event import Event
        return Event(evNothing)

    def __has_ready_event(self) -> bool:
        if not self.__ready_event_present:
            # First check sources marked as Ready
            for i in range(len(self.__poll_data)):
                if self.__poll_data.states[i] == PollState.Ready:
                    self.__poll_data.states[i] = PollState.Nothing
                    self.__ready_event = self.__new_event()
                    if self.__sources[i].get_event(self.__ready_event):
                        self.__ready_event_present = True
                        break

            # If no ready events found, try all input sources that might have immediate input available
            # This is needed for input adapters that don't buffer input until it's read
            if not self.__ready_event_present:
                for i in range(len(self.__poll_data)):
                    source = self.__sources[i]
                    # Try all input sources with Nothing state - they might have immediate input
                    if self.__poll_data.states[i] == PollState.Nothing:
                        self.__ready_event = self.__new_event()
                        if source.get_event(self.__ready_event):
                            self.__ready_event_present = True
                            break
        return self.__ready_event_present

    def __get_ready_event(self, event: Event):
        event.setFrom(self.__ready_event)
        self.__ready_event_present = False

    def add_source(self, source: EventSource):
        self.__sources.append(source)
        self.__poll_data.append(source.handle)

    @singledispatchmethod
    def remove_source(self):
        pass

    @remove_source.register
    def _(self, source: EventSource):
        if source in self.__sources:
            self.__sources.remove(source)
            # Also remove the handle from poll_data if it exists
            if hasattr(source, 'handle') and source.handle in self.__poll_data.handles:
                try:
                    index = self.__poll_data.handles.index(source.handle)
                    self.__poll_data.handles.pop(index)
                    self.__poll_data.states.pop(index)
                except (ValueError, IndexError, AttributeError):
                    pass

    @remove_source.register
    def _(self, source: WakeUpEventSource):
        if source in self.__sources:
            self.__sources.remove(source)

    @remove_source.register
    def _(self, source: int):
        try:
            self.__poll_data.erase(source)
            self.__sources = self.__sources[source:]
        except (IndexError, AttributeError):
            pass

    @staticmethod
    def poll_delay_ms(now: float, end: float) -> int:
        diff_seconds = end - now
        if diff_seconds <= 0:
            return 0
        return math.ceil(diff_seconds * 1000)

    def wait_for_events(self, timeout_ms: int = -1):
        now = time.monotonic()
        end = now + timeout_ms / 1000 if timeout_ms >= 0 else float('inf')
        while not self.__has_ready_event() and now <= end:
            self.__poll_sources(-1 if timeout_ms < 0 else self.poll_delay_ms(now, end))
            now = time.monotonic()

    def interrupt_event_wait(self):
        if self.__wakeup:
            self.__wakeup.signal()

    def get_event(self, event: Event):
        if self.__has_ready_event():
            self.__get_ready_event(event)
            return True
        
        # Poll sources with no timeout to check for immediate input
        self.__poll_sources(0)
        if self.__has_ready_event():
            self.__get_ready_event(event)
            return True
        
        return False
