# -*- coding: utf-8 -*-
from __future__ import annotations

import time

from typing import Callable

from dataclasses import dataclass

from vindauga.utilities.platform.system_interface import systemInterface


def systemTimeMs():
    # getTickCount() returns ticks at SystemInterface.TICKS_PER_SECOND;
    # convert that tick count to milliseconds. The previous fixed factor of
    # 55000 was off by orders of magnitude, making every timer fire far
    # sooner than requested.
    return systemInterface.getTickCount() * (1000 / systemInterface.TICKS_PER_SECOND)


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
        # Must use the same clock that setTimer()/timeUntilNextTimeout() use
        # for expiresAt (self.getTimeMs(), tick-based) -- comparing against
        # time.time() (wall-clock epoch seconds) made every timer appear
        # already expired the instant it was created.
        now = self.getTimeMs()

        removals = []
        for timer in self.timers:
            if timer.collectId or now < timer.expiresAt:
                continue
            if timer.period > 0:
                # Recurring timer: reschedule for the next period.
                timer.collectId = collectId
                timer.expiresAt = TimerQueue.calcNextExpiresAt(timer.expiresAt, now, timer.period)
            else:
                # One-shot timer (period <= 0): fire once, then remove it.
                # `period >= 0` here previously treated a one-shot timer
                # (period == 0) as recurring without ever advancing its
                # expiresAt, so it fired again on every subsequent idle
                # cycle forever instead of firing once.
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

        now = self.getTimeMs()
        nextExpiry = min(t.expiresAt for t in self.timers)
        return max(0, nextExpiry - now)
