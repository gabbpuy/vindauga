# -*- coding: utf-8 -*-
from vindauga.constants.grow_flags import gfGrowHiX, gfGrowHiY
from vindauga.types.group import Group

from .background import Background


class Panel(Group):
    """
    Group with a background installed. I do this enough that I'm making it a widget.
    """

    def __init__(self, bounds):
        super().__init__(bounds)
        self.background = None
        self.initBackground()

    def initBackground(self):
        self.background = Background(self.getExtent(), ' ')
        self.background.growMode = gfGrowHiX | gfGrowHiY
        self.insert(self.background)
