# -*- coding: utf-8 -*-
from __future__ import annotations
from copy import copy
from dataclasses import dataclass, field

from vindauga.types.point import Point


@dataclass
class MouseEvent:
    where: Point = field(default_factory=Point)
    eventFlags: int = 0
    controlKeyState: int = 0
    buttons: int = 0
    wheel: int = 0

    def copy(self, other: MouseEvent):
        self.where = copy(other.where)
        self.eventFlags = other.eventFlags
        self.controlKeyState = other.controlKeyState
        self.buttons = other.buttons
        self.wheel = other.wheel
