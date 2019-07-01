# -*- coding: utf-8 -*-
from dataclasses import dataclass


@dataclass
class CharScanEvent:
    scanCode: int = 0
    charCode: str = '\x00'
