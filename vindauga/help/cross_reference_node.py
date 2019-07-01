# -*- coding: utf-8 -*-
from dataclasses import dataclass


@dataclass
class CrossReferenceNode:
    topic: str
    offset: int
    length: int
    next: 'CrossReferenceNode'
