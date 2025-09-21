# -*- coding: utf-8 -*-
from vindauga.utilities.platform.events.get_ch_buf import GetChBuf


class CSIData:
    """
    CSI escape sequence data
    """

    def __init__(self):
        self.max_length = 6
        self._val = [0] * self.max_length
        self.terminator = 0
        self.length = 0

    def get_value(self, i: int, default_value: int = 1) -> int:
        """
        Get value at index i with default
        """
        if i < self.length and self._val[i] != 0xFFFFFFFF:
            return self._val[i]
        return default_value

    def read_from(self, buf: GetChBuf) -> bool:
        self.length = 0
        self.terminator = 0

        # Read parameters separated by semicolons
        while self.length < self.max_length:
            num = 0
            has_num = False

            # Read digits
            while True:
                k = buf.get()
                if k == -1:
                    return False
                if ord('0') <= k <= ord('9'):
                    num = num * 10 + (k - ord('0'))
                    has_num = True
                else:
                    break

            # Store the number
            if has_num:
                self._val[self.length] = num
            else:
                self._val[self.length] = 0xFFFFFFFF  # Mark as missing
            self.length += 1

            # Check terminator
            if k != ord(';'):
                self.terminator = k
                return True

        return False
