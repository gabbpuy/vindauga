# -*- coding: utf-8 -*-
from dataclasses import dataclass


@dataclass
class MessageEvent:
    command: int = 0
    infoPtr: object = None

    """
    infoLong = None
    infoWord = None
    infoInt = None
    infoByte = None
    infoChar = None
    """