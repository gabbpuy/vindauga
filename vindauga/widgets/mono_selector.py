# -*- coding: utf-8 -*-
from vindauga.constants.colors import cmColorSet, cmColorForegroundChanged, cmColorBackgroundChanged
from vindauga.constants.event_codes import evBroadcast
from vindauga.misc.message import message

from .cluster import Cluster

monoColors = (0x07, 0x0F, 0x01, 0x70, 0x09)


class MonoSelector(Cluster):
    """
    The interrelated classes `ColorItem`, `ColorGroup`, `ColorSelector`,
    `MonoSelector`, `ColorDisplay`, `ColorGroupList`, `ColorItemList` and
    `ColorDialog` provide viewers and dialog boxes from which the user can
    select and change the color assignments from available palettes with
    immediate effect on the screen.

    `MonoSelector` implements a cluster from which you can select normal,
    highlight, underline, or inverse video attributes on monochrome screens.
    """
    name = 'MonoSelector'

    button = ' ( ) '
    normal = 'Normal'
    highlight = 'Highlight'
    underline = 'Underline'
    inverse = 'Inverse'

    def __init__(self, bounds):
        super().__init__(bounds, (self.normal, self.highlight, self.underline, self.inverse))
        self.eventMask |= evBroadcast
        self.value = 0

    def draw(self):
        self.drawBox(self.button, 0x07)

    def handleEvent(self, event):
        """
        Calls `super().handleEvent()` and responds to `cmColorSet` events by
        changing the data member `value` accordingly. The view is redrawn if
        necessary. `value` holds a video attribute corresponding to the
        selected attribute.

        :param event: Event to be handled
        """
        super().handleEvent(event)
        if event.what == evBroadcast and event.message.command == cmColorSet:
            self.value = event.message.infoPtr
            self.drawView()

    def mark(self, item):
        """
        Returns True if the item'th button has been selected; otherwise returns
        False.

        :param item: Item index
        :return: True if the item is selected, False otherwise
        """
        return monoColors[item] == self.value

    def newColor(self):
        """
        Informs the owning group if the attribute has changed.
        """
        message(self.owner, evBroadcast, cmColorForegroundChanged, self.value & 0x0F)
        message(self.owner, evBroadcast, cmColorBackgroundChanged, (self.value >> 4) & 0x0F)

    def press(self, item):
        """
        Sets `value` to the item'th attribute and calls `newColor()`.
        """
        self.value = monoColors[item]
        self.newColor()

    def movedTo(self, item):
        """
        Sets value to the item'th attribute (same effect as `press()`).

        :param item: Item number
        """
        self.value = monoColors[item]
        self.newColor()
