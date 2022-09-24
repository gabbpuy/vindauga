# -*- coding: utf -8- -*-
import logging

from vindauga.constants.command_codes import cmCancel, cmDefault, cmOK, cmYes, cmNo
from vindauga.constants.window_flags import wfMove, wfClose
from vindauga.constants.event_codes import evKeyDown, evCommand, evBroadcast
from vindauga.constants.keys import *
from vindauga.constants.state_flags import sfModal
from vindauga.types.palette import Palette
from .window import Window

logger = logging.getLogger(__name__)

dpBlueDialog = 0
dpCyanDialog = 1
dpGrayDialog = 2


class Dialog(Window):

    name = 'Dialog'

    cpGrayDialog = ('\x20\x21\x22\x23\x24\x25\x26\x27\x28\x29\x2A\x2B\x2C\x2D\x2E\x2F' +
                    '\x30\x31\x32\x33\x34\x35\x36\x37\x38\x39\x3A\x3B\x3C\x3D\x3E\x3F')

    cpBlueDialog = ('\x40\x41\x42\x43\x44\x45\x46\x47\x48\x49\x4a\x4b\x4c\x4d\x4e\x4f' +
                    '\x50\x51\x52\x53\x54\x55\x56\x57\x58\x59\x5a\x5b\x5c\x5d\x5e\x5f')

    cpCyanDialog = ('\x60\x61\x62\x63\x64\x65\x66\x67\x68\x69\x6a\x6b\x6c\x6d\x6e\x6f' +
                    '\x70\x71\x72\x73\x74\x75\x76\x77\x78\x79\x7a\x7b\x7c\x7d\x7e\x7f')

    cpDialog = cpGrayDialog
    paletteBlue = Palette(cpBlueDialog)
    paletteCyan = Palette(cpCyanDialog)
    paletteGray = Palette(cpGrayDialog)

    _palettes = [paletteBlue, paletteCyan, paletteGray]

    def __init__(self, bounds, title):
        super().__init__(bounds, title, 0)

        self.growMode = 0
        self.flags = wfMove | wfClose
        self.palette = dpGrayDialog

    def __enter__(self):
        yield self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.destroy(self)

    def getPalette(self):
        return self._palettes[self.palette]

    def handleEvent(self, event):
        super().handleEvent(event)

        if event.what == evKeyDown:
            kc = event.keyDown.keyCode
            if kc == kbEsc:
                event.what = evCommand
                event.message.command = cmCancel
                event.message.infoPtr = None
                self.putEvent(event)
                self.clearEvent(event)
            elif kc == kbEnter:
                event.what = evBroadcast
                event.message.command = cmDefault
                event.message.infoPtr = None
                self.putEvent(event)
                self.clearEvent(event)
        elif event.what == evCommand:
            command = event.message.command
            if command in {cmOK, cmCancel, cmYes, cmNo}:
                if self.state & sfModal:
                    self.endModal(command)
                    self.clearEvent(event)

    def valid(self, command: int) -> bool:
        if command == cmCancel:
            return True
        return super().valid(command)
