# -*- coding: utf-8 -*-
import array
import atexit
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

from .draw_buffer import BufferArray, DrawBuffer
from .display import Display
from .mouse_event import MouseEvent
from .point import Point

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

logger = logging.getLogger('vindauga.types.screen')

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
class TScreen:
    eventQ_Size = 16
    evQueue = queue.Queue(eventQ_Size)

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

    @staticmethod
    def evLength():
        # return len(TScreen.evQueue)
        return TScreen.evQueue.qsize()

    @staticmethod
    def kbReadShiftState():
        if not HAS_IOCTL:
            return 0
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
            return 0
        return shift

    @staticmethod
    def kbMapKey(code, eventType, modifiers):
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
        if not self.lockRefresh:
            self.stdscr.refresh()

    # noinspection PyUnresolvedReferences
    def initialiseScreen(self):
        stdscr = curses.initscr()
        curses.noecho()
        curses.cbreak()
        stdscr.keypad(1)
        try:
            curses.start_color()
            curses.use_default_colors()
        except curses.error:
            pass
        atexit.register(self.shutdown)
        curses.mousemask(curses.ALL_MOUSE_EVENTS)
        sys.stderr = os.devnull
        return stdscr

    def shutdown(self):
        sys.stderr = sys.__stderr__
        self.stdscr.keypad(0)
        curses.echo()
        curses.nocbreak()
        curses.endwin()

    def setScreenSize(self, width, height):
        if PLATFORM_IS_WINDOWS:
            subprocess.call(['mode', 'con:', 'cols={}'.format(width), 'lines={}'.format(height)], shell=True)
            # There's no incoming sigwinch, so resize the terminal then redraw
            curses.resize_term(height, width)
        elif curses.is_term_resized(height, width):
            # The resize is handled via sigwinch
            print('\x1b[8;{};{}t'.format(height, width))
        self.doResize += 1

    @staticmethod
    def msPutEvent(event, buttons, flags, what):
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

        TScreen.putEvent(event)

    def handleMouse(self):
        event = Event(evNothing)

        try:
            me = MouseEvent(*curses.getmouse())
        except Exception as e:
            # No mouse? No Problem.
            return

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
            self.msPutEvent(event, buttons, 0, evMouseDown)
            self.msOldButtons = buttons

            msAutoTimer.stop()
            self.msPutEvent(event, buttons, 0, evMouseUp)
            self.msOldButtons &= ~buttons

        # Double clicked...
        if me.bstate & BUTTON_DOUBLE_CLICKED:
            msAutoTimer.stop()
            self.msPutEvent(event, buttons, meDoubleClick, evMouseDown)
            self.msOldButtons &= ~buttons

        if event.mouse.where != self.msWhere:
            # Undraw the mouse
            self.drawMouse(False)
            if me.bstate & BUTTON_PRESSED:
                self.msPutEvent(event, buttons, meMouseMoved, evMouseMove)
                self.msWhere.x = event.mouse.where.x
                self.msWhere.y = event.mouse.where.y
                msAutoTimer.start(DELAY_AUTOCLICK_FIRST)
                self.msPutEvent(event, buttons, 0, evMouseDown)
                self.msOldButtons = buttons

            if me.bstate & BUTTON_RELEASED:
                self.msPutEvent(event, buttons, meMouseMoved, evMouseMove)
                self.msWhere.x = event.mouse.where.x
                self.msWhere.y = event.mouse.where.y
                msAutoTimer.stop()
                self.msPutEvent(event, buttons, 0, evMouseUp)
                self.msOldButtons &= ~buttons
        else:
            if me.bstate & BUTTON_PRESSED:
                msAutoTimer.start(DELAY_AUTOCLICK_FIRST)
                self.msPutEvent(event, buttons, 0, evMouseDown)
                self.msOldButtons = buttons
            if me.bstate & BUTTON_RELEASED:
                msAutoTimer.stop()
                self.msPutEvent(event, buttons, 0, evMouseUp)
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
            if (code & 0x120) == 0x120:
                code = chr(code - 0x160)
                keyType = TALT
                modifiers = 0
        else:
            modifiers = self.kbReadShiftState()
        code = self.kbMapKey(code, keyType, modifiers)
        if code != kbNoKey:
            event = Event(evKeyDown)
            event.keyDown.keyCode = code
            event.keyDown.controlKeyState = modifiers
            TScreen.putEvent(event)

    def selectPalette(self):
        if curses.can_change_color():
            # TODO: Put the palette back the way it was
            # Your powershell window is going to look pink after you exit... d8)
            curses.init_color(curses.COLOR_BLACK, 0, 0, 0)
            curses.init_color(curses.COLOR_BLUE, 0, 0, 750)
            curses.init_color(curses.COLOR_GREEN, 0, 750, 0)
            curses.init_color(curses.COLOR_RED, 750, 0, 0)
            curses.init_color(curses.COLOR_YELLOW, 750, 750, 0)
            curses.init_color(curses.COLOR_MAGENTA, 750, 0, 750)
            curses.init_color(curses.COLOR_CYAN, 0, 750, 750)
            curses.init_color(curses.COLOR_WHITE, 750, 750, 750)

        # The color ordering is different between a CMD / Powershell window and everything else...
        if not PLATFORM_IS_WINDOWS:
            colorMap = (curses.COLOR_BLACK,
                        curses.COLOR_CYAN,
                        curses.COLOR_GREEN,
                        curses.COLOR_RED,
                        curses.COLOR_YELLOW,
                        curses.COLOR_MAGENTA,
                        curses.COLOR_BLUE,
                        curses.COLOR_WHITE)
        else:
            colorMap = (curses.COLOR_BLACK,
                        curses.COLOR_YELLOW,
                        curses.COLOR_GREEN,
                        curses.COLOR_CYAN,
                        curses.COLOR_RED,
                        curses.COLOR_MAGENTA,
                        curses.COLOR_BLUE,
                        curses.COLOR_WHITE)

        self.attributeMap = array.array('L', [0] * 256)

        if curses.has_colors():
            self.screenMode = Display.smCO80
            i = 0
            for fore in reversed(colorMap):
                for back in colorMap:
                    if i:
                        curses.init_pair(i, fore, back)
                    i += 1

            for i in range(256):
                back = (i >> 4) & 0x07
                bold = i & 0x08
                fore = i & 0x07
                self.attributeMap[i] = curses.color_pair((7 - colorMap[fore]) * 8 + colorMap[back])
                if bold:
                    self.attributeMap[i] |= curses.A_BOLD

        else:
            self.screenMode = Display.smMono
            self.attributeMap[0x07] = curses.A_NORMAL
            self.attributeMap[0x0f] = curses.A_BOLD
            self.attributeMap[0x70] = curses.A_REVERSE

    def getEvent(self, event):
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
        elif TScreen.evLength() > 0:
            event.setFrom(TScreen.evQueue.get())
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
    def putEvent(event):
        try:
            TScreen.evQueue.put(event)
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

    def drawCursor(self, show):
        if show:
            self.moveCursor(self.curX, self.curY)
        else:
            self.moveCursor(self.screenWidth - 1, self.screenHeight - 1)

    def drawMouse(self, show):
        try:
            cell = self.screenBuffer[self.msWhere.y * self.screenWidth + self.msWhere.x]
        except IndexError:
            logger.exception('drawMouse')
            return

        code = cell & DrawBuffer.CHAR_MASK
        color = (cell >> DrawBuffer.CHAR_WIDTH) & 0xFF

        if self.screenMode in {Display.smCO80, Display.smFont8x8}:
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

    def writeRow(self, x, y, src, rowLen):
        stdscr = self.stdscr
        stdscr.move(y, x)
        attributeMap = self.attributeMap
        attrset = stdscr.attrset
        addch = stdscr.addch
        for sc in itertools.islice(src, rowLen):
            code = chr(sc & 0xFFFF)
            color = ((sc & 0xFF0000) >> 16) & 0xFF
            attrset(attributeMap[color])
            try:
                addch(code)
            except curses.error as e:
                # Writing to the bottom right corner throws an error after it is drawn
                pass

        stdscr.move(self.curY, self.curX)

    def _setScreenSize(self):
        self.screenHeight, self.screenWidth = self.stdscr.getmaxyx()
        self.screenBuffer = BufferArray([0] * (self.screenWidth * self.screenHeight))

    def __handleIO_Events(self, event):
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
                                                      .001)
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

        if not (kbReady or msReady):
            wakeupTimer.start(DELAY_WAKEUP)
            event.message.command = cmSysWakeup
            event.what = evCommand


Screen = None


def _setScreen():
    global Screen
    if not Screen:
        Screen = TScreen()


_setScreen()
