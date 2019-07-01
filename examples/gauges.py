# -*- coding: utf-8 -*-
import math
import time

from vindauga.constants.command_codes import cmQuit, hcNoContext
from vindauga.constants.window_flags import wfClose
from vindauga.constants.keys import kbAltF, kbAltX
from vindauga.constants.option_flags import ofCentered
from vindauga.menus.menu_bar import MenuBar
from vindauga.menus.menu_item import MenuItem
from vindauga.menus.sub_menu import SubMenu
from vindauga.types.rect import Rect
from vindauga.types.status_def import StatusDef
from vindauga.types.status_def import StatusItem
from vindauga.widgets.application import Application
from vindauga.widgets.dialog import Dialog
from vindauga.widgets.gauge import Gauge
from vindauga.widgets.param_text import ParamText
from vindauga.widgets.static_text import StaticText
from vindauga.widgets.status_line import StatusLine


class GaugeDialog(Dialog):
    def __init__(self, bounds, title):
        super().__init__(bounds, title)
        self.flags &= ~wfClose
        self.options |= ofCentered
        self.degrees = 0

        self.insert(StaticText(Rect(15, 2, 36, 3), 'Gauge Readings'))
        self.insert(StaticText(Rect(3, 4, 15, 5), 'Gauge #1'))
        self.insert(StaticText(Rect(3, 6, 15, 7), 'Gauge #2'))
        self.insert(StaticText(Rect(3, 8, 15, 9), 'Gauge #3'))

        self.gauge1 = Gauge(Rect(16, 4, 36, 5))
        self.gauge1.setParams(60, 200)
        self.insert(self.gauge1)

        self.gauge2 = Gauge(Rect(16, 6, 36, 7))
        self.gauge2.setParams(120, 200)
        self.insert(self.gauge2)

        self.gauge3 = Gauge(Rect(16, 8, 36, 9))
        self.gauge3.setParams(180, 200)
        self.insert(self.gauge3)

        self.gauge1Value = ParamText(Rect(37, 4, 44, 5))
        self.gauge1Value.setText('%3d', 60)
        self.insert(self.gauge1Value)

        self.gauge2Value = ParamText(Rect(37, 6, 44, 7))
        self.gauge2Value.setText('%3d', 120)
        self.insert(self.gauge2Value)

        self.gauge3Value = ParamText(Rect(37, 8, 44, 9))
        self.gauge3Value.setText('%3d', 180)
        self.insert(self.gauge3Value)

    def update(self):
        tempValue = 100 + 100 * math.sin(self.degrees / 180 * math.pi)
        self.gauge1.setValue(tempValue)
        self.gauge1Value.setText('%3d', tempValue)

        tempValue = 100 + 100 * math.cos((self.degrees + 120) / 180 * math.pi)
        self.gauge2.setValue(tempValue)
        self.gauge2Value.setText('%3d', tempValue)

        tempValue = 100 + 100 * math.sin((self.degrees + 240) / 180 * math.pi)
        self.gauge3.setValue(tempValue)
        self.gauge3Value.setText('%3d', tempValue)

        self.degrees += 2
        self.degrees %= 360


class GaugeApp(Application):
    def __init__(self):
        super().__init__()
        self.lastUpdate = time.time()
        self.gaugeDialog = None
        self.showDialog()

    def initStatusLine(self, bounds):
        bounds.topLeft.y = bounds.bottomRight.y - 1
        return StatusLine(bounds, StatusDef(0, 0xFFFF) + StatusItem('~Alt+X~ Exit', kbAltX, cmQuit))

    def initMenuBar(self, bounds):
        bounds.bottomRight.y = bounds.topLeft.y + 1
        return MenuBar(bounds,
                       SubMenu('~F~ile', kbAltF) +
                       MenuItem('E~x~it', cmQuit, kbAltX, hcNoContext, 'Alt+X'))

    def idle(self):
        super().idle()
        now = time.time()
        if now - self.lastUpdate >= .04:
            self.gaugeDialog.update()
            self.lastUpdate = now

    def showDialog(self):
        self.gaugeDialog = GaugeDialog(Rect(15, 4, 65, 18), 'Some gauges')
        self.desktop.insert(self.gaugeDialog)


if __name__ == '__main__':
    app = GaugeApp()
    app.run()

