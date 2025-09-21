# -*- coding: utf-8 -*-
from __future__ import annotations
from dataclasses import dataclass


@dataclass
class TextMetrics:
    width: int
    character_count: int
    grapheme_count: int  # Number of non-combining characters
