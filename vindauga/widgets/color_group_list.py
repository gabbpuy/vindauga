# -*- coding: utf-8 -*-
import logging

from vindauga.constants.colors import cmNewColorItem, cmSaveColorIndex
from vindauga.constants.event_codes import evBroadcast
from vindauga.misc.message import message
from vindauga.widgets.list_viewer import ListViewer

logger = logging.getLogger('vindauga.widgets.color_group_list')


class ColorGroupList(ListViewer):
    """
    The interrelated classes `ColorItem`, `ColorGroup`, `ColorSelector`,
    `MonoSelector`, `ColorDisplay`, `ColorGroupList`, `ColorItemList` and
    `ColorDialog` provide viewers and dialog boxes from which the user can
    select and change the color assignments from available palettes with
    immediate effect on the screen.

    `ColorGroupList` is a specialized derivative of `ListViewer` providing a
    scrollable list of named color groups. Groups can be selected in any of the
    usual ways (by mouse or keyboard).

    `ColorGroupList` uses the `ListViewer` event handler without modification.
    """
    name = 'ColorGroupList'

    def __init__(self, bounds, scrollBar, groups):
        super().__init__(bounds, 1, 0, scrollBar)
        self._groups = groups
        self.setRange(len(self._groups.groups))

    def focusItem(self, item):
        """
        Selects the given item by calling `super().focusItem(item)` and then
        broadcasts a `cmNewColorItem` event.

        :param item: Item to select
        """
        super().focusItem(item)
        curGroup = self._groups.groups[item]
        message(self.owner, evBroadcast, cmNewColorItem, curGroup)

    def getText(self, item, maxChars):
        """
        Retrieve the group name corresponding to item

        :param item: The group index
        :param maxChars: Max length of the string to return
        :return: The group name
        """
        curGroup = self._groups.groups[item]
        return curGroup.name[:maxChars]

    def handleEvent(self, event):
        super().handleEvent(event)
        if event.what == evBroadcast:
            if event.message.command == cmSaveColorIndex:
                self.setGroupIndex(self.focused, event.message.infoPtr)

    def setGroupIndex(self, groupNum, itemNum):
        g = self.getGroup(groupNum)
        g.index = itemNum

    def getGroupIndex(self, groupNum):
        g = self.getGroup(groupNum)
        return g.index

    def getGroup(self, groupNum):
        return self._groups.groups[groupNum]

    def getNumGroups(self):
        return len(self._groups.groups)

    def __getitem__(self, groupNum):
        return self._groups.groups[groupNum]
