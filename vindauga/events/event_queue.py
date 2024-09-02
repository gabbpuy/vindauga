# -*- coding: utf-8 -*-
from dataclasses import dataclass
from vindauga.events.mouse_event import MouseEvent


@dataclass
class EventQueue:
    doubleDelay: int = 8
    mouseReverse: bool = False
    mouse: MouseEvent = MouseEvent()
