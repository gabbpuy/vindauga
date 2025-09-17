# -*- coding: utf-8 -*-
from dataclasses import dataclass
import sys


@dataclass
class CharScanType:
    scanCode: int = 0
    charCode: str = '\x00'

    def __int__(self):
        if sys.byteorder == 'little':
            return self.scanCode << 8 | ord(self.charCode)
        else:
            return ord(self.charCode) << 8 | self.scanCode
