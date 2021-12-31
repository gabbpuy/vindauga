# -*- coding: utf-8 -*-
import logging
from threading import RLock
from typing import Any

from vindauga.constants.event_codes import evNothing
from vindauga.events.event import Event

logger = logging.getLogger(__name__)

__message_lock = RLock()


def message(receiver: Any, what: int, command: int, infoPtr: Any) -> Any:
    """
    Send an event directly to a component

    :param receiver: The component
    :param what: Event type (e.g. from `vindauga.constants.event_codes`)
    :param command: The command
    :param infoPtr: Additional data.
    :return: Event info pointer if any
    """
    if not receiver:
        return None

    event = Event(what)
    event.message.infoPtr = infoPtr
    event.message.command = command

    with __message_lock:
        # Need to think about this, as it could trigger redraws from a thread instead of the main thread, and that
        # might cause an issue with curses etc not being thread-safe. Events usually go onto a queue which is serviced
        # from the main thread.
        receiver.handleEvent(event)
        if event.what == evNothing:
            return event.message.infoPtr
        return None
