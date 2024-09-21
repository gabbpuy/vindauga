# -*- coding: utf-8 -*-
from __future__ import annotations
import logging
from typing import Optional

from vindauga.constants.command_codes import hcNoContext
from vindauga.types.view import View

logger = logging.getLogger(__name__)


class MenuItem:
    """
    Instances of `MenuItem` serve as elements of a menu.
       
    They can be individual menu items that cause a command to be generated or
    a `SubMenu` pull-down menu that contains other `MenuItem` instances.
    `MenuItem` also serves as a base class for `SubMenu`.
    """

    def __init__(self, name: str, command: int, keyCode: int, helpCtx: int = hcNoContext, params=None,
                 subMenu: Optional['SubMenu'] = None, nextItem: Optional[MenuItem] = None):
        self.name = name
        self.command = command
        self.disabled = not View.commandEnabled(command)
        self.keyCode = keyCode
        self.helpCtx = helpCtx
        # Used to display the hot key for this menu
        self.param = params
        # Points to a submenu to be created when this item is selected if a command is not generated.
        self.subMenu = subMenu
        self.next = nextItem

    def append(self, nextItem: MenuItem):
        """
        Appends the given `MenuItem` to the list of `MenuItems` by setting
        @ref next data member to `nextItem`.

        :param nextItem: The next menu items
        """
        self.next = nextItem

    @staticmethod
    def newLine() -> MenuItem:
        return MenuItem('', 0, 0, hcNoContext)

    def __contains__(self, item: MenuItem) -> bool:
        cur = self
        while cur:
            if cur is item:
                return True
            cur = cur.next
        return False

    def __iter__(self):
        cur = self
        while cur:
            yield cur
            cur = cur.next

    def __repr__(self):
        return f'<MenuItem: {id(self):X} - {self.name} {self.command} [{self.disabled} - {self.keyCode:X}]>'
