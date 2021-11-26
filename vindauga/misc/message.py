# -*- coding: utf-8 -*-
import logging

from vindauga.constants.event_codes import evNothing
from vindauga.events.event import Event

logger = logging.getLogger(__name__)


def message(receiver, what, command, infoPtr):
    if not receiver:
        return None

    event = Event(what)
    event.message.infoPtr = infoPtr
    event.message.command = command

    receiver.handleEvent(event)
    if event.what == evNothing:
        return event.message.infoPtr
    return None
