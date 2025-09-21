# -*- coding: utf-8 -*-
from __future__ import annotations

import time

from typing import Callable

from dataclasses import dataclass

from vindauga.utilities.platform.system_interface import systemInterface


def systemTimeMs():
    return systemInterface.getTickCount() * 55000


@dataclass
class Timer:
    expiresAt: int = 0
    period: int = 0
    collectId = []


class TimerQueue:
    def __init__(self, getTimeMs: Callable | None = None):
        if getTimeMs is None:
            self.getTimeMs = systemTimeMs
        else:
            self.getTimeMs = getTimeMs
        self.timers = []

    def __del__(self):
        for timer in self.timers:
            del timer
        self.timers = []

    def setTimer(self, timeoutMs: int, periodMs: int) -> Timer:
        timer = Timer()
        timer.expiresAt = self.getTimeMs() + timeoutMs
        timer.period = periodMs
        self.timers.append(timer)
        return timer

    def killTimer(self, timer: Timer) -> None:
        if timer in self.timers:
            self.timers.remove(timer)

    @staticmethod
    def calcNextExpiresAt(expiresAt, now, period) -> int:
        return (1 + (now - expiresAt + period) / period) * period + expiresAt - period

    def collectExpiredTimers(self, callback: Callable, *callbackArgs):
        collectId = time.time_ns()
        now = time.time()

        removals = []
        for timer in self.timers:
            if timer.collectId or now < timer.expiresAt:
                continue
            if timer.period >= 0:
                timer.collectId = collectId
                if timer.period > 0:
                    timer.expiresAt = TimerQueue.calcNextExpiresAt(timer.expiresAt, now, timer.period)
            else:
                removals.append(timer)
            callback(timer, *callbackArgs)

        for timer in removals:
            self.timers.remove(timer)
            del timer

        for timer in self.timers:
            if timer.collectId == collectId:
                timer.collectId = 0

    def timeUntilNextTimeout(self) -> int:
        if not self.timers:
            return -1

        now = time.time()
        timeout = min(
            t.expiresAt for t in self.timers if t.expiresAt <= now
        )
        return timeout
