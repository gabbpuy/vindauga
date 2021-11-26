# -*- coding: utf-8 -*-
import logging

logger = logging.getLogger(__name__)


class Menu:
    def __init__(self, itemList=None, theDefault=None):
        self.items = itemList

        if self.items:
            self.default = self.items
        else:
            self.default = theDefault
