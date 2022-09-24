# -*- coding: utf-8 -*-
from dataclasses import dataclass
from typing import Any


@dataclass
class MessageEvent:
    command: int = 0
    infoPtr: Any = None

    """
    infoLong = None
    infoWord = None
    infoInt = None
    infoByte = None
    infoChar = None
    """