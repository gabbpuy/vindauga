# -*- coding: utf-8 -*-
import logging

from vindauga.constants.grow_flags import gfGrowHiX
from vindauga.constants.option_flags import ofPreProcess
from vindauga.misc.util import nameLength
from vindauga.types.draw_buffer import DrawBuffer
from vindauga.types.rect import Rect
from .menu import Menu
from .menu_view import MenuView

logger = logging.getLogger(__name__)


class MenuBar(MenuView):
    """
    TMenuBar objects represent the horizontal menu bars from which menu
    selections can be made by:
        direct clicking
    * F10 selection and hot keys
    * selection (highlighting) and pressing Enter
    * hot keys
       
    The main menu selections are displayed in the top menu bar. This is
    represented by an object of type `MenuBar`, usually owned by your
    `Application` object.
       
    Submenus are displayed in objects of type `MenuBox`. Both `MenuBar`
    and `MenuBox` are derived from `MenuView` (which is in turn derived
    from `View`).
       
    For most vindauga applications, you will not be involved directly with menu
    objects. By overriding `Application.initMenuBar()` with a suitable
    set of nested new `MenuItem` and `Menu` calls, vindauga takes
    care of all the standard menu mechanisms.

    Palette layout
    1 = Normal text
    2 = Disabled text
    3 = Shortcut text
    4 = Normal selection
    5 = Disabled selection
    6 = Shortcut selection
    """
    name = 'MenuBar'

    def __init__(self, bounds, menu):
        super().__init__(bounds)
        if isinstance(menu, Menu):
            self.menu = menu
        else:
            self.menu = Menu(menu)

        self.growMode = gfGrowHiX
        self.options |= ofPreProcess

    def _chooseColor(self, p):
        cNormal = self.getColor(0x0301)
        cSelect = self.getColor(0x0604)
        cNormDisabled = self.getColor(0x0202)
        cSelDisabled = self.getColor(0x0505)

        if p.disabled:
            if p is self._current:
                color = cSelDisabled
            else:
                color = cNormDisabled
        else:
            if p is self._current:
                color = cSelect
            else:
                color = cNormal
        return color

    def draw(self):
        """
        Draws the menu bar with the default palette. The `MenuItem.name`
        and `MenuItem.disabled` data members of each `MenuItem`
        object in the menu linked list are read to give the menu legends in
        the correct colors.

        The current (selected) item is highlighted.
        """
        b = DrawBuffer()
        cNormal = self.getColor(0x0301)
        b.moveChar(0, ' ', cNormal, self.size.x)
        if self.menu and self.menu.items:
            x = 1
            items = (item for item in self.menu.items if item.name)
            for p in items:
                nameLen = nameLength(p.name)
                if x + nameLen < self.size.x:
                    color = self._chooseColor(p)
                    b.moveChar(x, ' ', color, 1)
                    b.moveCStr(x + 1, p.name, color)
                    b.moveChar(x + nameLen + 1, ' ', color, 1)
                x += (nameLen + 2)
        self.writeBuf(0, 0, self.size.x, 1, b)

    def getItemRect(self, item):
        """
        Returns the rectangle occupied by the given menu item. It can be used
        with `mouseInView()` to determine if a mouse click has occurred on
        a given menu selection.

        :param item: Menu item to find
        :return: `Rect` of the `Menu` item
        """
        r = Rect(1, 0, 1, 1)
        for p in self.menu.items:
            r.topLeft.x = r.bottomRight.x
            if p.name:
                r.bottomRight.x += (nameLength(p.name) + 2)
            if p is item:
                return r
        return r
