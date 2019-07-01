# -*- coding: utf-8 -*-
import logging
from vindauga.constants.event_codes import evMouseDown, evMouseUp, evKeyDown, evCommand, evBroadcast
from vindauga.widgets.window import Window

from .terminal_view import TerminalView


class TerminalWindow(Window):
    MIN_WIDTH = 28
    MIN_HEIGHT = 11

    def __init__(self, bounds, title, windowNum, command=None, *commandArgs):
        super().__init__(bounds, title, windowNum)
        self.eventMask = evMouseDown | evMouseUp | evKeyDown | evCommand | evBroadcast
        r = self.getClipRect()
        r.grow(-1, -1)
        self.window = TerminalView(r, self, command, *commandArgs)
        self.insert(self.window)
        TerminalView.ActiveTerminals.append(self.window)

    def sizeLimits(self, minLimit, maxLimit):
        super().sizeLimits(minLimit, maxLimit)
        minLimit.x = TerminalWindow.MIN_WIDTH
        minLimit.y = TerminalWindow.MIN_HEIGHT

    def dragView(self, event, mode, limits, minSize, maxSize):
        super().dragView(event, mode, limits, minSize, maxSize)
        self.window.changeSize(self.size)

    def zoom(self):
        super().zoom()
        self.window.changeSize(self.size)

    def setTitle(self, title):
        self.title = title
        self.frame.drawView()
