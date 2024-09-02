# -*- coding: utf-8 -*-
from .validator import Validator


class LookupValidator(Validator):

    def isValid(self, item) -> bool:
        return self.lookup(item)

    def lookup(self, item) -> bool:
        return False
