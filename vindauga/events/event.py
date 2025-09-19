# -*- coding: utf-8 -*-
from __future__ import annotations
from copy import copy

from vindauga.constants.event_codes import evNothing

from .event_queue import event_queue
from .key_down_event import KeyDownEvent
from .message_event import MessageEvent
from .mouse_event import MouseEvent


class Event:
    def __init__(self, what):
        self.what = what
        self.mouse: MouseEvent = MouseEvent()
        self.keyDown: KeyDownEvent = KeyDownEvent()
        self.message: MessageEvent = MessageEvent()

    def setFrom(self, event: Event):
        self.clear(None)
        self.what = event.what
        self.mouse = copy(event.mouse)
        self.keyDown = copy(event.keyDown)
        self.message = copy(event.message)

    def clear(self, who):
        self.what = evNothing
        self.mouse: MouseEvent = MouseEvent()
        self.keyDown: KeyDownEvent = KeyDownEvent()
        self.message: MessageEvent = MessageEvent()
        self.message.infoPtr = who

    def getMouseEvent(self):
        """
        Get mouse event
        """
        event_queue.getMouseEvent(self)
    
    def getKeyEvent(self):
        """
        Get keyboard event
        """
        event_queue.getKeyEvent(self)

    def __repr__(self):
        return f'<Event: What:{self.what:X} Mo:{self.mouse} Ke:{self.keyDown} Me:{self.message}>'
