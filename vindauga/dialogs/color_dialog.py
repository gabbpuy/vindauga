# -*- coding: utf-8 -*-
import logging

from vindauga.constants.buttons import bfNormal, bfDefault
from vindauga.constants.command_codes import cmOK, cmCancel
from vindauga.constants.colors import cmNewColorIndex, cmNewColorItem, cmSetColorIndex
from vindauga.constants.event_codes import evBroadcast
from vindauga.constants.option_flags import ofCentered
from vindauga.constants.key_mappings import showMarkers
from vindauga.types.rect import Rect
from vindauga.widgets.button import Button
from vindauga.widgets.color_display import ColorDisplay
from vindauga.widgets.color_group_list import ColorGroupList
from vindauga.widgets.color_item_list import ColorItemList
from vindauga.widgets.color_selector import ColorSelector
from vindauga.widgets.dialog import Dialog
from vindauga.widgets.label import Label
from vindauga.widgets.mono_selector import MonoSelector
from vindauga.widgets.scroll_bar import ScrollBar

logger = logging.getLogger(__name__)


class ColorIndex:
    def __init__(self):
        self.groupIndex = 0
        self.colorSize = 0
        self.colorIndex = []


class ColorDialog(Dialog):
    """
    `ColorDialog` is a specialized scrollable dialog box called "Colors" from
    which the user can examine various palette selections before making a
    selection.
    """
    name = 'ColorDialog'

    colors = _('Colors')
    groupText = _('~G~roup')
    itemText = _('~I~tem')
    forText = _('~F~oreground')
    bakText = _('~B~ackground')
    textText = _('Text')
    colorText = _('Color')
    okText = _('O~K~')
    cancelText = _('Cancel')

    def __init__(self, palette, groups):
        super().__init__(Rect(0, 0, 79, 18), self.colors)
        self.groupIndex = None
        self.colorIndexes = None

        self.options |= ofCentered
        if palette:
            self.pal = palette
        else:
            self.pal = None

        sb = ScrollBar(Rect(27, 3, 28, 14))
        self.insert(sb)

        self._groups = ColorGroupList(Rect(3, 3, 27, 14), sb, groups)
        self.insert(self._groups)
        self.insert(Label(Rect(3, 2, 10, 3), self.groupText, self._groups))

        sb = ScrollBar(Rect(59, 3, 60, 14))
        self.insert(sb)

        p = ColorItemList(Rect(30, 3, 59, 14), sb, groups.items)
        self.insert(p)

        self.insert(Label(Rect(30, 2, 36, 3), self.itemText, p))

        self._forSel = ColorSelector(Rect(63, 3, 75, 7), ColorSelector.csForeground)

        self.insert(self._forSel)

        self._forLabel = Label(Rect(63, 2, 75, 3), self.forText, self._forSel)
        self.insert(self._forLabel)

        self._bakSel = ColorSelector(Rect(63, 9, 75, 11), ColorSelector.csBackground)
        self.insert(self._bakSel)
        self._bakLabel = Label(Rect(63, 8, 75, 9), self.bakText, self._bakSel)
        self.insert(self._bakLabel)

        self._display = ColorDisplay(Rect(62, 12, 76, 14), self.textText)
        self.insert(self._display)

        self._monoSel = MonoSelector(Rect(62, 3, 77, 7))
        self._monoSel.hide()
        self.insert(self._monoSel)
        self._monoLabel = Label(Rect(62, 2, 69, 3), self.colorText, self._monoSel)
        self._monoLabel.hide()
        self.insert(self._monoLabel)

        self.insert(Button(Rect(51, 15, 61, 17), self.okText, cmOK, bfDefault))
        self.insert(Button(Rect(63, 15, 73, 17), self.cancelText, cmCancel, bfNormal))
        self.selectNext(False)
        if self.pal:
            self.setData(self.pal)

    def handleEvent(self, event):
        if event.what == evBroadcast:
            if event.message.command == cmNewColorItem:
                self.groupIndex = self._groups.focused
            elif event.message.command == cmSetColorIndex:
                self.pal.palette[self._groups.getGroupIndex(self.groupIndex)] = event.message.infoPtr
            elif event.message.command == cmNewColorIndex:
                self._display.setColor(self.pal.palette[event.message.infoPtr])
        super().handleEvent(event)

    def consumesData(self):
        return True

    def getData(self):
        """
        Reads the data record of this dialog.
        """
        self.colorIndexes = self.getIndexes(self.colorIndexes)
        return self.pal

    def setData(self, palette):
        """
        Sets the palette to the

        :param palette: A Palette
        """
        self.pal = palette
        self.colorIndexes = self.setIndexes(self.colorIndexes)

        self._display.setColor(self.pal.palette[self._groups.getGroupIndex(self.groupIndex)])
        self._groups.focusItem(self.groupIndex)
        if showMarkers:
            self._forLabel.hide()
            self._forSel.hide()
            self._bakLabel.hide()
            self._bakSel.hide()
            self._monoLabel.show()
            self._monoSel.show()

        self._groups.select()

    def setIndexes(self, colorIndex):
        numGroups = self._groups.getNumGroups()

        if colorIndex and (colorIndex.colorSize != numGroups):
            colorIndex = None

        if not colorIndex:
            colorIndex = ColorIndex()
            colorIndex.colorIndex = [0] * numGroups
            colorIndex.colorSize = numGroups

        for index in range(numGroups):
            self._groups.setGroupIndex(index, colorIndex.colorIndex[index])

        self.groupIndex = colorIndex.groupIndex
        return colorIndex

    def getIndexes(self, colorIndex):
        n = self._groups.getNumGroups()

        if not colorIndex:
            colorIndex = ColorIndex()
            colorIndex.colorSize = n
        colorIndex.groupIndex = self.groupIndex
        colorIndex.colorIndex.extend(self._groups.groups)
        return colorIndex
