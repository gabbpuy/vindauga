# -*- coding: utf-8 -*-
"""
InputGetter interface - Python implementation of C++ tvision InputGetter
"""
from abc import ABC, abstractmethod


class InputGetter(ABC):
    """Abstract base class for input getters - matches C++ InputGetter"""
    
    @abstractmethod
    def get(self) -> int:
        """Get next character from input - returns -1 if no input available"""
        pass
    
    @abstractmethod
    def unget(self, key: int) -> None:
        """Push character back to input stream"""
        pass