# -*- coding: utf-8 -*-
import curses
import logging
from vindauga.utilities.platform.events.input_getter import InputGetter

logger = logging.getLogger(__name__)


class NcursesInputGetter(InputGetter):
    """
    Curses-based input getter with unget support
    """
    def __init__(self, screen=None):
        self.screen = screen
        self.pending_count = 0
        
    def get(self) -> int:
        """
        Get next character
        """
        if not self.screen:
            return -1
            
        try:
            k = self.screen.getch()
            if self.pending_count > 0:
                self.pending_count -= 1
            return k
        except Exception:
            return curses.ERR
    
    def unget(self, key: int) -> None:
        """
        Push character back
        """
        try:
            if curses.ungetch(key) != curses.ERR:
                self.pending_count += 1
        except Exception:
            pass
    
    def has_pending(self) -> bool:
        """
        Check if characters are pending
        """
        return self.pending_count > 0
