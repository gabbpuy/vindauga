# -*- coding: utf-8 -*-
import logging
import math
import random
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
from vindauga.widgets.sparkline import Sparkline
from vindauga.widgets.static_text import StaticText
from vindauga.widgets.status_line import StatusLine

logger = logging.getLogger(__name__)


class SparklineDialog(Dialog):
    def __init__(self, bounds, title):
        super().__init__(bounds, title)
        self.flags &= ~wfClose
        self.options |= ofCentered
        self.time = 0

        # Labels
        self.insert(StaticText(Rect(15, 2, 36, 3), 'Sparkline Examples'))
        self.insert(StaticText(Rect(2, 4, 15, 5), 'Sine Wave:'))
        self.insert(StaticText(Rect(2, 6, 15, 7), 'Random Walk:'))
        self.insert(StaticText(Rect(2, 8, 15, 9), 'Stock Price:'))
        self.insert(StaticText(Rect(2, 11, 18, 12), 'Multi-line (3):'))
        self.insert(StaticText(Rect(2, 15, 18, 16), 'Multi-line (5):'))

        # Single-line sparklines
        self.sparkSine = Sparkline(Rect(16, 4, 50, 5))
        self.insert(self.sparkSine)

        self.sparkRandom = Sparkline(Rect(16, 6, 50, 7))
        self.insert(self.sparkRandom)

        self.sparkStock = Sparkline(Rect(16, 8, 50, 9))
        self.insert(self.sparkStock)

        # Multi-line sparklines (3 lines tall)
        self.sparkMulti3 = Sparkline(Rect(19, 11, 50, 14))
        self.insert(self.sparkMulti3)

        # Multi-line sparklines (5 lines tall)
        self.sparkMulti5 = Sparkline(Rect(19, 15, 50, 20))
        self.insert(self.sparkMulti5)

        # Initialize data
        self.randomWalkValue = 50
        self.stockValue = 100
        self.sineData = []
        self.randomData = []
        self.stockData = []
        self.multiData = []

        # Generate initial data
        for i in range(34):
            self.sineData.append(50 + 50 * math.sin(i * 0.2))
            self.randomWalkValue += random.uniform(-5, 5)
            self.randomData.append(max(0, min(100, self.randomWalkValue)))

            change = random.uniform(-2, 2)
            self.stockValue *= (1 + change / 100)
            self.stockData.append(self.stockValue)

            self.multiData.append(50 + 40 * math.sin(i * 0.3) + random.uniform(-10, 10))

        self.sparkSine.setData(self.sineData)
        self.sparkRandom.setData(self.randomData)
        self.sparkStock.setData(self.stockData)
        self.sparkMulti3.setData(self.multiData)
        self.sparkMulti5.setData(self.multiData)

    def update(self):
        # Update sine wave
        sineValue = 50 + 50 * math.sin(self.time * 0.2)
        self.sineData.append(sineValue)
        if len(self.sineData) > 100:
            self.sineData.pop(0)
        self.sparkSine.setData(self.sineData)

        # Update random walk
        self.randomWalkValue += random.uniform(-5, 5)
        self.randomWalkValue = max(0, min(100, self.randomWalkValue))
        self.randomData.append(self.randomWalkValue)
        if len(self.randomData) > 100:
            self.randomData.pop(0)
        self.sparkRandom.setData(self.randomData)

        # Update stock price
        change = random.uniform(-2, 2)
        self.stockValue *= (1 + change / 100)
        self.stockData.append(self.stockValue)
        if len(self.stockData) > 100:
            self.stockData.pop(0)
        self.sparkStock.setData(self.stockData)

        # Update multi-line data
        multiValue = 50 + 40 * math.sin(self.time * 0.3) + random.uniform(-10, 10)
        self.multiData.append(multiValue)
        if len(self.multiData) > 100:
            self.multiData.pop(0)
        self.sparkMulti3.setData(self.multiData)
        self.sparkMulti5.setData(self.multiData)

        self.time += 1


class SparklineApp(Application):
    def __init__(self):
        super().__init__()
        self.lastUpdate = time.time()
        self.sparklineDialog = None
        self.showDialog()

    def initStatusLine(self, bounds: Rect) -> StatusLine:
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
        if now - self.lastUpdate >= 0.1:
            self.sparklineDialog.update()
            self.lastUpdate = now

    def showDialog(self):
        self.sparklineDialog = SparklineDialog(Rect(10, 2, 62, 24), 'Sparkline Demo')
        self.desktop.insert(self.sparklineDialog)


if __name__ == '__main__':
    app = SparklineApp()
    app.run()