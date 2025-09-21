# -*- coding: utf-8 -*-
from __future__ import annotations
from enum import Enum, auto
import logging
from typing import List, Optional, Union, Tuple

from vindauga.constants.command_codes import cmMenu, hcNoContext, cmCommandSetChanged
import vindauga.constants.event_codes as event_codes
import vindauga.constants.keys as keys
from vindauga.events.event import Event
from vindauga.utilities.input.character_codes import getAltChar
from vindauga.utilities.input.key_utils import ctrlToArrow
from vindauga.types.palette import Palette
from vindauga.types.point import Point
from vindauga.types.rect import Rect
from vindauga.types.view import View
from .menu import Menu

from .menu_item import MenuItem

logger = logging.getLogger(__name__)


class MenuAction(Enum):
    doNothing = auto()
    doSelect = auto()
    doReturn = auto()


class MenuView(View):
    """
    `MenuView` provides an abstract base from which menu bar and menu box
    classes (either pull down or pop up) are derived. You cannot instantiate a
    `MenuView` itself.

    Palette layout
    1 = Normal text
    2 = Disabled text
    3 = Shortcut text
    4 = Normal selection
    5 = Disabled selection
    6 = Shortcut selection
    """
    name = 'MenuView'

    cpMenuView = "\x02\x03\x04\x05\x06\x07"

    def __init__(self, bounds: Rect, menu=None, parent: Optional[MenuView] = None):
        super().__init__(bounds)
        self._parentMenu = parent
        self._current = None
        self.menu = menu
        self.eventMask |= event_codes.evBroadcast

    @staticmethod
    def newSubView(bounds: Rect, menu, parentMenu) -> 'MenuBox':
        from .menu_box import MenuBox
        return MenuBox(bounds, menu, parentMenu)

    def getItemRect(self, item: MenuItem) -> Rect:
        """
        Classes derived from `MenuView` must override this member function in
        order to respond to mouse events. Your overriding functions in derived
        classes must return the rectangle occupied by the given menu item.

        :param item: Item to rect to return 
        :return: `Rect` with the item bounds
        """
        return Rect(0, 0, 0, 0)

    def execute(self) -> int:
        """
        Executes a menu view until the user selects a menu item or cancels the
        process. Returns the command assigned to the selected menu item, or
        zero if the menu was canceled.
       
        Should never be called except by `Group.execView()`.
        """
        autoSelect = False
        result = 0
        itemShown = None
        e = Event(event_codes.evNothing)
        self._current = self.menu.default
        action = MenuAction.doNothing

        while action != MenuAction.doReturn:
            action = MenuAction.doNothing
            self.getEvent(e)
            what = e.what
            if what == event_codes.evMouseDown:
                if self.mouseInView(e.mouse.where) or self.__mouseInOwner(e):
                    self.__trackMouse(e)
                    if self.size.y == 1:
                        autoSelect = True
                else:
                    action = MenuAction.doReturn
            elif what == event_codes.evMouseUp:
                action = self.__handleMouseUp(action, e)
            elif what == event_codes.evMouseMove:
                if e.mouse.buttons:
                    self.__trackMouse(e)
                    if not (self.mouseInView(e.mouse.where) or self.__mouseInOwner(e)) and self.__mouseInMenus(e):
                        action = MenuAction.doReturn
            elif what == event_codes.evKeyDown:
                action, autoSelect, result = self.__handleEventKeyDown(action, autoSelect, e, result)
            elif what == event_codes.evCommand:
                if e.message.command == cmMenu:
                    autoSelect = False
                    if self._parentMenu:
                        action = MenuAction.doReturn
                else:
                    action = MenuAction.doReturn

            if itemShown != self._current:
                itemShown = self._current
                self.drawView()

            result = self.__handleMenuAction(action, autoSelect, e, result)

            if result and self.commandEnabled(result):
                action = MenuAction.doReturn
                self.clearEvent(e)
            else:
                result = 0

        if e.what != event_codes.evNothing and (self._parentMenu or e.what == event_codes.evCommand):
            self.putEvent(e)

        if self._current:
            self.menu.default = self._current
            self._current = None
            self.drawView()

        return result

    def findItem(self, ch: Union[str, int]) -> Optional[MenuItem]:
        """
        Returns a pointer to the menu item that has code.upper() as its hot key
        (the highlighted character). Returns None if no such menu item is found or
        if the menu item is disabled. Note that `findItem()` is case-insensitive.

        :param ch: Hot key character
        :return: `MenuItem` object
        """
        if not (self.menu.items and ch):
            return None

        if isinstance(ch, int):
            ch = chr(ch)
        ch = ch.upper()
        enabledMenus = (m for m in self.menu.items if m.name and not m.disabled and '~' in m.name)
        for m in enabledMenus:
            if ch == m.name.partition('~')[-1][0].upper():
                return m
        return None

    def getHelpCtx(self) -> int:
        """
        By default, this member function returns the help context of the
        current menu selection. If this is `hcNoContext`, the parent menu's
        current context is checked. If there is no parent menu, `getHelpCtx()`
        returns `hcNoContext`.

        :return: Help Context 
        """
        c = self

        while c and (not c._current or c._current.helpCtx == hcNoContext or not c._current.name):
            c = c._parentMenu

        if c:
            return c._current.helpCtx
        return hcNoContext

    def getPalette(self) -> Palette:
        palette = Palette(self.cpMenuView)
        return palette

    def updateMenu(self, menu: Menu) -> bool:
        res = False
        if menu:
            items = (p for p in menu.items if p.name)
            for p in items:
                if not p.command:
                    if p.subMenu and self.updateMenu(p.subMenu):
                        res = True
                else:
                    commandState = self.commandEnabled(p.command)
                    if p.disabled == commandState:
                        p.disabled = not commandState
                        res = True
        return res

    def executeMenu(self, event: Event):
        self.putEvent(event)
        emc = self.owner.execView(self)
        if emc and self.commandEnabled(emc):
            event.what = event_codes.evCommand
            event.message.command = emc
            event.message.infoPtr = None
            self.putEvent(event)
        self.clearEvent(event)

    def handleEvent(self, event: Event):
        if self.menu:
            what = event.what
            if what == event_codes.evMouseDown:
                self.executeMenu(event)
            elif what == event_codes.evKeyDown:
                if self.findItem(getAltChar(event.keyDown.keyCode)):
                    self.executeMenu(event)
                else:
                    p = self.hotKey(event.keyDown.keyCode)
                    if p and self.commandEnabled(p.command):
                        event.what = event_codes.evCommand
                        event.message.command = p.command
                        event.message.infoPtr = None
                        self.putEvent(event)
                        self.clearEvent(event)
            elif what == event_codes.evCommand:
                if event.message.command == cmMenu:
                    self.executeMenu(event)
            elif what == event_codes.evBroadcast:
                if event.message.command == cmCommandSetChanged:
                    if self.updateMenu(self.menu):
                        self.drawView()

    def findHotKey(self, items: List[MenuItem], keyCode) -> Optional[MenuItem]:
        if items:
            items = (p for p in items if p.name)
            for p in items:
                if p.subMenu:
                    T = self.findHotKey(p.subMenu.items, keyCode)
                    if T:
                        return T
                elif (not p.disabled) and p.keyCode != keys.kbNoKey and p.keyCode == keyCode:
                    return p
        return None

    def hotKey(self, keyCode) -> MenuItem:
        """
        Returns a pointer to the menu item associated with the hot key given
        by `keyCode`. Returns None if no such menu item exists, or if the item is
        disabled. `hotKey()` is used by `handleEvent()` to determine whether a
        keystroke event selects an item in the menu.

        :param keyCode: keyCode to search for
        :return: `MenuItem` object or None
        """
        return self.findHotKey(self.menu.items, keyCode)

    def __handleMouseUp(self, action: MenuAction, e: Event) -> MenuAction:
        mouseActive = self.__trackMouse(e)
        if self.__mouseInOwner(e):
            self._current = self.menu.default
        elif self._current and self._current.name:
            action = MenuAction.doSelect
        elif mouseActive:
            action = MenuAction.doReturn
        else:
            self._current = self.menu.default
            if not self._current:
                self._current = self.menu.items
            action = MenuAction.doNothing
        return action

    def __handleEventKeyDown(self, action: MenuAction, autoSelect: bool, e: Event, 
                             result: int) -> Tuple[MenuAction, bool, int]:
        cta = ctrlToArrow(e.keyDown.keyCode)
        if cta in {keys.kbUp, keys.kbDown}:
            if self.size.y != 1:
                self.__trackKey(cta == keys.kbDown)
            elif e.keyDown.keyCode == keys.kbDown:
                autoSelect = True
        elif cta in {keys.kbLeft, keys.kbRight}:
            if not self._parentMenu:
                self.__trackKey(cta == keys.kbRight)
            elif cta == keys.kbRight and not self._current.command:
                action = MenuAction.doSelect
            else:
                action = MenuAction.doReturn
        elif cta in {keys.kbHome, keys.kbEnd}:
            if self.size.y != 1:
                self._current = self.menu.items
                if e.keyDown.keyCode == keys.kbEnd:
                    self.__trackKey(False)
        elif cta == keys.kbEnter:
            if self.size.y == 1:
                autoSelect = True
            action = MenuAction.doSelect
        elif cta == keys.kbEsc:
            action = MenuAction.doReturn
            if not self._parentMenu or (self._parentMenu.size.y != 1):
                self.clearEvent(e)
        else:
            target = self
            ch = getAltChar(e.keyDown.keyCode)
            if not ch:
                ch = e.keyDown.charScan.charCode
            else:
                target = self.__topMenu()

            p = target.findItem(ch)

            if not p:
                p = self.__topMenu().hotKey(e.keyDown.keyCode)
                if p and self.commandEnabled(p.command):
                    result = p.command
                    action = MenuAction.doReturn
            elif target is self:
                if self.size.y == 1:
                    autoSelect = True
                action = MenuAction.doSelect
                self._current = p
            elif self._parentMenu is not target or self._parentMenu._current is not p:
                action = MenuAction.doReturn
        return action, autoSelect, result

    def __handleMenuAction(self, action: MenuAction, autoSelect: bool, e: Event, result: int) -> int:
        if ((action == MenuAction.doSelect or (action == MenuAction.doNothing and autoSelect))
                and (self._current and self._current.name)):
            if not self._current.command:
                if e.what & (event_codes.evMouseDown | event_codes.evMouseMove):
                    self.putEvent(e)

                r = self.getItemRect(self._current)
                r.topLeft.x += self.origin.x
                r.topLeft.y = self.origin.y + r.bottomRight.y
                r.bottomRight = Point(self.owner.size.x, self.owner.size.y)

                if self.size.y == 1:
                    r.topLeft.x -= 1

                target = self.__topMenu().newSubView(r, self._current.subMenu, self)
                result = self.owner.execView(target)
                self.destroy(target)
            elif action == MenuAction.doSelect:
                result = self._current.command
        return result

    def __trackMouse(self, e: Event) -> bool:
        mouse = self.makeLocal(e.mouse.where)
        # Because any bails if the first thing matches... self._current will point to the thing that
        # matches

        if self.menu.items:
            if any(mouse in self.getItemRect(self._current) for self._current in self.menu.items):
                return True
        self._current = None
        return False

    def __nextItem(self):
        """
        idx = (self.menu.items.index(self._current) + 1) % len(self.menu.items)
        self._current = self.menu.items[idx]
        """
        self._current = self._current.next
        if not self._current:
            self._current = self.menu.items

    def __prevItem(self):
        """
        idx = (self.menu.items.index(self._current) - 1) % len(self.menu.items)
        self._current = self.menu.items[idx]
        """
        p = self._current
        if p is self.menu.items:
            p = None
        self.__nextItem()
        while self._current.next is not p:
            self.__nextItem()

    def __trackKey(self, findNext: bool):
        if not self._current:
            return

        action = self.__nextItem if findNext else self.__prevItem
        done = False
        while not done:
            action()
            done = bool(self._current.name)

    def __mouseInOwner(self, e: Event) -> bool:
        if not self._parentMenu or self._parentMenu.size.y != 1:
            return False

        mouse = self._parentMenu.makeLocal(e.mouse.where)
        r = self._parentMenu.getItemRect(self._parentMenu._current)
        return mouse in r

    def __mouseInMenus(self, e: Event) -> bool:
        p = self._parentMenu
        while p and not p.mouseInView(e.mouse.where):
            p = p.parentMenu
        return p is not None

    def __topMenu(self) -> MenuView:
        p = self
        while p._parentMenu:
            p = p._parentMenu
        return p
