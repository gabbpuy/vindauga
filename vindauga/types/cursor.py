# -*- coding: utf-8 -*-
from __future__ import annotations
from typing import TYPE_CHECKING

import logging
from vindauga.constants.state_flags import sfVisible, sfCursorVis, sfFocused, sfCursorIns

from vindauga.types.screen import Screen
from vindauga.utilities.platform.system_interface import systemInterface
from vindauga.utilities.platform.console_manager import ConsoleManager

logger = logging.getLogger(__name__)

if TYPE_CHECKING:
    from .view import View


class Cursor:
    """
    Handles cursor position calculation and visibility.
    """

    def __init__(self):
        self.view: View | None = None
        self.x: int = 0
        self.y: int = 0

    def reset_cursor(self, view: View):
        """
        Reset cursor position and visibility for the given view
        """

        self.view = view
        self.x = view.cursor.x
        self.y = view.cursor.y

        caret_size = self._compute_caret_size()

        # Convert view-relative coordinates to screen coordinates
        screen_x, screen_y = self._convert_to_screen_coords()

        if caret_size:
            # Set cursor position through hardware info
            systemInterface.setCaretPosition(screen_x, screen_y)

        # Set cursor size through hardware info  
        systemInterface.setCaretSize(caret_size)

    def _compute_caret_size(self) -> int:
        """
        Compute the appropriate caret size based on view state and visibility
        """
        if not self.view:
            return 0

        # Check if view is visible, has cursor visible, and is focused
        required_flags = sfVisible | sfCursorVis | sfFocused
        if (self.view.state & required_flags) != required_flags:
            return 0

        v = self.view
        x, y = self.x, self.y

        # Walk up the view hierarchy to check if cursor is visible
        while 0 <= y < v.size.y and 0 <= x < v.size.x:
            y += v.origin.y
            x += v.origin.x

            if v.owner:
                if v.owner.state & sfVisible:
                    if self._caret_covered(v, x, y):
                        break
                    v = v.owner
                else:
                    break
            else:
                # Reached root - cursor is visible
                return self._decide_caret_size()
        return 0

    def _caret_covered(self, view: View, x: int, y: int) -> bool:
        """
        Check if cursor is covered by another view
        """
        if not view.owner:
            return False

        # Check all views in front of this one
        current = view.owner.last.next if view.owner.last else None
        while current and current != view:
            if (current.state & sfVisible and
                    current.origin.y <= y < current.origin.y + current.size.y and
                    current.origin.x <= x < current.origin.x + current.size.x):
                return True
            current = current.next

        return False

    def _decide_caret_size(self) -> int:
        """
        Decide cursor size based on insert mode state
        """
        if not self.view:
            return 0

        if self.view.state & sfCursorIns:
            return 100  # Large cursor for insert mode

        # Normal cursor size from screen
        screen = Screen.screen
        if screen and hasattr(screen, 'cursorLines'):
            cursor_lines = screen.cursorLines & 0x0F
            if cursor_lines == 0:
                return 7
            return cursor_lines
        return 7  # Default small cursor

    def _convert_to_screen_coords(self) -> tuple[int, int]:
        """
        Convert view-relative cursor coordinates to absolute screen coordinates
        """
        if not self.view:
            return 0, 0

        # Start with view-relative coordinates
        x, y = self.x, self.y
        v = self.view

        # Walk up the view hierarchy, accumulating coordinate transformations
        while v:
            y += v.origin.y
            x += v.origin.x
            v = v.owner

        return x, y
