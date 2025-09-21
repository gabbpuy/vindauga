from enum import Enum, auto
import sys


class TermColourTypes(Enum):
    Default = auto()
    Indexed = auto()
    RGB = auto()
    NoColor = auto()


class TermColour:
    def __init__(self, type: TermColourTypes, idx: int = None, bgr: tuple[int, int, int] = (0, 0, 0)):
        self.type: TermColourTypes = type
        self.idx: int = idx
        self.bgr: tuple[int, int, int] = bgr

    def __int__(self):
        return int.from_bytes((self.idx,) + self.bgr, byteorder=sys.byteorder)

    def __eq__(self, other):
        return self.type == other.type and self.idx == other.idx and self.bgr == other.bgr

    def __ne__(self, other):
        return not self == other

    def from_int(self, val: int):
        parts = val.to_bytes(byteorder=sys.byteorder)
        self.idx = parts[0]
        self.bgr = (parts[1], parts[2], parts[3])

    @classmethod
    def default(cls):
        return cls(TermColourTypes.Default)

    @classmethod
    def indexed(cls, idx: int):
        return cls(TermColourTypes.Indexed, idx=idx)

    @classmethod
    def rgb(cls, r: int, g: int, b: int):
        return cls(TermColourTypes.RGB, bgr=(b, g, r))
