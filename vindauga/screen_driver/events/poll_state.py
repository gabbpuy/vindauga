# -*- coding: utf-8 -*-
from enum import Enum, auto


class PollState(Enum):
    Nothing = auto()
    Ready = auto()
    Disconnect = auto()
