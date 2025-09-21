# -*- coding: utf-8 -*-
from dataclasses import dataclass, field
from vindauga.utilities.colours.style_mask import StyleMask
from .colour import TermColour


@dataclass
class TermAttribute:
    fg: TermColour = field(default_factory=TermColour.default)
    bg: TermColour = field(default_factory=TermColour.default)
    style: StyleMask = StyleMask.NONE
