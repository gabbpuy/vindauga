# -*- coding: utf-8 -*-
from gettext import gettext as _

from vindauga.constants.message_flags import mfError, mfOKButton
from vindauga.dialogs.message_box import messageBox
from .lookup_validator import LookupValidator


class StringLookupValidator(LookupValidator):

    errorMsg = _('Input is not in list of valid strings')

    def __init__(self, collection):
        super().__init__()
        self.strings = collection

    def error(self):
        messageBox(self.errorMsg, mfError, [mfOKButton])

    def lookup(self, s: str) -> bool:
        return s in self.strings

    def newStringList(self, collection):
        self.strings = collection
