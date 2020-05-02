# -*- coding: utf-8 -*-
import logging
from threading import Timer as _Timer

logger = logging.getLogger('vindauga.types.timer')


class Timer:
    """
    Basic timers to handle things like waiting for Escape keys
    """
    def __init__(self):
        self._timer: _Timer = None
        self._running: bool = False
        self._expired: bool = True

    def start(self, timeout) -> None:
        if self._timer:
            self._timer.cancel()
        self._timer = _Timer(timeout, self.expire)
        self._timer.start()
        self._running = True
        self._expired = False
        return timeout

    def stop(self) -> None:
        if self._timer:
            self._timer.cancel()
            self._timer = None
        self._running = False
        self._expired = True

    def expire(self):
        self._expired = True

    def isRunning(self) -> bool:
        return self._running

    def isExpired(self) -> bool:
        return self._expired
