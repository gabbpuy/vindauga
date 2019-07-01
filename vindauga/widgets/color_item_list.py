# -*- coding: utf-8 -*-
import logging

from vindauga.constants.colors import cmSaveColorIndex, cmNewColorIndex, cmNewColorItem
from vindauga.constants.event_codes import evBroadcast
from vindauga.misc.message import message
from .list_viewer import ListViewer

logger = logging.getLogger('vindauga.widgets.color_item_list')


class ColorItemList(ListViewer):
    """
    The interrelated classes `ColorItem`, `ColorGroup`, `ColorSelector`,
    `MonoSelector`, `ColorDisplay`, `ColorGroupList`, `ColorItemList` and
    `ColorDialog` provide viewers and dialog boxes from which the user can
    select and change the color assignments from available palettes with
    immediate effect on the screen.
    
    `ColorItemList` is a simpler variant of `ColorGroupList` for viewing and
    selecting single color items rather than groups of colors.
       
    Like `ColorGroupList`, `ColorItemList` is specialized derivative of
    `ListViewer`. Color items can be selected in any of the usual ways (by
    mouse or keyboard).
       
    Unlike `ColorGroupList`, `ColorItemList` overrides the `ListViewer`
    event handler.
    """
    name = 'ColorItemList'

    def __init__(self, bounds, scrollBar, items):
        super().__init__(bounds, 1, 0, scrollBar)
        self._items = items

        self.eventMask |= evBroadcast
        self.setRange(len(items))

    def focusItem(self, item):
        """
        Selects the given item by calling `super().focusItem(item)`, then
        broadcasts a `cmNewColorIndex` event.

        :param item: Item number to focus
        """
        super().focusItem(item)
        message(self.owner, evBroadcast, cmSaveColorIndex, item)

        curItem = self._items[item]
        message(self.owner, evBroadcast, cmNewColorIndex, curItem.index)

    def getText(self, item, maxChars):
        curItem = self._items[item]
        return curItem.name[:maxChars]

    def handleEvent(self, event):
        super().handleEvent(event)

        if event.what == evBroadcast:
            g = event.message.infoPtr
            command = event.message.command
            if command == cmNewColorItem:
                self._items = g.items
                self.setRange(len(g.items))
                self.focusItem(g.index)
                self.drawView()
