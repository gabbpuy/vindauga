# -*- coding: utf-8 -*-
from __future__ import annotations
from dataclasses import dataclass
from typing import Optional


@dataclass
class StatusItem:
    """
    A `StatusItem` object is not a view but represents a component (status item)
    of a linked list associated with a `StatusLine` view.
       
    `StatusItem` serves two purposes: it controls the visual appearance of the
    status line, and it defines hot keys by mapping key codes to commands.
    """
    text: str
    keyCode: int
    command: int
    next: Optional[StatusItem] = None
