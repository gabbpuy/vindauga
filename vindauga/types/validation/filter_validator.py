# -*- coding: utf-8 -*-
from vindauga.constants.message_flags import mfError, mfOKButton
from vindauga.dialogs.message_box import messageBox
from .validator import Validator


class FilterValidator(Validator):
    """
    Filter validator objects check an input field as the user types into it.
    The validator holds a set of allowed characters. If the user types one of
    the legal characters, the filter validator indicates that the character is
    valid.

    If the user types any other character, the validator indicates that the
    input is invalid.
    """
    errorMsg = _('Invalid character in input')

    def __init__(self, validChars):
        super().__init__()
        self.validChars = validChars

    def isValid(self, s: str) -> bool:
        return all(c in self.validChars for c in s)

    def isValidInput(self, item, _flag) -> bool:
        return self.isValid(item)

    def error(self):
        messageBox(self.errorMsg, mfError, (mfOKButton,))
