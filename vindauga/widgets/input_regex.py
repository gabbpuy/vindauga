# -*- coding: utf-8 -*-
import re
from curses.ascii import iscntrl
import logging

from vindauga.constants.command_codes import cmReleasedFocus, cmQuit, cmOK, cmClose
from vindauga.constants.message_flags import mfError, mfOKButton
from vindauga.constants.event_codes import evKeyDown
from vindauga.constants.state_flags import sfSelected, sfFocused
from vindauga.dialogs.message_box import messageBox
from vindauga.events.event import Event
from vindauga.types.screen import Screen
from .input_line import InputLine

logger = logging.getLogger(__name__)


class InputRegex(InputLine):
    name = 'InputRegex'

    def __init__(self, bounds, maxLen, keySet=None, regex=None, newCase=None):
        super().__init__(bounds, maxLen)
        self.regex = regex
        self.keySet = keySet
        self.newCase = newCase
        self.inUse = False
        if keySet and newCase:
            self.keySet = newCase(keySet)

    def setState(self, state, enable):
        if state & sfFocused and not enable and not self.inUse:
            self.inUse = True
            check = self.valid(cmReleasedFocus)
            self.inUse = False
            if not check:
                return
        super().setState(state, enable)

    def handleEvent(self, event: Event):
        if self.state & sfSelected and event.what == evKeyDown:
            key = event.keyDown.charScan.charCode
            if not iscntrl(key):
                if self.newCase:
                    key = self.newCase(key)
                if self.keySet and not re.match(self.keySet, key):
                    logger.info('No regex match')
                    Screen.beep()
                    self.clearEvent(event)
                    return
        super().handleEvent(event)

    def valid(self, command):
        if command == cmReleasedFocus:
            return True

        if command in {cmQuit, cmClose, cmOK}:
            if self.regex:
                try:
                    m = re.match(self.regex, self.getDataString())
                    if m and m.string != self.getDataString():
                        self.select()
                        return False
                except Exception as e:
                    messageBox(str(e), mfError, (mfOKButton,))
                    return False
        return super().valid(command)
