# -*- coding: utf-8 -*-
from dataclasses import dataclass
import logging
from typing import List, Optional

from vindauga.constants.command_codes import wnNoNumber
from vindauga.constants.option_flags import ofCentered, ofBuffered
from vindauga.constants.event_codes import evBroadcast
from vindauga.events.event import Event
from vindauga.utilities.message import message
from vindauga.types.palette import Palette
from vindauga.types.rect import Rect
from vindauga.types.view import View

from .message_window import cmFindInfoBox, cmInsInfoBox
from .program import Program
from .static_prompt import StaticPrompt
from .static_text import StaticText
from .window import Window


logger = logging.getLogger(__name__)


class InfoWindow(Window):
    cpInfoWindow = "\x18\x19\x1A\x1B\x1C\x1D\x1E\x1F\x14"

    def __init__(self, bounds: Rect, title: str, windowNumber: int):
        super().__init__(bounds, title, windowNumber)

        self.flags = 0
        self.options |= (ofCentered | ofBuffered)
        self.count = 0
        self.items: List[Optional[View]] = [None] * 25

    def handleEvent(self, event: Event):
        if event.what == evBroadcast:
            emc = event.message.command
            if emc == cmFindInfoBox:
                self.clearEvent(event)
            elif emc == cmInsInfoBox:
                p: InfoData = event.message.infoPtr
                r = self.getExtent()
                lastLine = r.bottomRight.y - 2
                i = p.line
                if i > r.bottomRight.y - r.topLeft.y - 1:
                    return
                self.lock()
                try:
                    if self.items[i]:
                        self.remove(self.items[i])
                        self.destroy(self.items[i])
                        self.items[i] = None

                    r.topLeft.y = i
                    r.bottomRight.y = i + 1

                    if i == lastLine:
                        r.topLeft.x += 1
                        r.bottomRight.x -= 1
                        self.items[i] = StaticPrompt(r, p.text)
                    else:
                        r.topLeft.x += 2
                        r.bottomRight.x -= 1
                        self.items[i] = StaticText(r, p.text)

                    self.insert(self.items[i])
                finally:
                    self.unlock()
                    self.clearEvent(event)

    def getPalette(self) -> Palette:
        return Palette(self.cpInfoWindow)


@dataclass(frozen=True)
class InfoData:
    line: int
    text: str


def postInfo(line: int, text: str):
    wPtr = message(Program.desktop, evBroadcast, cmFindInfoBox, 0)
    if line < 0 and wPtr:
        Program.desktop.destroy(wPtr)
        return

    if not wPtr:
        wPtr = InfoWindow(Rect(0, 0, 40, 12), 'Information', wnNoNumber)
        Program.desktop.insert(wPtr)

    data = InfoData(line=line, text=text)
    message(wPtr, evBroadcast, cmInsInfoBox, data)
