# -*- coding: utf-8 -*-
from __future__ import annotations
from gettext import gettext as _
import logging
import threading
from typing import Any, Optional

from vindauga.constants.command_codes import (cmReleasedFocus, cmCancel, cmSelectWindowNum, cmQuit, cmCommandSetChanged, cmMenu, cmClose, cmZoom,
                                              cmResize, cmValid, cmScreenChanged, cmTimerExpired)
from vindauga.constants.event_codes import evNothing, evCommand, evKeyDown, evMouseDown, evBroadcast
import vindauga.constants.keys
from vindauga.constants.state_flags import sfVisible, sfSelected, sfFocused, sfModal, sfExposed
import vindauga.constants.key_mappings as key_mappings
from vindauga.events.event import Event
from vindauga.events.event_queue import event_queue
from vindauga.menus.menu_bar import MenuBar
from vindauga.utilities.input.character_codes import getAltChar
from vindauga.utilities.message import message
from vindauga.mouse.mouse import Mouse
from vindauga.utilities.platform.system_interface import systemInterface
from vindauga.types.display import Display
from vindauga.types.group import Group
from vindauga.types.palette import Palette
from vindauga.types.point import Point
from vindauga.types.rect import Rect
from vindauga.types.screen import Screen
from vindauga.types.status_def import StatusDef
from vindauga.types.status_item import StatusItem
from vindauga.types.timer_queue import TimerQueue
from vindauga.types.view import View, SHADOW_SIZE

from .desktop import Desktop
from .dialog import Dialog
from .status_line import StatusLine
from .window import Window


logger = logging.getLogger(__name__)


def hasMouse(view: View, event: Event) -> bool:
    return view.state & sfVisible and view.mouseInView(event.mouse.where)


class Program(Group):
    """
    The mother of `Application`.

    `Program` provides the basic template for all standard vindauga
    applications. All programs must be derived from `Program` or its immediate
    derived class, `Application`. `Application` differs from `Program`
    only for its constructor and destructor. However most applications will
    be derived from `Application`.
    """

    exitText = _('~Alt+X~ Exit')
    desktop: Optional[Desktop] = None
    application: Optional['Application'] = None
    cpAppColor = "\x71\x70\x78\x74\x20\x28\x24\x17\x1F\x1A\x31\x31\x1E\x71\x1F" \
                 "\x37\x3F\x3A\x13\x13\x3E\x21\x3F\x70\x7F\x7A\x13\x13\x70\x7F\x7E" \
                 "\x70\x7F\x7A\x13\x13\x70\x70\x7F\x7E\x20\x2B\x2F\x78\x2E\x70\x30" \
                 "\x3F\x3E\x1F\x2F\x1A\x20\x72\x31\x31\x30\x2F\x3E\x31\x13\x38\x00" \
                 "\x17\x1F\x1A\x71\x71\x1E\x17\x1F\x1E\x20\x2B\x2F\x78\x2E\x10\x30" \
                 "\x3F\x3E\x70\x2F\x7A\x20\x12\x31\x31\x30\x2F\x3E\x31\x13\x38\x00" \
                 "\x37\x3F\x3A\x13\x13\x3E\x30\x3F\x3E\x20\x2B\x2F\x78\x2E\x30\x70" \
                 "\x7F\x7E\x1F\x2F\x1A\x20\x32\x31\x71\x70\x2F\x7E\x71\x13\x78\x00" \
                 "\x37\x3F\x3A\x13\x13\x30\x3E\x1E"  # help colors

    cpAppBlackWhite = "\x70\x70\x78\x7F\x07\x07\x0F\x07\x0F\x07\x70\x70\x07\x70\x0F" \
                      "\x07\x0F\x07\x70\x70\x07\x70\x0F\x70\x7F\x7F\x70\x07\x70\x07\x0F" \
                      "\x70\x7F\x7F\x70\x07\x70\x70\x7F\x7F\x07\x0F\x0F\x78\x0F\x78\x07" \
                      "\x0F\x0F\x0F\x70\x0F\x07\x70\x70\x70\x07\x70\x0F\x07\x07\x08\x00" \
                      "\x07\x0F\x0F\x07\x70\x07\x07\x0F\x0F\x70\x78\x7F\x08\x7F\x08\x70" \
                      "\x7F\x7F\x7F\x0F\x70\x70\x07\x70\x70\x70\x07\x7F\x70\x07\x78\x00" \
                      "\x70\x7F\x7F\x70\x07\x70\x70\x7F\x7F\x07\x0F\x0F\x78\x0F\x78\x07" \
                      "\x0F\x0F\x0F\x70\x0F\x07\x70\x70\x70\x07\x70\x0F\x07\x07\x08\x00" \
                      "\x07\x0F\x07\x70\x70\x07\x0F\x70"  # Help colors

    cpAppMonochrome = "\x70\x07\x07\x0F\x70\x70\x70\x07\x0F\x07\x70\x70\x07\x70\x00" \
                      "\x07\x0F\x07\x70\x70\x07\x70\x00\x70\x70\x70\x07\x07\x70\x07\x00" \
                      "\x70\x70\x70\x07\x07\x70\x70\x70\x0F\x07\x07\x0F\x70\x0F\x70\x07" \
                      "\x0F\x0F\x07\x70\x07\x07\x70\x07\x07\x07\x70\x0F\x07\x07\x70\x00" \
                      "\x70\x70\x70\x07\x07\x70\x70\x70\x0F\x07\x07\x0F\x70\x0F\x70\x07" \
                      "\x0F\x0F\x07\x70\x07\x07\x70\x07\x07\x07\x70\x0F\x07\x07\x01\x00" \
                      "\x70\x70\x70\x07\x07\x70\x70\x70\x0F\x07\x07\x0F\x70\x0F\x70\x07" \
                      "\x0F\x0F\x07\x70\x07\x07\x70\x07\x07\x07\x70\x0F\x07\x07\x01\x00" \
                      "\x07\x0F\x07\x70\x70\x07\x0F\x70"

    apColor = 0
    apBlackWhite = 1
    apMonochrome = 2
    pending: Event = Event(evNothing)
    timerQueue = TimerQueue()
    eventTimeoutMs = 20

    def __init__(self):
        w = systemInterface.getScreenCols()
        h = systemInterface.getScreenRows()
        super().__init__(Rect(0, 0, w, h))
        color = Palette(self.cpAppColor)
        blackWhite = Palette(self.cpAppBlackWhite)
        monochrome = Palette(self.cpAppMonochrome)
        self.palettes = [color, blackWhite, monochrome]
        self.initScreen()
        self.state = sfVisible | sfSelected | sfFocused | sfModal | sfExposed
        self.options = 0
        self.buffer = Screen.screen.screenBuffer
        self.statusLine = None
        self.menuBar = None

        Program.desktop = self.initDesktop(self.getExtent())
        self.insert(Program.desktop)

        self.statusLine = self.initStatusLine(self.getExtent())
        self.insert(self.statusLine)

        self.menuBar = self.initMenuBar(self.getExtent())
        self.insert(self.menuBar)

    def shutdown(self):
        self.statusLine = None
        self.menuBar = None
        Program.desktop = None
        super().shutdown()

    def canMoveFocus(self) -> bool:
        """
        Returns True if the focus can be moved from one (desktop) view to another
        one.

        It returns `deskTop.valid(cmReleasedFocus)`.

        :return: True if the focus can be moved
        """
        return self.desktop.valid(cmReleasedFocus)

    def executeDialog(self, pD: Dialog, data) -> tuple[int, Any]:
        """
        Executes a dialog.

        `pD` points to the dialog. The dialog is executed only if it is valid.

        `data` is a data record which is set on the dialog before executing and
        read afterwards. If `data` is None no data will be set.

        This method calls `execView()` to execute the dialog. The
        dialog is destroyed before returning from the function, so a call to
        delete is not necessary. `executeDialog()` returns `cmCancel` if the view
        is not valid, otherwise it returns the return value of `execView()`.

        :param pD: Dialog to execute
        :param data: Data to set on dialog
        :return: tuple of `executeDate()` call and the data
        """
        logger.info('executeDialog(%s)', pD)
        c = cmCancel

        if self.validView(pD):
            if data:
                pD.setData(data)
            try:
                c = Program.desktop.execView(pD)
            except Exception:
                logger.exception('Dialog failed.')
                c = cmCancel
            if c != cmCancel:
                data = pD.getData()
            self.destroy(pD)

        return c, data

    def eventWaitTimeout(self):
        timeout_ms = min(Program.timerQueue.timeUntilNextTimeout(), 2**64)
        if timeout_ms < 0:
            return self.eventTimeoutMs
        if self.eventTimeoutMs < 0:
            return timeout_ms
        return min(timeout_ms, self.eventTimeoutMs)

    def getEvent(self, event: Event):
        """
        Gets an event.

        This method collects events from the system like key events, mouse
        events and timer events and returns them in the `event` instance.

        `getEvent()` first checks if `Program.putEvent()` has generated a
        pending event. If so, `getEvent()` returns that event. If there is no
        pending event, `getEvent()` calls `screen.getEvent()`.

        If both calls return `evNothing`, indicating that no user input is
        available, `getEvent()` calls `Program.idle()` to allow "background"
        tasks to be performed while the application is waiting for user input.

        Before returning, `getEvent()` passes any `evKeyDown` and
        `evMouseDown` events to the `statusLine` for it to map into
        associated `evCommand` hot key events.

        :param event: Event object to be modified
        """
        if Program.pending.what != evNothing:
            event.setFrom(Program.pending)
            Program.pending.what = evNothing
        else:
            event_queue.waitForEvents(10)  # Reasonable timeout for event processing
            event.getMouseEvent()

            if event.what == evNothing:
                event.getKeyEvent()
                if event.what == evNothing:
                    self.idle()

        if self.statusLine:
            if event.what in (evKeyDown, evMouseDown) and self.firstThat(self.hasMouse, event) is self.statusLine:
                self.statusLine.handleEvent(event)

        if event.what == evCommand and event.message.command == cmScreenChanged:
            logger.info("Program received cmScreenChanged event - calling setScreenMode(smUpdate)")
            self.setScreenMode(Display.smUpdate)
            logger.info("setScreenMode(smUpdate) completed")
            self.clearEvent(event)

    def putEvent(self, event: Event):
        """
        Sets a pending event.

        Puts an event in the pending state, by storing a copy of the `event`
        structure in the `pending` variable, a member of `Program`.

        Only one event is allowed to be pending. The next call to
        `getEvent()` will return this pending event even if there are
        other events in the system queue to be handled.
        :param event: Event to place in the queue
        """
        e = Event(evNothing)
        e.setFrom(event)
        Program.pending = e

    def handleEvent(self, event: Event):
        """
        Standard `Program` event handler.

        This method first checks for keyboard events. When it catches keys from
        Alt-1 to Alt-9 it generates an `evBroadcast` event with the `command`
        field equal to `cmSelectWindowNum` and the `infoPtr` field in the range 1
        to 9.

        Then it calls `Group.handleEvent()`.

        Last it checks for a `cmQuit` command in a `evCommand` event. On
        success it calls `Group.endModal(cmQuit)` to end the modal state. This
        causes the `Program.run()` method to return. In most applications
        this will result in program termination.

        Method `handleEvent()` is almost always overridden to introduce handling
        of commands that are specific to your own application.

        :param event: Event to be handled
        """
        if event.what == evKeyDown:
            c = getAltChar(event.keyDown.keyCode)
            if '1' <= c <= '9':
                if self.canMoveFocus():
                    if message(Program.desktop, evBroadcast, cmSelectWindowNum, int(c)):
                        self.clearEvent(event)
                else:
                    self.clearEvent(event)

        super().handleEvent(event)

        if event.what == evCommand and event.message.command == cmQuit:
            self.endModal(cmQuit)
            self.clearEvent(event)

    @staticmethod
    def handleTimeout(id: TimerId, self):
        message(self, evBroadcast, cmTimerExpired, id)

    def getPalette(self) -> Palette:
        return self.appPalette

    def setPalette(self, palette: Palette):
        self.appPalette = Palette(palette)

    def idle(self):
        """
        Called when in idle state.

        This method is called whenever the library is in idle state, i.e. there
        is not any event to serve. It allows the application to perform
        background tasks while waiting for user input.

        The default idle() calls `statusLine.update()` to allow the status line
        to update itself according to the current help context. Then, if the
        command set has changed since the last call to `idle()`, an
        `evBroadcast` with a command value of `cmCommandSetChanged` is
        generated to allow views that depend on the command set to enable or
        disable themselves.

        The user may redefine this method, for example, to update a clock in
        like the `vindauga_demo` program does.
        """
        if self.statusLine:
            self.statusLine.update()

        if View.commandSetChanged:
            message(self, evBroadcast, cmCommandSetChanged, None)
            View.commandSetChanged = False

        self.timerQueue.collectExpiredTimers(self.handleTimeout, self)

    def initDesktop(self, bounds: Rect):
        """
        Creates a new desktop.
       
        This method creates a standard `Desktop` view and returns it

        `initDesktop()` should never be called directly. Few applications need to
        redefine it to have a custom desktop, instead of the default empty
        `Desktop`

        :param bounds: Bounds of the screen.
        :return: `Desktop` object
        """
        bounds.bottomRight.y -= 1
        bounds.topLeft.y += 1
        return Desktop(bounds)

    def initScreen(self):
        """
        Initializes the screen.
        
        This method is called by the `Program` constructor and
        `setScreenMode()` every time the screen mode is initialized or
        changed.

        Performs the updating and adjustment of screen mode-dependent variables
        for shadow size, markers and application palette (color, monochrome or
        black & white). The shadows are usually painted in the right and bottom
        sides of menus and windows.
        """
        screen = Screen.screen
        if screen.screenMode & 0x00FF != Display.smMono:
            if screen.screenMode & Display.smFont8x8:
                SHADOW_SIZE.x = 1
            else:
                SHADOW_SIZE.x = 2

            SHADOW_SIZE.y = 1
            self.showMarkers = False
            if screen.screenMode & 0x00FF == Display.smBW80:
                self.appPalette = self.palettes[self.apBlackWhite]
            else:
                self.appPalette = self.palettes[self.apColor]
        else:
            SHADOW_SIZE.x = 0
            SHADOW_SIZE.y = 0
            self.showMarkers = True
            self.appPalette = self.palettes[self.apMonochrome]

    def initMenuBar(self, bounds: Rect):
        """
        Creates a new menu bar.

        This method creates a standard `MenuBar` view and returns it.

        `initMenuBar()` should never be called directly. `initMenuBar()` is almost
        always overridden to instantiate a user defined `MenuBar`
        instead of the default empty `MenuBar`.

        :param bounds: Bounds of the screen. Modify to be the top line...
        :return: A MenuBar object.
        """
        bounds.bottomRight.y = bounds.topLeft.y + 1
        return MenuBar(bounds, [])

    def initStatusLine(self, bounds: Rect):
        """
        Creates a new status line.

        This method creates a standard `StatusLine` view and returns it

        `initStatusLine()` should never be called directly. `initStatusLine()` is
        almost always overridden to instantiate a user defined `StatusLine`
        instead of the default empty `StatusLine`.

        :param bounds: Bounds of the screen. Modify to reduce to the bottom line...
        :return: A `StatusLine` object
        """
        bounds.topLeft.y = bounds.bottomRight.y - 1
        return StatusLine(bounds, StatusDef(0, 0xFFFF) +
                          StatusItem(self.exitText, vindauga.constants.keys.kbAltX, cmQuit) +
                          StatusItem('', vindauga.constants.keys.kbF10, cmMenu) +
                          StatusItem('', vindauga.constants.keys.kbCtrlW, cmClose) +
                          StatusItem('', vindauga.constants.keys.kbF5, cmZoom) +
                          StatusItem('', vindauga.constants.keys.kbCtrlF5, cmResize))

    def insertWindow(self, window: Window):
        """
        Inserts a window in the `Program`.

        :param window: Window to insert
        :return: The inserted window
        """
        if self.validView(window):
            if self.canMoveFocus():
                Program.desktop.insert(window)
                return window
            else:
                self.destroy(window)
        return None

    def outOfMemory(self):
        raise Exception

    def run(self):
        """
        Runs `Program`.
       
        Executes `Program` by calling its method `execute()`, which `Program`
        inherits from `Group`.
        """
        self.execute()

    def validView(self, view: View):
        """
        Checks if a view is valid.
       
        Returns `view` if the view pointed by `view` is valid. Otherwise returns None.

        First, if `view` is None the call returns None.

        Last if a call to `view.valid(cmValid)` returns False the view pointed by
        `view` is released and the function returns None.

        Otherwise, the view is considered valid, and pointer `view` is returned.

        :param view: View to test
        :return: View or None
        """
        if not view:
            return None

        if not view.valid(cmValid):
            self.destroy(view)
            return None
        return view

    def killTimer(self, id: TimerId):
        self.timerQueue.killTimer(id)

    def setScreenMode(self, mode):
        Mouse.hide()
        Screen.screen.setVideoMode(mode)
        self.initScreen()
        self.buffer = Screen.screen.screenBuffer
        r = Rect(0, 0, Screen.screen.screenWidth, Screen.screen.screenHeight)
        self.changeBounds(r)
        self.setState(sfExposed, False)
        self.setState(sfExposed, True)
        self.redraw()
        Mouse.show()

    def setTimer(self, timeoutMs: int, periodMs: int) -> TimerId:
        return self.timerQueue.setTimer(timeoutMs, periodMs)


def getDesktopSize() -> Point:
    """
    Get the size of the desktop

    :return: :mod:`Size` object
    """
    return Program.desktop.size


def execView(view):
    """
    Get the running application

    :param view: :mod:`View` to execute
    :return: view exit code
    """
    return Program.application.execView(view)
