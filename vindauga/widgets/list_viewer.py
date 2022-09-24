# -*- coding: utf-8 -*-
import logging

from vindauga.constants.command_codes import (cmScrollBarClicked, cmScrollBarChanged, cmListItemSelected)
from vindauga.constants.event_codes import evBroadcast, evMouseDown, evMouseAuto, evMouseMove, meDoubleClick, evKeyDown
from vindauga.constants.keys import kbUp, kbDown, kbLeft, kbRight, kbPgDn, kbPgUp, kbHome, kbEnd, kbCtrlPgDn, \
    kbCtrlPgUp, kbEnter
from vindauga.constants.option_flags import ofSelectable, ofFirstClick
from vindauga.constants.state_flags import sfVisible, sfActive, sfSelected
from vindauga.constants.key_mappings import showMarkers
from vindauga.misc.character_codes import SPECIAL_CHARS
from vindauga.misc.message import message
from vindauga.misc.util import ctrlToArrow
from vindauga.types.draw_buffer import DrawBuffer
from vindauga.types.palette import Palette
from vindauga.types.view import View

logger = logging.getLogger(__name__)


class ListViewer(View):
    """
    ListViewer is an abstract class from which you can derive list viewers of
    various kinds, such as `TListBox`. `ListViewer`'s members offer the
    following functionality:

    * A view for displaying linked lists of items (but no list)
    * Control over one or two scroll bars
    * Basic scrolling of lists in two dimensions
    * Reading and writing the view and its scroll bars from and to a stream
    * Ability to use a mouse or the keyboard to select (highlight) items on
      list
    * Draw member function that copes with resizing and scrolling

    `ListViewer` has an abstract `getText()` method, so you need to supply
    the mechanism for creating and manipulating the text of the items to be
    displayed.

    `ListViewer` has no list storage mechanism of its own. Use it to display
    scrollable lists of arrays, linked lists, or similar data structures. You
    can also use its descendants, such as `ListBox`, which associates a
    collection with a list viewer.
    """
    emptyText = ""
    separatorChar = '│'
    cpListViewer = "\x1A\x1A\x1B\x1C\x1D"
    name = 'ListViewer'

    def __init__(self, bounds, numColumns, hScrollBar, vScrollBar):
        super().__init__(bounds)

        self.numCols = numColumns
        self.topItem = 0
        self.focused = 0
        self._range = 0

        self.options |= ofFirstClick | ofSelectable
        self.eventMask |= evBroadcast

        if vScrollBar:
            if self.numCols == 1:
                pageStep = self.size.y - 1
                arrowStep = 1
            else:
                pageStep = self.size.y * self.numCols
                arrowStep = self.size.y

            vScrollBar.setStep(pageStep, arrowStep)

        if hScrollBar:
            hScrollBar.setStep(self.size.x // self.numCols, 1)

        self.hScrollBar = hScrollBar
        self.vScrollBar = vScrollBar

    def changeBounds(self, bounds):
        """
        Changes the size of the `ListViewer` object by calling
        `super().changeBounds(bounds)`. If a horizontal scroll bar has been
        assigned, `pageStep` is updated by way of `setStep()`.

        :param bounds: Bounds to set to
        """
        super().changeBounds(bounds)

        if self.hScrollBar:
            self.hScrollBar.setStep(self.size.x // self.numCols,
                                    self.hScrollBar.arrowStep)

        if self.vScrollBar:
            self.vScrollBar.setStep(self.size.y, self.vScrollBar.arrowStep)

    def draw(self):
        """
        Draws the `ListViewer` object with the default palette by repeatedly
        calling `getText()` for each visible item. Takes into account the
        `focused` and `selected` items and whether the view is `sfActive`.
        """
        focusedColor = 0
        b = DrawBuffer()

        active_ = (self.state & sfSelected | sfActive) == (sfSelected | sfActive)
        if active_:
            normalColor = self.getColor(1)
            focusedColor = self.getColor(3)
            selectedColor = self.getColor(4)
        else:
            normalColor = self.getColor(2)
            selectedColor = self.getColor(4)

        if self.hScrollBar:
            indent = self.hScrollBar.value
        else:
            indent = 0

        colWidth = self.size.x // self.numCols + 1

        for i in range(self.size.y):
            for j in range(self.numCols):
                item = j * self.size.y + i + self.topItem
                curCol = j * colWidth

                if active_ and (self.focused == item) and (self._range > 0):
                    color = focusedColor
                    self.setCursor(curCol + 1, i)
                    scOff = 2
                elif item < self._range and self.isSelected(item):
                    color = selectedColor
                    scOff = 2
                else:
                    color = normalColor
                    scOff = 4

                b.moveChar(curCol, ' ', color, colWidth)

                if item < self._range:
                    text = self.getText(item, colWidth + indent)[indent:indent + colWidth]

                    b.moveStr(curCol + 1, text, color)
                    if showMarkers:
                        b.putChar(curCol, SPECIAL_CHARS[scOff])
                        b.putChar(curCol + colWidth - 2, SPECIAL_CHARS[scOff + 1])
                elif i == 0 and j == 0:
                    b.moveStr(curCol + 1, self.emptyText, self.getColor(1))

                b.moveChar(curCol + colWidth - 1, self.separatorChar, self.getColor(5), 1)
            self.writeLine(0, i, self.size.x, 1, b)

    def focusItem(self, item):
        """
        Makes the given item focused by setting the `focused` data member to
        `item`. Also sets the `value` data member of the vertical scroll bar (if any) to
        `item` and adjusts `topItem`.

        :param item: Item index to focus
        """
        self.focused = item

        if self.vScrollBar:
            self.vScrollBar.setValue(item)
        else:
            self.drawView()

        if item < self.topItem:
            if self.numCols == 1:
                self.topItem = item
            else:
                self.topItem = item - item % self.size.y
        else:
            if item >= self.topItem + self.size.y * self.numCols:
                if self.numCols == 1:
                    self.topItem = item - self.size.y + 1
                else:
                    self.topItem = item - item % self.size.y - (self.size.y * (self.numCols - 1))

    def getPalette(self):
        palette = Palette(self.cpListViewer)
        return palette

    def getText(self, item, maxLen):
        return ''

    def isSelected(self, item):
        """
        Returns True if the given item is selected (focused), that is, if `item` == `focused`.

        :param item: Item number to test
        :return: True if item is selected
        """
        return item == self.focused

    def handleEvent(self, event):
        """
        Handles events by first calling `super().handleEvent(event)`.

        Mouse clicks and "auto" movements over the list will change the focused
        item. Items can be selected with double mouse clicks.

        Keyboard events are handled as follows: Spacebar selects the currently
        focused item; the arrow keys, PgUp, PgDn, Ctrl-PgDn, Ctrl-PgUp, Home,
        and End keys are tracked to set the focused item.

        Broadcast events from the scroll bars are handled by changing the
        `focused` item and redrawing the view as required.

        :param event: Event to handle
        """
        mouseAutosToSkip = 4
        super().handleEvent(event)

        if event.what == evMouseDown:
            self.__handleMouseEvent(event, mouseAutosToSkip)
        elif event.what == evKeyDown:
            self.__handleKeyDownEvent(event)
        elif event.what == evBroadcast:
            if self.options & ofSelectable:
                if (event.message.command == cmScrollBarClicked and
                        (event.message.infoPtr in {self.hScrollBar, self.vScrollBar})):
                    self.focus()
                elif event.message.command == cmScrollBarChanged:
                    if self.vScrollBar is event.message.infoPtr:
                        self.focusItemNum(self.vScrollBar.value)
                        self.drawView()
                    elif self.hScrollBar is event.message.infoPtr:
                        self.drawView()

    def selectItem(self, item):
        """
        Selects the item'th element of the list, then broadcasts this fact to
        the owning group by calling:

        ```
        message(owner, evBroadcast, cmListItemSelected, self)
        ```

        :param item: Item to select
        """
        message(self.owner, evBroadcast, cmListItemSelected, self)

    def setRange(self, range_):
        """
        Sets the `_range` data member to `range_`.

        If a vertical scroll bar has been assigned, its parameters are adjusted
        as necessary (and `drawView()` is invoked if redrawing is needed).

        If the currently focused item falls outside the new range, the
        `focused` data member is set to zero.

        :param range_: Number of items...
        """
        self._range = range_

        if self.focused >= range_:
            self.focused = range_ - 1 if (range_ - 1 >= 0) else 0

        if self.vScrollBar:
            self.vScrollBar.setParams(self.focused, 0, range_ - 1,
                                      self.vScrollBar.pageStep,
                                      self.vScrollBar.arrowStep)
        else:
            self.drawView()

    def setState(self, state, enable):
        """
        Calls `super().setState(aState, enable)` to change the `ListViewer`
        object's state. Depending on the `state` argument, this can result in
        displaying or hiding the view.

        Additionally, if `state` is `sfSelected` and `sfActive`, the
        scroll bars are redrawn; if `state` is `sfSelected` but not
        `sfActive`, the scroll bars are hidden.

        :param state: State to set
        :param enable: Enable or disable the state
        """
        super().setState(state, enable)

        if state & (sfSelected | sfActive | sfVisible):
            if self.hScrollBar:
                if self.getState(sfActive) and self.getState(sfVisible):
                    self.hScrollBar.show()
                else:
                    self.hScrollBar.hide()
            if self.vScrollBar:
                if self.getState(sfActive) and self.getState(sfVisible):
                    self.vScrollBar.show()
                else:
                    self.vScrollBar.hide()
            self.drawView()

    def focusItemNum(self, item):
        """
        Used internally by `focusItem()`. Makes the given item focused by
        setting the `focused` data member to `item`.

        :param item: Item to focus
        """
        if item < 0:
            item = 0
        else:
            if item >= self._range > 0:
                item = self._range - 1

        if self._range != 0:
            self.focusItem(item)

    def shutdown(self):
        self.hScrollBar = None
        self.vScrollBar = None
        super().shutdown()

    def __handleKeyDownEvent(self, event):
        if event.keyDown.charScan.charCode == ' ' and self.focused < self._range:
            self.selectItem(self.focused)
            newItem = self.focused
        else:
            kc = ctrlToArrow(event.keyDown.keyCode)
            if kc == kbUp:
                newItem = self.focused - 1
            elif kc == kbDown:
                newItem = self.focused + 1
            elif kc == kbRight:
                if self.numCols > 1:
                    newItem = self.focused + self.size.y
                else:
                    return
            elif kc == kbLeft:
                if self.numCols > 1:
                    newItem = self.focused - self.size.y
                else:
                    return
            elif kc == kbPgDn:
                newItem = self.focused + self.size.y * self.numCols
            elif kc == kbPgUp:
                newItem = self.focused - self.size.y * self.numCols
            elif kc == kbHome:
                newItem = self.topItem
            elif kc == kbEnd:
                newItem = self.topItem + (self.size.y * self.numCols) - 1
            elif kc == kbCtrlPgDn:
                newItem = self._range - 1
            elif kc == kbCtrlPgUp:
                newItem = 0
            else:
                return
        self.focusItemNum(newItem)
        self.drawView()
        self.clearEvent(event)

    def __handleMouseEvent(self, event, mouseAutosToSkip):
        colWidth = self.size.x // self.numCols + 1
        oldItem = self.focused
        mouse = self.makeLocal(event.mouse.where)
        if self.mouseInView(event.mouse.where):
            newItem = mouse.y + (self.size.y * (mouse.x // colWidth)) + self.topItem
        else:
            newItem = oldItem
        count = 0
        mouseIsDown = True
        while mouseIsDown:
            if newItem != oldItem:
                self.focusItemNum(newItem)
                self.drawView()
            oldItem = newItem
            mouse = self.makeLocal(event.mouse.where)

            if self.mouseInView(event.mouse.where):
                newItem = mouse.y + (self.size.y * (mouse.x // colWidth)) + self.topItem
            else:
                if self.numCols == 1:
                    if event.what == evMouseAuto:
                        count += 1
                    if count == mouseAutosToSkip:
                        count = 0
                        if mouse.y < 0:
                            newItem = self.focused - 1
                        elif mouse.y > self.size.y:
                            newItem = self.focused + 1
                else:
                    if event.what == evMouseAuto:
                        count += 1
                    if count == mouseAutosToSkip:
                        count = 0
                        if mouse.x < 0:
                            newItem = self.focused - self.size.y
                        elif mouse.x >= self.size.x:
                            newItem = self.focused + self.size.y
                        elif mouse.y < 0:
                            newItem = self.focused - (self.focused % self.size.y)
                        elif mouse.y > self.size.y:
                            newItem = self.focused - (self.focused % self.size.y) + self.size.y - 1
            if event.mouse.eventFlags & meDoubleClick:
                break
            mouseIsDown = (self.mouseEvent(event, evMouseMove | evMouseAuto))
        self.focusItemNum(newItem)
        self.drawView()
        if event.mouse.eventFlags & meDoubleClick and self._range > newItem:
            self.selectItem(newItem)
        self.clearEvent(event)
