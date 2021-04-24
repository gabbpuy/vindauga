# -*- coding: utf-8 -*-
from vindauga.types.group import Group
from vindauga.types.palette import Palette

from .background import Background


class Panel(Group):
    """
    Group with a background installed. I do this enough that I'm making it a widget.
    """

    cpGrayDialog = ('\x20\x21\x22\x23\x24\x25\x26\x27\x28\x29\x2A\x2B\x2C\x2D\x2E\x2F' +
                    '\x30\x31\x32\x33\x34\x35\x36\x37\x38\x39\x3A\x3B\x3C\x3D\x3E\x3F')

    def __init__(self, bounds):
        super().__init__(bounds)
        self.initBackground()

    def initBackground(self):
        self.insert(Background(self.getExtent(), ' '))

    def getPalette(self):
        return Palette(self.cpGrayDialog)
