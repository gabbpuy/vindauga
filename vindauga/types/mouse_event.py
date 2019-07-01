# -*- coding: utf-8 -*-
from dataclasses import dataclass


@dataclass
class MouseEvent:
    id: int
    x: int
    y: int
    z: int
    bstate: int
