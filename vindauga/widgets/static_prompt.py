# -*- coding: utf-8 -*-
from vindauga.types.palette import Palette
from .static_text import StaticText


class StaticPrompt(StaticText):
    cpStaticPrompt = "\x09"

    def getPalette(self):
        return Palette(self.cpStaticPrompt)
