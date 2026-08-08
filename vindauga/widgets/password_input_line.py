# -*- coding: utf-8 -*-

from .input_line import InputLine


class PasswordInputLine(InputLine):

    def draw(self):
        password = self.current.data
        self.current.data = list('*' * len(password))
        try:
            super().draw()
        finally:
            self.current.data = password
