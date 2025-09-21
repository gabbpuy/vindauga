# -*- coding: utf-8 -*-
from vindauga.utilities.platform.events.event_source import EventSource
from vindauga.utilities.platform.events.sys_manual_event import SysHandle


class InputAdapter(EventSource):
    """
    Base class for input adapters that handle keyboard, mouse, and other input events
    Extends EventSource to provide input-specific functionality
    """
    def __init__(self, handle: SysHandle):
        super().__init__(handle)
        self._enabled = True
        
    def enable(self, enabled: bool = True):
        """
        Enable or disable this input adapter
        """
        self._enabled = enabled
    
    def is_enabled(self) -> bool:
        """
        Check if input adapter is enabled
        """
        return self._enabled
    
    def has_pending_events(self) -> bool:
        """
        Check if input events are pending - override in subclasses
        """
        return False
    
    def get_event(self, event):
        """
        Get next input event - override in subclasses
        """
        return False
    
    def flush_input(self):
        """
        Flush any pending input events
        """
        pass
    
    def reset_input_state(self):
        """
        Reset input adapter state
        """
        pass
