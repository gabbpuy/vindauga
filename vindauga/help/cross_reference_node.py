# -*- coding: utf-8 -*-
from __future__ import annotations
from dataclasses import dataclass
from typing import Optional


@dataclass
class CrossReferenceNode:
    topic: str
    offset: int
    length: int
    next: Optional[CrossReferenceNode] = None
