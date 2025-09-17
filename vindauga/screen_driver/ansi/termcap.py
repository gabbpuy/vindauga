# -*- coding: utf-8 -*-
from dataclasses import dataclass
import logging
import os
import platform
from typing import Any

from .termcap_colours import TermCapColours
from .quirks import TerminalQuirks


@dataclass
class TermCap:
    colours: TermCapColours
    quirks: TerminalQuirks

    @classmethod
    def get_display_capabilities(cls, console_ctl: Any, display_adapter: Any):
        logger = logging.getLogger(__name__)
        quirks = TerminalQuirks.NONE
        colour_term = os.getenv('COLORTERM', None)
        term = os.getenv('TERM', None)
        
        if colour_term in ('truecolor', '24bit'):
            colours = TermCapColours.Direct
        else:
            _colours = display_adapter.get_colour_count()
            
            if _colours >= 256**3:
                colours = TermCapColours.Direct
            elif _colours >= 256:
                colours = TermCapColours.Indexed256
            elif _colours >= 16:
                colours = TermCapColours.Indexed16
            else:
                colours = TermCapColours.Indexed8
                quirks |= TerminalQuirks.BoldIsBright
                if term == 'xterm':
                    colours = TermCapColours.Indexed16
        
        return cls(colours, quirks)
