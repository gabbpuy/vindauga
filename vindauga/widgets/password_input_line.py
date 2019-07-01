# -*- coding: utf-8 -*-

from .input_line import InputLine


class PasswordInputLine(InputLine):

    def draw(self):
        password = self.getDataString()
        self.setData('*' * len(password))
        super().draw()
        self.setData(password)
