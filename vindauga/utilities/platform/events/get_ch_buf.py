# -*- coding: utf-8 -*-
import logging

from .input_getter import InputGetter

logger = logging.getLogger(__name__)


class GetChBuf:
    """
    Buffered character reader with unget functionality
    """
    MAX_SIZE = 31
    
    def __init__(self, input_getter: InputGetter):
        self.in_getter = input_getter
        self.keys = []
    
    def get_unbuffered(self) -> int:
        """
        Get character directly from input without buffering
        """
        return self.in_getter.get()

    def get(self, keep_err: bool = False) -> int:
        """
        Get character and buffer it
        """
        if len(self.keys) < self.MAX_SIZE:
            k = self.in_getter.get()
            if keep_err or k != -1:
                self.keys.append(k)
            return k
        return -1
    
    def last(self, i: int = 0) -> int:
        """
        Get previously read character (0 = most recent)
        """
        if i < len(self.keys):
            return self.keys[-(i + 1)]
        return -1
    
    def unget(self) -> None:
        """
        Push most recent character back to input stream
        """
        if self.keys:
            k = self.keys.pop()
            if k != -1:
                self.in_getter.unget(k)
    
    def reject(self) -> None:
        """
        Reject all buffered characters by pushing them back
        """
        while self.keys:
            self.unget()
    
    def get_num(self) -> tuple[bool, int]:
        """
        Read a numeric value from input
        """
        num = 0
        digits = 0
        k = 0
        while (k := self.get(True)) != -1 and ord('0') <= k <= ord('9'):
            num = 10 * num + k - ord('0')
            digits += 1
        if digits:
            return True, num

        return False, 0
    
    def get_int(self) -> tuple[bool, int]:
        """
        Read an integer value from input
        """
        num = 0
        digits = 0
        sign = 1
        k = self.get(True)
        if k == '-':
            sign = -1
            k = self.get(True)

        while k != -1 and ord('0') <= k <= ord('9'):
            num = 10 * num + k - ord('0')
            digits += 1
            k = self.get(True)

        if digits:
            return True, num * sign
        return False, 0
    
    def read_str(self, expected: str) -> bool:
        """
        Read and match a specific string
        """
        original_size = len(self.keys)
        i = 0
        while i < len(expected) and self.get() == expected[i]:
            i += 1
        if i == len(expected):
            return True
        while original_size < len(self.keys):
            self.unget()
        return False
