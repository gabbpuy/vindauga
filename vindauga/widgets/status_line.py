# -*- coding: utf-8 -*-
import logging

from vindauga.constants.command_codes import cmCommandSetChanged, hcNoContext
from vindauga.constants.grow_flags import gfGrowLoY, gfGrowHiX, gfGrowHiY
from vindauga.constants.event_codes import evBroadcast, evMouseDown, evMouseMove, evCommand, evKeyDown
from vindauga.constants.option_flags import ofPreProcess
from vindauga.misc.util import nameLength
from vindauga.types.draw_buffer import DrawBuffer
from vindauga.types.palette import Palette
from vindauga.events.event import Event
from vindauga.types.view import View

logger = logging.getLogger(__name__)


class StatusLine(View):
    """
    The `StatusLine` object is a specialized view, usually displayed at the
    bottom of the screen. Typical status line displays are lists of available
    hot keys, displays of available memory, time of day, current edit modes,
    and hints for users.
       
    Status line items are `StatusItem` objects which contain data members
    for a text string to be displayed on the status line, a key code to bind
    a hot key, and a command to be generated if the displayed text is clicked
    on with the mouse or the hot key is pressed.

    The `ofPreProcess` bit in `options` is set, `eventMask` is
    set to include `evBroadcast`, and `growMode` is set to
     `gfGrowLoY | gfGrowHiX | @gfGrowHiY`.

    Palette layout
    1 = Normal text
    2 = Disabled text
    3 = Shortcut text
    4 = Normal selection
    5 = Disabled selection
    6 = Shortcut selection
    """
    name = 'StatusLine'
    cpStatusLine = '\x02\x03\x04\x05\x06\x07'
    hintSeparator = '│ '

    def __init__(self, bounds, defs):
        super().__init__(bounds)
        self.options |= ofPreProcess
        self.eventMask |= evBroadcast
        self.growMode = gfGrowLoY | gfGrowHiX | gfGrowHiY
        self._items = []
        self._itemCodes = {}
        self._defs = defs
        self.__findItems()

    @staticmethod
    def hint(helpContext):
        """
        By default, `hint()` returns an empty string. Override it to provide a
        context-sensitive hint string for the `helpContext' argument. A non-empty
        string will be drawn on the status line after a divider bar.

        :param helpContext: Help context to display a hint for
        """
        return ''

    def draw(self):
        """
        Draws the status line by writing the text string for each status item
        that has one, then any hints defined for the current help context,
        following a divider bar. Uses the appropriate palettes depending on
        each item's status.
        """
        self.__drawSelect(None)

    def getPalette(self):
        palette = Palette(self.cpStatusLine)
        return palette

    def handleEvent(self, event):
        """
        Handles events sent to the status line by calling
        `super().handleEvent()`, then checking for three kinds of special
        events.
       
        - Mouse clicks that fall within the rectangle occupied by any status
          item generate a command event, with event.what set to the command in
          that status item.
        - Key events are checked against the keyCode data member in each
          item; a match causes a command event with that item's command.
        - Broadcast events with the command cmCommandSetChanged cause the
          status line to redraw itself to reflect any hot keys that might have
          been enabled or disabled.

        :param event: The event to handle
        """
        super().handleEvent(event)

        what = event.what
        item = None
        if what == evMouseDown:
            processing = True
            while processing:
                mouse = self.makeLocal(event.mouse.where)
                if item is not self.__itemMouseIsIn(mouse):
                    item = self.__itemMouseIsIn(mouse)
                    self.__drawSelect(item)
                processing = self.mouseEvent(event, evMouseMove)

            if item and self.commandEnabled(item.command):
                e = Event(evCommand)
                e.message.command = item.command
                e.message.infoPtr = None
                self.putEvent(e)
                logger.info(event)
                self.drawView()
                return
            self.clearEvent(event)
            self.drawView()
        elif what == evKeyDown:
            item = self._itemCodes.get(event.keyDown.keyCode)
            if item and self.commandEnabled(item.command):
                e = Event(evCommand)
                e.message.command = item.command
                e.message.infoPtr = None
                self.putEvent(e)
                self.drawView()
                return
        elif what == evBroadcast:
            if event.message.command == cmCommandSetChanged:
                self.drawView()

    def update(self):
        """
        Updates the status line by selecting the correct items from the lists
        in `defs` data member, depending on the current help context.
       
        Then calls `drawView()` to redraw the status line if the items have
        changed.
        """
        p = self.TopView
        h = hcNoContext
        if p:
            h = p.getHelpCtx()

        if self.helpCtx != h:
            self.helpCtx = h
            self.__findItems()
            self.drawView()

    def __itemMouseIsIn(self, mouse):
        if mouse.y != 0:
            return None
        i = 0
        for item in self._items:
            if item.text:
                k = i + nameLength(item.text) + 2
                if i <= mouse.x < k:
                    return item
                i = k
        return None

    def __drawSelect(self, selected):
        b = DrawBuffer()
        cNormal = self.getColor(0x0301)
        cSelect = self.getColor(0x0604)
        cNormDisabled = self.getColor(0x0202)
        cSelDisabled = self.getColor(0x0505)

        b.moveChar(0, ' ', cNormal, self.size.x)
        i = 0

        textItems = (item for item in self._items if item.text)
        for item in textItems:
            textLen = nameLength(item.text)
            if i + textLen < self.size.x:
                if self.commandEnabled(item.command):
                    if item is selected:
                        color = cSelect
                    else:
                        color = cNormal
                else:
                    if item is selected:
                        color = cSelDisabled
                    else:
                        color = cNormDisabled

                b.moveChar(i, ' ', color, 1)
                b.moveCStr(i + 1, item.text, color)
                b.moveChar(i + textLen + 1, ' ', color, 1)
            i += textLen + 2

        if i < self.size.x - 2:
            hintBuf = self.hint(self.helpCtx)
            if hintBuf:
                b.moveStr(i, self.hintSeparator, cNormal)
                i += len(self.hintSeparator)
                if len(hintBuf) + i > self.size.x:
                    hintBuf = hintBuf[:self.size.x - i]

                b.moveStr(i, hintBuf, cNormal)
                i += len(hintBuf)

        self.writeLine(0, 0, self.size.x, 1, b)

    def __findItems(self):
        p = self._defs
        while p and (self.helpCtx < p.min or self.helpCtx > p.max):
            p = p.next
        self._items = list(p) if p else []
        self._itemCodes = {p.keyCode: p for p in self._items}
