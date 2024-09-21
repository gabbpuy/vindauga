# -*- coding: utf-8 -*-
import array
import atexit
import contextlib
import curses
import curses.ascii
import itertools
import logging
import os
import platform
import queue
import select
import struct
import subprocess
import sys
import threading
from typing import Union

from vindauga.constants.command_codes import cmSysRepaint, cmSysResize, cmSysWakeup
from vindauga.constants.event_codes import (mbLeftButton, mbRightButton, evMouseDown, evMouseUp, meDoubleClick,
                                            evMouseMove, meMouseMoved, evKeyDown, evNothing, evCommand, evMouseAuto)
from vindauga.constants.key_mappings import (DELAY_WAKEUP, DELAY_AUTOCLICK_FIRST, DELAY_AUTOCLICK_NEXT, DELAY_ESCAPE,
                                             TALT, keyMappings)
from vindauga.constants.keys import kbNoKey, kbLeftShift, kbRightShift, kbLeftAlt, kbRightAlt, kbLeftCtrl, kbRightCtrl
from vindauga.events.event import Event
from vindauga.events.event_queue import EventQueue
from vindauga.misc.signal_handling import signalHandler, sigWinchHandler
from vindauga.misc.util import clamp
from vindauga.timers import kbEscTimer, msAutoTimer, wakeupTimer
from vindauga.utilities.colours.colours import setPalette

from .draw_buffer import BufferArray, DrawBuffer
from .display import Display
from .mouse_event import MouseEvent
from .point import Point
from .key_mapping import get_key_mapping

PLATFORM_IS_WINDOWS = platform.system().lower() == 'windows'

if PLATFORM_IS_WINDOWS:
    HAS_IOCTL = False
    import msvcrt
    from signal import *
else:
    import fcntl
    import termios
    from signal import signal, SIGCONT, SIGINT, SIGQUIT, SIGTSTP, SIGWINCH

    HAS_IOCTL = 'TIOCLINUX' in dir(termios)

logger = logging.getLogger(__name__)

BUTTON_PRESSED = (curses.BUTTON1_PRESSED |
                  curses.BUTTON2_PRESSED |
                  curses.BUTTON3_PRESSED)
BUTTON_RELEASED = (curses.BUTTON1_RELEASED |
                   curses.BUTTON2_RELEASED |
                   curses.BUTTON3_RELEASED)
BUTTON_DOUBLE_CLICKED = (curses.BUTTON1_DOUBLE_CLICKED |
                         curses.BUTTON2_DOUBLE_CLICKED |
                         curses.BUTTON3_DOUBLE_CLICKED)
BUTTON_CLICKED = (curses.BUTTON1_CLICKED |
                  curses.BUTTON2_CLICKED |
                  curses.BUTTON3_CLICKED)
BUTTON1 = (curses.BUTTON1_PRESSED |
           curses.BUTTON1_RELEASED |
           curses.BUTTON1_CLICKED |
           curses.BUTTON1_DOUBLE_CLICKED |
           curses.BUTTON1_TRIPLE_CLICKED)
BUTTON2 = (curses.BUTTON2_PRESSED |
           curses.BUTTON2_RELEASED |
           curses.BUTTON2_CLICKED |
           curses.BUTTON2_DOUBLE_CLICKED |
           curses.BUTTON2_TRIPLE_CLICKED)
BUTTON3 = (curses.BUTTON3_PRESSED |
           curses.BUTTON3_RELEASED |
           curses.BUTTON3_CLICKED |
           curses.BUTTON3_DOUBLE_CLICKED |
           curses.BUTTON3_TRIPLE_CLICKED)
BUTTON4 = (curses.BUTTON4_PRESSED |
           curses.BUTTON4_RELEASED |
           curses.BUTTON4_CLICKED |
           curses.BUTTON4_DOUBLE_CLICKED |
           curses.BUTTON4_TRIPLE_CLICKED)

# noinspection PyUnresolvedReferences,PyUnresolvedReferences
class Screen:
    eventQ_Size = 16
    evQueue = queue.Queue(eventQ_Size)
    screen = None

    @classmethod
    def init(cls):
        if not Screen.screen:
            Screen.screen = cls()

    def __init__(self):
        self.msWhere = Point(0, 0)
        self.doRepaint = 0
        self.doResize = 0
        self.msOldButtons = 0
        self.msFlag = 0
        self.fdSetRead = []
        self.fdSetWrite = []
        self.fdSetExcept = []
        self.screenMode = 0
        self.screenWidth = 0
        self.screenHeight = 0
        self.screenBuffer = None
        self.curX = 0
        self.curY = 0
        self.attributeMap = []
        self.highColourMap = []

        self.evIn = None
        self.evOut = None
        kbEscTimer.start(1)
        kbEscTimer.stop()
        msAutoTimer.start(1)
        msAutoTimer.stop()
        self.msOldButtons = self.msWhere.x = self.msWhere.y = 0
        wakeupTimer.start(DELAY_WAKEUP)
        self.stdscr = self.initialiseScreen()
        self._setScreenSize()
        self.__rawMode = False

        if not PLATFORM_IS_WINDOWS:
            signals = (SIGCONT,
                       SIGINT,
                       SIGQUIT,
                       SIGTSTP,
                       # SIGWINCH is handled separately
                       )
            self.fdSetRead.append(sys.stdin.fileno())
        else:
            signals = (
                SIGINT,
                SIGBREAK,
                SIGTERM,
            )

        [signal(signo, signalHandler) for signo in signals]
        if not PLATFORM_IS_WINDOWS:
            sigWinchHandler()

        self.selectPalette()
        self.lockRefresh = 0
        self.__draw_lock = threading.Lock()

    @staticmethod
    def evLength() -> int:
        # return len(Screen.evQueue)
        return Screen.evQueue.qsize()

    @staticmethod
    def kbReadShiftState(ch: Union[str, int]):
        shift = 0
        if not HAS_IOCTL:
            return get_key_mapping(ch)
        arg = 6
        shift = 0
        try:
            buf = array.array('B', [arg])
            res = fcntl.ioctl(sys.stdin, termios.TIOCLINUX, buf)
            buf = struct.unpack('B', res)
            arg = buf[0]
            if arg & (2 | 8):
                shift |= kbLeftAlt | kbRightAlt
            if arg & 4:
                shift |= kbLeftCtrl | kbRightCtrl
            if arg & 1:
                shift |= kbLeftShift | kbRightShift
        except OSError:
            return get_key_mapping(ch)
        return ch, shift

    @staticmethod
    def kbMapKey(code: Union[str, int], eventType: int, modifiers: int) -> int:
        best = keyMappings.get((code, eventType, modifiers))

        if best:
            return best.key

        if isinstance(code, str):
            code = ord(code)

        if code <= 255:
            return code
        # unknown code
        return kbNoKey

    @staticmethod
    def setBigCursor():
        curses.curs_set(2)

    @staticmethod
    def setSmallCursor():
        curses.curs_set(1)

    def refresh(self):
        self.stdscr.refresh()

    # noinspection PyUnresolvedReferences
    def initialiseScreen(self):
        stdscr = curses.initscr()
        curses.noecho()
        curses.cbreak()
        stdscr.keypad(True)
        stdscr.nodelay(True)
        try:
            curses.start_color()
            curses.use_default_colors()
        except curses.error:
            pass
        atexit.register(self.shutdown)
        curses.mousemask(curses.ALL_MOUSE_EVENTS)
        sys.stderr = open(os.devnull, 'wt')
        return stdscr

    def shutdown(self):
        sys.stderr = sys.__stderr__
        self.stdscr.nodelay(False)
        self.stdscr.keypad(False)
        curses.echo()
        curses.nocbreak()
        curses.endwin()

    def setScreenSize(self, width: int, height: int):
        if PLATFORM_IS_WINDOWS:
            subprocess.call(['mode', 'con:', f'cols={width}', f'lines={height}'], shell=True)
            # There's no incoming sigwinch, so resize the terminal then redraw
            curses.resize_term(height, width)
        elif curses.is_term_resized(height, width):
            # The resize is handled via sigwinch
            print(f'\x1b[8;{height};{width}t')
        self.doResize += 1

    @staticmethod
    def putMouseEvent(event: Event, buttons: int, flags: int, what: int):
        event.mouse.buttons = 0
        event.mouse.eventFlags = flags
        event.what = what

        if EventQueue.mouseReverse:
            if buttons & mbLeftButton:
                event.mouse.buttons |= mbRightButton
            if buttons & mbRightButton:
                event.mouse.buttons |= mbLeftButton
        else:
            event.mouse.buttons = buttons
        EventQueue.mouse.copy(event.mouse)
        Screen.putEvent(event)

    def handleMouse(self) -> bool:
        event = Event(evNothing)

        try:
            me = MouseEvent(*curses.getmouse())
        except Exception as e:
            # No mouse? No Problem.
            return False

        event.mouse.controlKeyState = 0

        if me.bstate & curses.BUTTON_SHIFT:
            event.mouse.controlKeyState |= kbLeftShift | kbRightShift
        if me.bstate & curses.BUTTON_CTRL:
            event.mouse.controlKeyState |= kbLeftCtrl | kbRightCtrl
        if me.bstate & curses.BUTTON_ALT:
            event.mouse.controlKeyState |= kbLeftAlt | kbRightAlt

        event.mouse.where.x = clamp(me.x, 0, self.screenWidth - 1)
        event.mouse.where.y = clamp(me.y, 0, self.screenHeight - 1)

        # Convert buttons.
        buttons = mbLeftButton
        if me.bstate & BUTTON1:
            buttons = mbLeftButton
        elif me.bstate & BUTTON3:
            buttons = mbRightButton

        # Check clicks.
        if me.bstate & BUTTON_CLICKED:
            self.putMouseEvent(event, buttons, 0, evMouseDown)
            self.msOldButtons = buttons

            msAutoTimer.stop()
            self.putMouseEvent(event, buttons, 0, evMouseUp)
            self.msOldButtons &= ~buttons

        # Double clicked...
        if me.bstate & BUTTON_DOUBLE_CLICKED:
            msAutoTimer.stop()
            self.putMouseEvent(event, buttons, meDoubleClick, evMouseDown)
            self.msOldButtons &= ~buttons

        if event.mouse.where != self.msWhere:
            # Undraw the mouse
            self.drawMouse(False)
            if me.bstate & BUTTON_PRESSED:
                self.putMouseEvent(event, buttons, meMouseMoved, evMouseMove)
                self.msWhere.x = event.mouse.where.x
                self.msWhere.y = event.mouse.where.y
                msAutoTimer.start(DELAY_AUTOCLICK_FIRST)
                self.putMouseEvent(event, buttons, 0, evMouseDown)
                self.msOldButtons = buttons

            if me.bstate & BUTTON_RELEASED:
                self.putMouseEvent(event, buttons, meMouseMoved, evMouseMove)
                self.msWhere.x = event.mouse.where.x
                self.msWhere.y = event.mouse.where.y
                msAutoTimer.stop()
                self.putMouseEvent(event, buttons, 0, evMouseUp)
                self.msOldButtons &= ~buttons
        else:
            if me.bstate & BUTTON_PRESSED:
                msAutoTimer.start(DELAY_AUTOCLICK_FIRST)
                self.putMouseEvent(event, buttons, 0, evMouseDown)
                self.msOldButtons = buttons
            if me.bstate & BUTTON_RELEASED:
                msAutoTimer.stop()
                self.putMouseEvent(event, buttons, 0, evMouseUp)
                self.msOldButtons &= ~buttons
        return True

    def handleKeyboard(self):
        keyType = 0

        # see if there is data available
        try:
            code = self.stdscr.get_wch()
        except curses.error:
            # getch() returns -1, get_wch() raises an exception
            code = curses.ERR

        if not isinstance(code, (int,)):
            code = ord(code)

        if code == curses.KEY_MOUSE:
            return self.handleMouse()

        if code != curses.ERR:
            # grab the escape key and start the timer
            if code == 27 and not kbEscTimer.isRunning():
                return kbEscTimer.start(DELAY_ESCAPE)

            # key pressed within time limit
            if kbEscTimer.isRunning() and not kbEscTimer.isExpired():
                kbEscTimer.stop()
                if code != 27:  # simulate Alt-letter code
                    code = chr(code & 0xFF).upper()
                    keyType = TALT
        elif kbEscTimer.isExpired():
            # timeout condition: generate standard Esc code
            kbEscTimer.stop()
            code = 27
        else:  # code == curses.ERR
            return

        modifiers = 0
        if PLATFORM_IS_WINDOWS:
            # Handle ALT+ keys in DOS window
            if (code & 0x120) == 0x120 and code >= 0x160:
                code = chr(code - 0x160)
                keyType = TALT
                modifiers = 0
        else:
            code, modifiers = self.kbReadShiftState(code)

        code = self.kbMapKey(code, keyType, modifiers)

        if code != kbNoKey:
            event = Event(evKeyDown)
            event.keyDown.keyCode = code
            event.keyDown.controlKeyState = modifiers
            Screen.putEvent(event)

    def selectPalette(self):
        self.screenMode, self.attributeMap, self.highColourMap = setPalette()
        logger.info('ScreenMode: %s', self.screenMode)

    def getEvent(self, event: Event):
        event.what = evNothing
        if self.doRepaint > 0:
            self.doRepaint = 0
            event.message.command = cmSysRepaint
            event.what = evCommand
        elif self.doResize > 0:
            self.doResize = 0
            # If there was a SIGWINCH, this will redraw based on the window size
            curses.endwin()
            self.stdscr.refresh()
            self._setScreenSize()
            event.message.command = cmSysResize
            event.what = evCommand
        elif not Screen.evQueue.empty():
            event.setFrom(Screen.evQueue.get())
        elif msAutoTimer.isExpired():
            msAutoTimer.start(DELAY_AUTOCLICK_NEXT)
            event.mouse.buttons = self.msOldButtons
            event.mouse.where.x = self.msWhere.x
            event.mouse.where.y = self.msWhere.y
            event.what = evMouseAuto
        elif wakeupTimer.isExpired():
            wakeupTimer.start(DELAY_WAKEUP)
            event.message.command = cmSysWakeup
            event.what = evCommand
        else:
            self.__handleIO_Events(event)

    def makeBeep(self):
        curses.beep()
        self.stdscr.refresh()

    @staticmethod
    def putEvent(event: Event):
        try:
            Screen.evQueue.put(event)
        except queue.Full:
            logger.error('evQueue hit event limit')
            pass

    def resume(self):
        self.doRepaint += 1

    def suspend(self):
        pass

    def moveCursor(self, x, y):
        self.stdscr.move(y, x)
        self.stdscr.refresh()
        self.curX = x
        self.curY = y

    def drawCursor(self, show: bool):
        if show:
            self.moveCursor(self.curX, self.curY)
        else:
            self.moveCursor(self.screenWidth - 1, self.screenHeight - 1)

    def drawMouse(self, show: bool):
        try:
            cell = self.screenBuffer[self.msWhere.y * self.screenWidth + self.msWhere.x]
        except IndexError:
            logger.exception('drawMouse')
            return

        code = cell & DrawBuffer.CHAR_MASK
        color = (cell >> DrawBuffer.CHAR_WIDTH) & 0xFF

        if self.screenMode in {Display.smCO80, Display.smFont8x8, Display.smCO256}:
            if show:
                color ^= 0x7F
        else:
            if show:
                if color in {0x07, 0x0f}:
                    color = 0x70
                elif color == 0x70:
                    color = 0x0f

        stdscr = self.stdscr
        stdscr.move(self.msWhere.y, self.msWhere.x)
        stdscr.attrset(self.attributeMap[color])
        try:
            stdscr.addch(chr(code))
        except curses.error as e:
            # Writing to the bottom right corner throws an error after it is drawn.
            # If the mouse cursor is in the bottom right...
            pass
        stdscr.move(self.curY, self.curX)
        stdscr.refresh()

    def writeRow(self, x: int, y: int, src, rowLen: int):
        if self.__rawMode: # and self.screenMode == Display.smCO256:
            return self.writeRowRaw(x, y, src, rowLen)

        with self.__draw_lock:
            stdscr = self.stdscr
            stdscr.move(y, x)
            attributeMap = self.attributeMap
            addstr = stdscr.addstr
            for sc in itertools.islice(src, rowLen):
                code = chr(sc & 0xFFFF)
                color = ((sc & 0xFFFF0000) >> 16) & 0xFFFF
                try:
                    addstr(code, attributeMap[color])
                except curses.error as e:
                    # Writing to the bottom right corner throws an error after it is drawn
                    pass

            stdscr.move(self.curY, self.curX)

    def writeRowRaw(self, x: int, y: int, src, rowLen: int):
        """
        Write a row with high colours, instead of the 8x16 text-ui palette.
        This needs `smCO256` Display type and 64K colour pairs to be worth using.
        """
        with self.__draw_lock:
            stdscr = self.stdscr
            stdscr.move(y, x)
            attributeMap = self.highColourMap
            addstr = stdscr.addstr
            for sc in itertools.islice(src, rowLen):
                code = chr(sc & 0xFFFF)
                color = ((sc & 0xFFFF0000) >> 16) & 0xFFFF
                try:
                    addstr(code, color) # attributeMap[color])
                except curses.error as e:
                    # Writing to the bottom right corner throws an error after it is drawn
                    pass

            stdscr.move(self.curY, self.curX)

    @contextlib.contextmanager
    def setRawMode(self):
        """
        Context manager to switch to raw mode for writing.
        """
        self.__rawMode = True
        try:
            yield
        finally:
            self.__rawMode = False

    def _setScreenSize(self):
        self.screenHeight, self.screenWidth = self.stdscr.getmaxyx()
        self.screenBuffer = BufferArray([0] * (self.screenWidth * self.screenHeight))

    def __handleIO_Events(self, event: Event):
        fdActualRead = self.fdSetRead
        fdActualWrite = self.fdSetWrite
        fdActualExcept = self.fdSetExcept
        kbReady = False
        msReady = False
        if not PLATFORM_IS_WINDOWS:
            try:
                reads, write, excepts = select.select(fdActualRead,
                                                      fdActualWrite,
                                                      fdActualExcept,
                                                      .01)
                kbReady = sys.stdin.fileno() in reads
                # msReady = (msFd >= 0 and msFd in reads)
                msReady = False
            except select.error as e:
                pass
        else:
            msReady = False
            kbReady = msvcrt.kbhit()

        if kbReady or kbEscTimer.isRunning() or PLATFORM_IS_WINDOWS:
            self.handleKeyboard()

        if not (kbReady or msReady) and wakeupTimer.isExpired():
            wakeupTimer.start(DELAY_WAKEUP)
            event.message.command = cmSysWakeup
            event.what = evCommand
