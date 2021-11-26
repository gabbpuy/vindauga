# -*- coding: utf-8 -*-
import logging

from vindauga.constants.event_codes import evKeyDown, evCommand
from vindauga.misc.character_codes import getCtrlChar, getAltChar

from .menu_box import MenuBox

logger = logging.getLogger(__name__)


class MenuPopup(MenuBox):
    name = 'MenuPopup'

    def __init__(self, bounds, menu):
        super().__init__(bounds, menu, None)

    def handleEvent(self, event):
        logger.info('handleEvent(%s)', event)
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
