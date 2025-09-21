# -*- coding: utf-8 -*-
from dataclasses import dataclass, field

from .poll_state import PollState
from .sys_manual_event import SysHandle


@dataclass()
class PollData:
    handles: list[SysHandle] = field(default_factory=list)
    states: list[PollState] = field(default_factory=list)

    def append(self, handle: SysHandle):
        self.handles.append(handle)
        self.states.append(PollState.Nothing)

    def erase(self, size: int):
        self.handles = self.handles[size:]
        self.states = self.states[size:]

    def __len__(self):
        return len(self.handles)
