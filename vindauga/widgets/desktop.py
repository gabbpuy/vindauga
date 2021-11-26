# -*- coding: utf-8 -*-
import logging

from vindauga.constants.command_codes import cmNext, cmPrev, cmReleasedFocus
from vindauga.constants.grow_flags import gfGrowHiX, gfGrowHiY
from vindauga.constants.event_codes import evCommand
from vindauga.constants.option_flags import ofTileable
from vindauga.constants.state_flags import sfVisible
from vindauga.types.group import Group
from vindauga.types.point import Point
from vindauga.types.rect import Rect

from .background import Background

logger = logging.getLogger(__name__)


class Desktop(Group):
    """
    The desktop of the application.

    `Desktop` inherits from `Group` `Desktop` is a simple group that owns the
    `Background` view upon which the application's windows and other views appear.

    `Desktop` represents the desk top area of the screen between the top menu
    bar and bottom status line (but only when the bar and line exist). By
    default, `Desktop` has a `Background` object inside which paints its
    background.
    """
    DEFAULT_BACKGROUND = '▒'

    name = 'Desktop'

    def __init__(self, bounds):
        super().__init__(bounds)
        self.cascadeNum = 0
        self.lastView = None
        self.numCols = 0
        self.numRows = 0
        self.numTileable = 0
        self.leftOver = 0
        self.tileNum = 0

        self.growMode = gfGrowHiX | gfGrowHiY
        self.tileColumnsFirst = False
        background = self.initBackground(self.getExtent())
        if background:
            self._background = background
            self.insert(self._background)
        else:
            self._background = None

    @staticmethod
    def isTileable(window):
        return window.options & ofTileable and window.state & sfVisible

    def mostEqualDivisors(self, n):
        """
        Find a 'square' to tile the windows.

        :param n: Number of windows
        :return: Width and height
        """
        i = int(n ** .5)
        if n % i:
            if not n % (i + 1):
                i += 1
        i = max(i, n // i)
        a, b = n // i, i
        if self.tileColumnsFirst:
            x, y = b, a
        else:
            x, y = a, b
        return x, y

    def calcTileRect(self, pos, bounds):
        def dividerLoc(lo, hi, num, dPos):
            return int((hi - lo) * dPos // num + lo)

        d = (self.numCols - self.leftOver) * self.numRows

        if pos < d:
            x, y = divmod(pos, self.numRows)
        else:
            x = (pos - d) // (self.numRows + 1) + (self.numCols - self.leftOver)
            y = (pos - d) % (self.numRows + 1)

        nRect = Rect(0, 0, 0, 0)
        nRect.topLeft.x = dividerLoc(bounds.topLeft.x, bounds.bottomRight.x, self.numCols, x)
        nRect.bottomRight.x = dividerLoc(bounds.topLeft.x, bounds.bottomRight.x, self.numCols, x + 1)

        if pos >= d:
            nRect.topLeft.y = dividerLoc(bounds.topLeft.y, bounds.bottomRight.y, self.numRows + 1, y)
            nRect.bottomRight.y = dividerLoc(bounds.topLeft.y, bounds.bottomRight.y, self.numRows + 1, y + 1)
        else:
            nRect.topLeft.y = dividerLoc(bounds.topLeft.y, bounds.bottomRight.y, self.numRows, y)
            nRect.bottomRight.y = dividerLoc(bounds.topLeft.y, bounds.bottomRight.y, self.numRows, y + 1)

        return nRect

    def doCountTileable(self, window, *_args):
        if self.isTileable(window):
            self.numTileable += 1

    def doCascade(self, window, bounds):
        if self.isTileable(window) and self.cascadeNum >= 0:
            newRect = bounds.copy()
            newRect.topLeft.x += self.cascadeNum
            newRect.topLeft.y += self.cascadeNum
            window.locate(newRect)
            self.cascadeNum -= 1

    def doCount(self, window, *_args):
        if self.isTileable(window):
            self.cascadeNum += 1
            self.lastView = window

    def doTile(self, window, bounds):
        if self.isTileable(window):
            r = self.calcTileRect(self.tileNum, bounds)
            window.locate(r)
            self.tileNum -= 1

    def shutdown(self):
        self._background = None
        super().shutdown()

    def cascade(self, r):
        """
        Moves all the windows in a cascade-like fashion.

        Redisplays all tileable windows owned by the desk top in cascaded
        format. The first tileable window in Z-order (the window "in back") is
        zoomed to fill the desk top, and each succeeding window fills a region
        beginning one line lower and one space further to the right than the
        one before. The active window appears "on top" as the smallest window.

        :param r: Rectangle to cascade into
        """
        minSize = Point()
        maxSize = Point()
        self.cascadeNum = 0

        self.forEach(self.doCount, None)
        if self.cascadeNum > 0:
            self.lastView.sizeLimits(minSize, maxSize)
            if ((minSize.x > r.bottomRight.x - r.topLeft.x - self.cascadeNum) or
                    (minSize.y > r.bottomRight.y - r.topLeft.y - self.cascadeNum)):
                self.tileError()
            else:
                self.cascadeNum -= 1
                self.lock()
                try:
                    self.forEach(self.doCascade, r)
                finally:
                    self.unlock()

    def handleEvent(self, event):
        """
        Calls `super().handleEvent()` and takes care of the commands `cmNext`
        (usually the hot key F6) and `cmPrev` by cycling through the windows
        owned by the desktop, starting with the currently selected view.

        :param event: The event to handle
        """
        super().handleEvent(event)

        if event.what == evCommand:
            c = event.message.command

            if c == cmNext:
                if self.valid(cmReleasedFocus):
                    self.selectNext(False)
            elif c == cmPrev:
                if self.valid(cmReleasedFocus):
                    self.current.putInFrontOf(self._background)
            else:
                return
            self.clearEvent(event)

    def initBackground(self, bounds):
        """
        Creates a new background.

        Returns a newly-created `Background` object.
        The `background` data member is set to point at the new `Background` object.

        Override this method if you want a custom background.

        :param bounds: Bounds of the desktop
        :return: A `Background` object
        """
        return Background(bounds, self.DEFAULT_BACKGROUND)

    def tile(self, bounds):
        """
        Moves all the windows in a tile-like fashion.

        :param bounds: Bounds of the desktop
        """
        self.numTileable = 0
        self.forEach(self.doCountTileable, None)
        if self.numTileable > 0:
            self.numCols, self.numRows = self.mostEqualDivisors(self.numTileable)

            if (((bounds.bottomRight.x - bounds.topLeft.x) // self.numCols == 0) or
                    ((bounds.bottomRight.y - bounds.topLeft.y) // self.numRows == 0)):
                self.tileError()
            else:
                self.leftOver = self.numTileable % self.numCols
                self.tileNum = self.numTileable - 1
                self.lock()
                try:
                    self.forEach(self.doTile, bounds)
                finally:
                    self.unlock()

    def tileError(self):
        """
        Called on tiling error.

        This method is called whenever `cascade()` or `tile()` run into
        troubles in moving the windows. You can override it if you want to
        give an error message to the user. By default, it does nothing.
        """
        logger.error('tile error.')
        pass
