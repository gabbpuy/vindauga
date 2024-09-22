# -*- coding: utf-8 -*-
import logging
from vindauga.constants.event_codes import evMouseDown, evMouseUp, evKeyDown, evCommand, evBroadcast
from vindauga.events.event import Event
from vindauga.types.point import Point
from vindauga.types.rect import Rect
from vindauga.widgets.window import Window

from .terminal_view import TerminalView

logger = logging.getLogger(__name__)


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

    def sizeLimits(self, minLimit: Point, maxLimit: Point):
        super().sizeLimits(minLimit, maxLimit)
        minLimit.x = TerminalWindow.MIN_WIDTH
        minLimit.y = TerminalWindow.MIN_HEIGHT

    def dragView(self, event: Event, mode: int, limits: Rect, minSize: Point, maxSize: Point):
        super().dragView(event, mode, limits, minSize, maxSize)
        self.window.changeSize(self.size)

    def zoom(self):
        super().zoom()
        self.window.changeSize(self.size)

    def setTitle(self, title: str):
        self.title = title
        self.frame.drawView()

    def shutdown(self):
        try:
            logger.info('Removing %s from active terminals', self.window)
            TerminalView.ActiveTerminals.remove(self.window)
            self.window.destroy()
        except ValueError:
            # Terminal is not in the list
            pass
        super().shutdown()
