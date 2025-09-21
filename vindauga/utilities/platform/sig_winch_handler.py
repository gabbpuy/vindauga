# -*- coding: utf-8 -*-
from __future__ import annotations
import logging
import signal

from vindauga.constants.command_codes import cmScreenChanged
from vindauga.constants.event_codes import evCommand
from vindauga.events.event import Event
from vindauga.utilities.platform.events.sys_manual_event import Handle, SysManualEvent
from vindauga.utilities.platform.events.wake_up_event_source import WakeUpEventSource

logger = logging.getLogger(__name__)


class SigWinchHandler(WakeUpEventSource):

    instance: SigWinchHandler = None

    def __init__(self, handle: Handle, oldSignals):
        super().__init__(handle, self.emitScreenChangedEvent, None)
        self.oldSignals = oldSignals
        SigWinchHandler.instance = self

    @staticmethod
    def handleSignal(signalNumber: int, _frame=None) -> None:
        if instance := SigWinchHandler.instance:
            instance.signal()

    @staticmethod
    def emitScreenChangedEvent(event: Event, *_args) -> bool:
        event.what = evCommand
        event.message.command = cmScreenChanged
        return True

    @staticmethod
    def create() -> SigWinchHandler | None:
        if not SigWinchHandler.instance:
            old_handler = signal.signal(signal.SIGWINCH, SigWinchHandler.handleSignal)
            try:
                if handle := SysManualEvent.create_handle():
                    return SigWinchHandler(handle, old_handler)
            except OSError:
                pass
            signal.signal(signal.SIGWINCH, old_handler)
        return None

    def __del__(self) -> None:
        signal.signal(signal.SIGWINCH, self.oldSignals)
        SigWinchHandler.instance = None
