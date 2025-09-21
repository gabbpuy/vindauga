# -*- coding: utf-8 -*-
from __future__ import annotations
import logging
import platform
import subprocess
import sys
import threading
import traceback

from vindauga.utilities.platform.system_interface import systemInterface
from vindauga.utilities.screen.screen_cell import ScreenCell
from vindauga.types.display import Display
from vindauga.mouse.mouse import Mouse

logger = logging.getLogger(__name__)


class _Display:

    def __init__(self, display: _Display | None = None):
        self.__updateIntlChars()

    def clearScreen(self, w: int, h: int):
        systemInterface.clearScreen(w, h)

    def setCursorType(self, ct: int):
        systemInterface.setCaretSize(ct & 0xFF)

    def getCursorType(self) -> int:
        return systemInterface.getCaretSize()

    def getRows(self) -> int:
        return systemInterface.getScreenRows()

    def getCols(self) -> int:
        return systemInterface.getScreenCols()

    def setCrtMode(self, mode: int):
        systemInterface.setScreenMode(mode)

    def getCrtMode(self) -> int:
        return systemInterface.getScreenMode()

    def __updateIntlChars(self):
        pass


class Screen(_Display):
    
    # Class-level screen instance (singleton-like)
    screen = None

    @classmethod
    def init(cls):
        """
        Initialize the global screen instance
        """
        if cls.screen is None:
            cls.screen = cls()
        return cls.screen

    def __init__(self):
        super().__init__()
        self.startupMode: int = -1
        self._video_mode_lock = threading.Lock()
        self.startupCursor: int = -1
        self.screenWidth: int = 0
        self.screenHeight: int = 0
        self.screenMode: int = 0
        self.clearOnSuspend: bool = False  # Set to False to prevent grey screen during resize

        systemInterface.setupConsole()
        # Expose platform for compatibility checking
        self.startupMode = self.getCrtMode()
        self.startupCursor = self.getCursorType()
        self.screenBuffer: list[ScreenCell] = systemInterface.allocateScreenBuffer()
        self.setCrtData()
        self.cursorLines: int = 0


    def setVideoMode(self, mode: int):
        if mode != Display.smUpdate:
            self.setCrtMode(self.fixCrtMode(mode))
        else:
            systemInterface.freeScreenBuffer(self.screenBuffer)
            self.screenBuffer = systemInterface.allocateScreenBuffer()
        self.setCrtData()
        if Mouse.present():
            Mouse.setRange(self.getCols() - 1, self.getRows() - 1)

    def clearScreen(self):
        super().clearScreen(self.screenWidth, self.screenHeight)

    def flushScreen(self):
        systemInterface.flushScreen()

    def setCrtData(self):
        raw_mode = self.getCrtMode()
        self.screenMode = raw_mode
        logger.debug("DEBUG setCrtData: raw_mode=%s (0x%s), screenMode=%s",
                     raw_mode, hex(raw_mode), self.screenMode)
        self.screenWidth = self.getCols()
        self.screenHeight = self.getRows()
        logger.info('Screen Dimensions now %s', (self.screenWidth, self.screenHeight))
        self.cursorLines = self.getCursorType()
        self.setCursorType(0)

    def fixCrtMode(self, mode: int) -> int:

        if (mode & 0xFF) == Display.smMono:
            return Display.smMono
        if (mode & 0xFF) != Display.smCO80 and (mode & 0xFF) != Display.smBW80:
            mode = mode & 0xFF00 | Display.smCO80
        return mode

    def setScreenSize(self, width, height):
        systemInterface.resize(width, height)
        self.setVideoMode(Display.smUpdate)

    def suspend(self):
        if self.startupMode != self.screenMode:
            self.setCrtMode(self.startupMode)
        if self.clearOnSuspend:
            self.clearScreen()
        self.setCursorType(self.startupCursor)
        systemInterface.restoreConsole()

    def refresh(self):
        """
        Refresh the screen display
        """
        self.flushScreen()
    
    def makeBeep(self):
        try:
            # Try to make a system beep sound
            print('\a', end='', flush=True)
        except Exception:
            pass  # Ignore if beep fails

    def __del__(self):
        self.suspend()

    def resume(self):
        self.startupMode = self.getCrtMode()
        self.startupCursor = self.getCursorType()
        if self.screenMode != self.startupMode:
            self.setCrtMode(self.screenMode)
        self.setCrtData()
    





