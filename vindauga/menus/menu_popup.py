# -*- coding: utf-8 -*-
import logging

from vindauga.constants.event_codes import evKeyDown, evCommand
from vindauga.events.event import Event
from vindauga.utilities.input.character_codes import getCtrlChar, getAltChar
from vindauga.types.rect import Rect
from .menu_box import MenuBox

logger = logging.getLogger(__name__)


class MenuPopup(MenuBox):
    name = 'MenuPopup'

    def __init__(self, bounds: Rect, menu):
        super().__init__(bounds, menu, None)

    def handleEvent(self, event: Event):
        if event.what == evKeyDown:
            item = self.findItem(getCtrlChar(event.keyDown.keyCode))
            if not item:
                item = self.hotKey(event.keyDown.keyCode)

            if item and self.commandEnabled(item.command):
                event.what = evCommand
                event.message.command = item.command
                event.message.infoPtr = None
                self.putEvent(event)
                self.clearEvent(event)
            elif getAltChar(event.keyDown.keyCode):
                self.clearEvent(event)
        
        super().handleEvent(event)
