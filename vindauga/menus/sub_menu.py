# -*- coding: utf-8 -*-
import logging
from typing import Union

from vindauga.constants.command_codes import hcNoContext

from .menu import Menu
from .menu_item import MenuItem

logger = logging.getLogger(__name__)


class SubMenu(MenuItem):
    """
    `SubMenu` is a class used to differentiate between different types of
    `MenuItem`: individual menu items and submenus.
       
    `vindauga` supplies the overloaded operator + so you can easily construct
    complete menus without dozens of nested parentheses.
    """
    def __init__(self, name, keyCode, helpCtx=hcNoContext):
        super().__init__(name, 0, keyCode, helpCtx)

    def __repr__(self):
        return "<SubMenu: {0.name}>".format(self)

    def __add__(self, other: Union['SubMenu', MenuItem]):
        if isinstance(other, SubMenu):
            self.__addSubMenu(other)
        elif isinstance(other, MenuItem):
            self.__addMenuItem(other)
        return self

    def __addMenuItem(self, menu: MenuItem):
        sub = self
        while sub.next:
            sub = sub.next

        if not sub.subMenu:
            sub.subMenu = Menu(menu)
        else:
            cur = sub.subMenu.items
            while cur.next:
                cur = cur.next
            cur.next = menu

    def __addSubMenu(self, other: 'SubMenu'):
        cur = self
        while cur.next:
            cur = cur.next
        cur.next = other
