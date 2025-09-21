# -*- coding: utf-8 -*-
import os

from vindauga.constants.event_codes import evBroadcast
from vindauga.constants.std_dialog_commands import cmFileFocused
from vindauga.events.event import Event
from vindauga.utilities.filesystem.path_utils import fexpand
from vindauga.types.draw_buffer import DrawBuffer
from vindauga.types.palette import Palette
from vindauga.types.rect import Rect
from vindauga.types.view import View
from vindauga.utilities.support.prefix.prefix import closestPrefix


class FileInfoPane(View):
    cpInfoPane = "\x1E"

    def __init__(self, bounds: Rect):
        super().__init__(bounds)
        self.eventMask |= evBroadcast
        self.__fileBlock = None

    @staticmethod
    def getNiceSize(rate: float) -> str:
        if rate <= 0.0:
            return '0 B'

        value, prefix = closestPrefix(rate)
        s = f'{value:.0f} {prefix}B'
        return s

    def draw(self):
        # Assumes FileDialog owner
        path = self.owner.wildCard

        if not (':' in path or '/' in path):
            path = os.path.join(os.path.abspath(self.owner.directory), self.owner.wildCard)
            path = fexpand(path)

        color = self.getColor(0x01)
        b = DrawBuffer()

        b.moveChar(0, ' ', color, self.size.x)
        b.moveStr(1, path, color)
        self.writeLine(0, 0, self.size.x, 1, b)

        b.moveChar(0, ' ', color, self.size.x)
        b.moveStr(0, self.__fileBlock.name[:19], color)

        if self.__fileBlock.name:
            buf = self.getNiceSize(self.__fileBlock.size)
            b.moveStr(26 - len(buf), buf, color)
            dt = self.__fileBlock.time
            b.moveStr(27, dt.strftime('%Y-%m-%d %I:%M %p'), color)

        self.writeLine(0, 1, self.size.x, 1, b)
        b.moveChar(0, ' ', color, self.size.x)
        self.writeLine(0, 2, self.size.x, self.size.y - 2, b)

    def getPalette(self) -> Palette:
        return Palette(self.cpInfoPane)

    def handleEvent(self, event: Event):
        super().handleEvent(event)
        if event.what == evBroadcast and event.message.command == cmFileFocused:
            self.__fileBlock = event.message.infoPtr
            self.drawView()
