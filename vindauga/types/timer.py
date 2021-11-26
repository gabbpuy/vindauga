# -*- coding: utf-8 -*-
import logging
from threading import Timer as _Timer, RLock

logger = logging.getLogger(__name__)


class Timer:
    """
    Basic timers to handle things like waiting for Escape keys
    """
    def __init__(self):
        self.__lock = RLock()
        self._timer: _Timer = None
        self._running: bool = False
        self._expired: bool = True

    def start(self, timeout) -> None:
        self.stop()
        with self.__lock:
            self._timer = _Timer(timeout, self.expire)
            self._running = True
            self._expired = False
            self._timer.start()
        return timeout

    def stop(self) -> None:
        with self.__lock:
            if self._timer:
                self._timer.cancel()
                self._timer = None
            self._running = False
            self._expired = True

    def expire(self):
        with self.__lock:
            self._expired = True
            self._timer = None

    def isRunning(self) -> bool:
        with self.__lock:
            return self._running

    def isExpired(self) -> bool:
        with self.__lock:
            return self._running and self._expired
