# -*- coding: utf-8 -*-
import logging
from typing import Any, Tuple

import wcwidth
from vindauga.constants.buttons import bfDefault, bfNormal
from vindauga.constants.command_codes import cmOK, cmCancel
from vindauga.types.rect import Rect
from vindauga.widgets.button import Button
from vindauga.widgets.dialog import Dialog
from vindauga.widgets.input_line import InputLine
from vindauga.widgets.label import Label
from vindauga.widgets.program import getDesktopSize, execView

from .message_box import MsgBoxText

logger = logging.getLogger(__name__)


def inputBoxRect(bounds: Rect, title: str, aLabel: str, datum: Any, limit: int) -> Tuple[int, Any]:
    dialog = Dialog(bounds, title)
    r = Rect(4 + wcwidth.wcswidth(aLabel), 2, dialog.size.x - 3, 3)
    control = InputLine(r, limit)
    dialog.insert(control)

    r = Rect(2, 2, 3 + wcwidth.wcswidth(aLabel), 3)
    dialog.insert(Label(r, aLabel, control))

    r = Rect(dialog.size.x - 24, dialog.size.y - 4, dialog.size.x - 14, dialog.size.y - 2)

    dialog.insert(Button(r, MsgBoxText.okText, cmOK, bfDefault))

    r.topLeft.x += 12
    r.bottomRight.x += 12
    dialog.insert(Button(r, MsgBoxText.cancelText, cmCancel, bfNormal))

    dialog.selectNext(False)
    dialog.setData([datum])

    c = execView(dialog)
    rec = None
    if c != cmCancel:
        rec = dialog.getData()[0]
    return c, rec


def inputBox(title: str, label: str, datum: Any, limit: int) -> Tuple[int, Any]:
    r = Rect(0, 0, 60, 8)
    size = getDesktopSize()
    r.move((size.x - r.bottomRight.x) // 2,
           (size.y - r.bottomRight.y) // 2)

    return inputBoxRect(r, title, label, datum, limit)
