# -*- coding: utf-8 -*-


class Validator:

    def __init__(self):
        self.status = 0
        self.options = 0

    def error(self):
        pass

    def isValidInput(self, item, flag) -> bool:
        return True

    def isValid(self, item) -> bool:
        return True

    def transfer(self, item, args, operation) -> bool:
        return False

    def validate(self, item) -> bool:
        if not self.isValid(item):
            self.error()
            return False
        return True
