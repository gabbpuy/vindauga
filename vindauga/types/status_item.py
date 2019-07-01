# -*- coding: utf-8 -*-
from dataclasses import dataclass


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
    next: 'StatusItem' = None
