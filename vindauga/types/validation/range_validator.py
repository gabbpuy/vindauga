# -*- coding: utf-8 -*-
from gettext import gettext as _
import logging

from vindauga.constants.message_flags import mfError, mfOKButton
from vindauga.constants.validation_constants import voTransfer, vtGetData, vtSetData
from vindauga.dialogs.message_box import messageBox
from .validator import Validator

logger = logging.getLogger(__name__)


class RangeValidator(Validator):
    """
    A range validator object determines whether the data typed by a user falls
    within a designated range of integers.
    """
    validUnsignedChars = "+0123456789"
    validSignedChars = "+-0123456789"
    errorMsg = _('Value not in the range {} to {}')

    def __init__(self, min_, max_):
        super().__init__()

        self.min = min_
        self.max = max_

        if min_ >= 0:
            self.validChars = self.validUnsignedChars
        else:
            self.validChars = self.validSignedChars

    def error(self):
        messageBox(self.errorMsg.format(self.min, self.max), mfError, (mfOKButton,))

    def isValid(self, s) -> bool:
        try:
            value = int(s)
            return self.min <= value <= self.max
        except:
            pass
        return False

    def transfer(self, item, args, operation: int):
        if self.options & voTransfer:
            if operation == vtGetData:
                try:
                    int(item)
                    return False
                except ValueError:
                    return True
            if operation == vtSetData:
                return str(args)
        else:
            return False
