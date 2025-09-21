# -*- coding: utf-8 -*-
from dataclasses import dataclass, field
from typing import Callable, Optional

from vindauga.types.point import Point


@dataclass
class InputState:
    buttons: int = 0  # Mouse button state
    surrogate: int = 0
    bracketed_paste: bool = False  # Terminal supports bracketed paste
    got_response: bool = False  # Got terminal capability response
    has_full_osc52: bool = False  # Full OSC52 clipboard support

    # Callbacks
    put_paste: Optional[Callable[[str], None]] = None

    # Mouse state - use default_factory for mutable defaults
    last_mouse_pos: Point = field(default_factory=lambda: Point(0, 0))

    def reset(self):
        """
        Reset transient state
        """
        self.got_response = False
