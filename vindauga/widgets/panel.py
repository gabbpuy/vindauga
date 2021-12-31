# -*- coding: utf-8 -*-
from vindauga.types.group import Group

from .background import Background


class Panel(Group):
    """
    Group with a background installed. I do this enough that I'm making it a widget.
    """

    def __init__(self, bounds):
        super().__init__(bounds)
        self.initBackground()

    def initBackground(self):
        self.insert(Background(self.getExtent(), ' '))
