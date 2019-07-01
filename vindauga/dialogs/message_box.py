# -*- coding: utf-8 -*-
from vindauga.constants.buttons import bfNormal
from vindauga.constants.command_codes import (cmYes, cmNo, cmOK,
                                              cmCancel)
from vindauga.constants.message_flags import mfYesButton, mfNoButton, mfOKButton, mfCancelButton
from vindauga.types.rect import Rect
from vindauga.widgets.button import Button
from vindauga.widgets.dialog import Dialog
from vindauga.widgets.program import getDesktopSize, execView
from vindauga.widgets.static_text import StaticText


class MsgBoxText:
    yesText = _('~Y~es')
    noText = _('~N~o')
    okText = _('O~K~')
    cancelText = _('Cancel')
    warningText = _('Warning')
    errorText = _('Error')
    informationText = _('Information')
    confirmText = _('Confirm')


BUTTONS = {
    mfYesButton: (MsgBoxText.yesText, cmYes),
    mfNoButton: (MsgBoxText.noText, cmNo),
    mfOKButton: (MsgBoxText.okText, cmOK),
    mfCancelButton: (MsgBoxText.cancelText, cmCancel)
}

TITLES = (
    MsgBoxText.warningText,
    MsgBoxText.errorText,
    MsgBoxText.informationText,
    MsgBoxText.confirmText
)


def messageBoxRect(r, msg, messageType, buttons):

    dialog = Dialog(r, TITLES[messageType])

    dialog.insert(
        StaticText(Rect(3, 2, dialog.size.x - 2, dialog.size.y - 3), msg))

    x = -2

    buttons = (BUTTONS[b] for b in sorted(buttons))
    buttonList = [Button(Rect(0, 0, 10, 2), button[0], button[1], bfNormal) for button in buttons]
    x += sum((2 + b.size.x) for b in buttonList)
    x = (dialog.size.x - x) // 2
    for b in buttonList:
        dialog.insert(b)
        b.moveTo(x, dialog.size.y - 3)
        x += b.size.x + 2
    dialog.selectNext(False)
    return execView(dialog)


def makeRect():
    r = Rect(0, 0, 40, 9)
    size = getDesktopSize()
    r.move((size.x - r.bottomRight.x) // 2,
           (size.y - r.bottomRight.y) // 2)
    return r


def messageBox(msg, messageType, buttons):
    return messageBoxRect(makeRect(), msg, messageType, buttons)
