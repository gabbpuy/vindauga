# -*- coding: utf-8 -*-
import logging
import os

from vindauga.types.collections.file_collection import FA_DIREC
from vindauga.constants.event_codes import evBroadcast
from vindauga.constants.state_flags import sfSelected
from vindauga.constants.std_dialog_commands import cmFileFocused
from vindauga.events.event import Event
from vindauga.misc.util import fexpand
from vindauga.types.rect import Rect

from .input_line import InputLine


logger = logging.getLogger(__name__)


class FileInputLine(InputLine):
    name = 'FileInputLine'

    def __init__(self, bounds: Rect, maxLen: int):
        super().__init__(bounds, maxLen)
        self.eventMask |= evBroadcast

    def handleEvent(self, event: Event):
        super().handleEvent(event)

        if (event.what == evBroadcast and
                event.message.command == cmFileFocused and not (self.state & sfSelected)):
            if event.message.infoPtr.attr & FA_DIREC:
                p = self.owner.wildCard
                self.setData(fexpand(os.path.join(event.message.infoPtr.name, p)))
            else:
                self.setData(event.message.infoPtr.name)
            self.drawView()
