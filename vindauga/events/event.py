# -*- coding: utf-8 -*-
from copy import copy

from vindauga.constants.event_codes import evNothing

from .key_down_event import KeyDownEvent
from .message_event import MessageEvent
from .mouse_event import MouseEvent


class Event:
    def __init__(self, what):
        self.what = what
        self.mouse: MouseEvent = MouseEvent()
        self.keyDown: KeyDownEvent = KeyDownEvent()
        self.message: MessageEvent = MessageEvent()

    def setFrom(self, event):
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

    def __repr__(self):
        return '<Event: What:{:X} Mo:{} Ke:{} Me:{}>'.format(self.what, self.mouse, self.keyDown, self.message)
