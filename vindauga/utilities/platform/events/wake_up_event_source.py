# -*- coding: utf-8 -*-
import logging
from threading import Event
from typing import TYPE_CHECKING
from vindauga.constants.event_codes import evNothing


from .event_source import EventSource
from .sys_manual_event import SysManualEvent, Handle

if TYPE_CHECKING:
    from vindauga.events.event import Event as VindaugaEvent

logger = logging.getLogger(__name__)


class WakeUpEventSource(EventSource):
    def __init__(self, handle: Handle, callback, callback_args):
        self.callback = callback
        self.callback_args = callback_args or tuple()
        self.sys = SysManualEvent(handle)
        self.signaled: Event = Event()
        self.signaled.clear()
        super().__init__(SysManualEvent.get_waitable_handle(handle))

    def signal(self):
        try:
            if not self.signaled.is_set():
                self.sys.signal()
                self.signaled.set()
        except Exception as e:
            logger.exception('signal failed:')

    def clear(self):
        if self.signaled.is_set():
            self.sys.clear()
            self.signaled.clear()
            return True
        return False

    def get_event(self, event: 'VindaugaEvent') -> bool:
        if self.signaled.is_set():
            try:
                if self.callback:
                    return self.callback(event, *self.callback_args)
                event.what = evNothing
                return True
            finally:
                self.clear()
        return False
