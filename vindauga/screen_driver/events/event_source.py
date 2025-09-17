# -*- coding: utf-8 -*-
from typing import TYPE_CHECKING
from .sys_manual_event import SysHandle


if TYPE_CHECKING:
    from vindauga.events.event import Event


class EventSource:
    def __init__(self, handle: SysHandle):
        self.handle = handle

    def has_pending_events(self) -> bool:
        return False

    def get_event(self, event: 'Event'):
        return False
