# -*- coding:utf-8 -*-
from vindauga.constants.option_flags import ofCentered
from vindauga.constants.window_flags import wfGrow
from vindauga.types.rect import Rect
from vindauga.widgets.application import Application
from vindauga.widgets.input_line import InputLine
from vindauga.widgets.scroll_dialog import ScrollDialog
from vindauga.widgets.scroll_group import sbVerticalBar
from vindauga.widgets.static_text import StaticText


class Demo(Application):
    def __init__(self):
        super().__init__()
        dlg = ScrollDialog(Rect(0, 0, 40, 10), 'Test Dialog', sbVerticalBar)
        dlg.options |= ofCentered
        dlg.flags |= wfGrow

        for x in range(40):
            if x % 10:
                n = x + 1
                ctrlString = 'Control {:02d}'.format(n)
                dlg.scrollGroup.insert(StaticText(Rect(0, x, 10, x + 1), ctrlString))
            else:
                dlg.scrollGroup.insert(InputLine(Rect(0, x, 10, x + 1), 20))

        dlg.scrollGroup.selectNext(False)
        dlg.scrollGroup.setLimit(0, 40)

        if self.validView(dlg):
            self.desktop.execView(dlg)
            self.destroy(dlg)


if __name__ == '__main__':
    app = Demo()
    app.run()
