# -*- coding: utf-8 -*-
from enum import IntEnum


class ParseResult(IntEnum):
    """
    Result of parsing an input event
    """
    Rejected = 0  # Event parsing failed, should unget characters
    Accepted = 1  # Event parsed successfully
    Ignored = 2   # Event parsed but should be ignored
