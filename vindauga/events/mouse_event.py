# -*- coding: utf-8 -*-
from dataclasses import dataclass, field

from vindauga.types.point import Point


@dataclass
class MouseEvent:
    where: Point = field(default_factory=Point)
    eventFlags: int = 0
    controlKeyState: int = 0
    buttons: int = 0
