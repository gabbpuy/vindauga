# -*- coding: utf-8 -*-
from abc import ABC, abstractmethod


class InputGetter(ABC):
    """
    Abstract base class for input getters
    """
    
    @abstractmethod
    def get(self) -> int:
        """
        Get next character from input
        """
        pass
    
    @abstractmethod
    def unget(self, key: int) -> None:
        """
        Push character back to input stream
        """
        pass