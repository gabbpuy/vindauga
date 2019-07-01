# -*- coding: utf-8 -*-
from dataclasses import dataclass, field
from typing import List

@dataclass
class FixUp:
    pos: int
    next: 'FixUp'


@dataclass
class Content:
    value: int = 0
    fixUpList: List[FixUp] = field(default_factory=list)


@dataclass
class Reference:
    topic: str
    resolved: bool
    val: Content = field(default_factory=Content)
