# -*- coding:utf-8 -*-
import logging

from vindauga.constants.option_flags import ofCentered
from vindauga.constants.window_flags import wfGrow
from vindauga.types.rect import Rect
from vindauga.widgets.application import Application
from vindauga.widgets.button import Button
from vindauga.widgets.flex_box import FlexBox, GrowDirection
from vindauga.widgets.scroll_dialog import Dialog


class FlexBoxDemo(Application):
    def __init__(self):
        super().__init__()
        dlg = Dialog(Rect(0, 0, 40, 30), 'Test Dialog')
        dlg.options |= ofCentered
        dlg.flags |= wfGrow
        box = FlexBox(Rect(1, 1, 38, 28), GrowDirection.GrowVertical)
        dlg.insert(box)
        topBox = FlexBox(Rect(1, 1, 1, 1), GrowDirection.GrowHorizontal)
        bottomBox = FlexBox(Rect(1, 1, 1, 1), GrowDirection.GrowVertical)

        for x in range(4):
            ctrlString = f'T{x:02d}'
            widget = Button(Rect(0, 0, 1, 1), ctrlString, 0, 0)
            topBox.insert(widget)
            ctrlString = f'B{x:02d}'
            widget = Button(Rect(0, 0, 1, 3), ctrlString, 0, 0)
            bottomBox.insert(widget)

        box.insert(topBox)
        box.insert(bottomBox)

        if self.validView(dlg):
            self.desktop.execView(dlg)
            self.destroy(dlg)


def setupLogging():
    logger = logging.getLogger('vindauga')
    logger.propagate = False
    format = "%(name)s\t %(message)s"
    logger.setLevel(logging.DEBUG)
    handler = logging.StreamHandler(open('vindauga.log', 'wt'))
    handler.setFormatter(logging.Formatter(format))
    logger.addHandler(handler)


if __name__ == '__main__':
    setupLogging()
    app = FlexBoxDemo()
    app.run()
