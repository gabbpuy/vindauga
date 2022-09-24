# -*- coding: utf-8-*-
import copy
from dataclasses import dataclass
import datetime
import logging
from itertools import cycle, islice
from typing import Optional

from vindauga.constants.command_codes import cmCancel, hcNoContext, cmReleasedFocus, cmLoseFocus, cmQuit
from vindauga.constants.event_codes import positionalEvents, focusedEvents, evNothing, evMouseDown
from vindauga.constants.option_flags import (ofSelectable, ofPreProcess, ofPostProcess, ofBuffered, ofValidate,
                                             ofCenterY, ofCenterX)
from vindauga.constants.state_flags import (sfVisible, sfActive, sfSelected, sfFocused, sfDragging, sfDisabled, sfModal,
                                            sfExposed)
from vindauga.events.event import Event

from .draw_buffer import BufferArray
from .point import Point
from .screen import Screen
from .view import View

logger = logging.getLogger(__name__)


@dataclass
class HandleStruct:
    event: Event
    group: 'Group'

    def __repr__(self):
        return '<HandleStruct event={} :: group={}>'.format(self.event, self.group)


@dataclass
class SetBlock:
    def __init__(self):
        self.state = 0
        self.enable = False


class Group(View):
    """
    `Group` objects and their derivatives (called groups for short) provide the
    central driving power to vindauga.

    A group is a special breed of view. In addition to all the members derived
    from `View`, a group has additional members and many overrides that allow it
    to control a dynamically linked list of views (including other groups) as
    though they were a single object.

    We often talk about the subviews of a group even when these subviews are
    often groups in their own right.

    Although a group has a rectangular boundary from its `View` ancestry, a
    group is only visible through the displays of its subviews. A group draws
    itself via the `draw()` methods of its subviews. A group owns its
    subviews, and together they must be capable of drawing (filling) the
    group's entire rectangular bounds.

    During the life of an application, subviews are created, inserted into
    groups, and displayed as a result of user activity and events generated by
    the application itself. The subviews can just as easily be hidden, deleted
    from the group, or disposed of by user actions (such as closing a window or
    quitting a dialog box).

    Three derived object types of `Group`, namely `Window`, `Desktop`,
    and `Application` (via `Program`) illustrate the group and subgroup concept.
    The application typically owns a desktop object, a status line object, and a
    menu view object. `Desktop is a `Group` derivative, so it, in turn, can own
    `Window` objects, which in turn own `Frame` objects, `ScrollBar` objects, and so on.

    `Group` overrides many of the basic `View` methods in a natural way.
    `Group` objects delegate both drawing and event handling to their subviews.
    You'll rarely construct an instance of `Group` itself; rather you'll
    usually use one or more of `Group`'s derived object types:
    `Application`, `Desktop`, and `Window`.
    """
    name = 'Group'

    def __init__(self, bounds):
        super().__init__(bounds)
        self.phase = self.phFocused
        self.buffer = None
        self.lockFlag = 0
        self.endState = 0
        self.options |= ofSelectable | ofBuffered
        self.clip = self.getExtent()
        self.eventMask = 0xFFFF
        self.current = None

    @property
    def last(self):
        return self.children[-1] if self.children else None

    @property
    def first(self):
        return self.children[0] if self.children else None

    @staticmethod
    def doCalcChange(view, delta):
        r = view.calcBounds(delta)
        view.changeBounds(r)

    @staticmethod
    def doAwaken(v, *_args):
        v.awaken()

    @staticmethod
    def doSetState(view, b):
        view.setState(b.state, b.enable)

    @staticmethod
    def hasMouse(child, event):
        return child.containsMouse(event)

    @staticmethod
    def doExpose(view, enable):
        if view.state & sfVisible:
            view.setState(sfExposed, enable)

    def doHandleEvent(self, child, eventHandle):
        if not child or (child.state & sfDisabled and eventHandle.event.what & (positionalEvents | focusedEvents)):
            return

        phase = eventHandle.group.phase
        if phase == self.phPreProcess and not (child.options & ofPreProcess):
            return
        elif phase == self.phPostProcess and not (child.options & ofPostProcess):
            return

        if eventHandle.event.what & child.eventMask:
            child.handleEvent(eventHandle.event)

    def shutdown(self):
        for view in reversed(self.children):
            view.hide()
        for view in reversed(self.children):
            self.destroy(view)

        self.children = []
        self.freeBuffer()
        self.current = None
        super().shutdown()

    def execView(self, v):
        if not v:
            return cmCancel

        saveOptions = v.options
        saveOwner = v.owner
        saveTopView = View.TheTopView
        saveCurrent = self.current
        saveCommands = copy.copy(self.getCommands())

        View.TheTopView = v
        v.options &= ~ofSelectable
        v.setState(sfModal, True)
        self.setCurrent(v, self.enterSelect)

        if not saveOwner:
            self.insert(v)

        try:
            return v.execute()
        except:
            logger.exception('exec view failed.')
        finally:
            if not saveOwner:
                try:
                    self.remove(v)
                except ValueError:
                    # Removed itself
                    pass

            self.setCurrent(saveCurrent, self.leaveSelect)
            v.setState(sfModal, False)
            v.options = saveOptions
            View.TheTopView = saveTopView
            self.setCommands(saveCommands)

    def execute(self):
        stillExecuting = True
        while stillExecuting:
            self.endState = 0
            handlingEvents = True
            while handlingEvents:
                e = Event(evNothing)
                self.getEvent(e)
                self.handleEvent(e)
                if e.what != evNothing:
                    logger.error('Event Error for %s', e)
                    self.eventError(e)
                    self.clearEvent(e)
                handlingEvents = self.endState == 0
            stillExecuting = not self.valid(self.endState)
        return self.endState

    def awaken(self):
        self.forEach(self.doAwaken, None)

    def resetCurrent(self):
        if not self.state & sfFocused or not self.current or self.current.valid(cmLoseFocus):
            self.setCurrent(self.firstMatch(sfVisible, ofSelectable), self.normalSelect)

    def setCurrent(self, view, mode):
        if self.current is view:
            return

        if self.state & sfFocused and not (not self.current or self.current.valid(cmLoseFocus)):
            return

        self.lock()
        try:
            self.__focusView(self.current, False)
            if mode != self.enterSelect and self.current:
                self.current.setState(sfSelected, False)
            if view and mode != self.leaveSelect:
                view.setState(sfSelected, True)
            if view and self.state & sfFocused:
                view.setState(sfFocused, True)
            self.current = view
        except Exception as e:
            logger.exception('focus failed: %s', e)
        finally:
            self.unlock()

    def selectNext(self, direction):
        if self.current:
            p = self.__findNext(direction)
            if p:
                p.select()

    def firstThat(self, func, *args) -> Optional[View]:
        if any(func((child := c), *args) is True for c in self.children):
            return child
        return None

    def focusNext(self, forwards):
        p = self.__findNext(forwards)
        if p:
            return p.focus()
        return True

    def firstMatch(self, state: int, options: int) -> Optional[View]:
        if not self.children:
            return None

        for c in [self.children[-1]] + self.children[:-1]:
            if (c.state & state) == state and (c.options & options) == options:
                return c
        return None

    def indexOf(self, view: View) -> int:
        try:
            return self.children.index(view)
        except ValueError:
            return -1

    def setState(self, state: int, enable: bool):
        sb = SetBlock()
        sb.state = state
        sb.enable = enable

        super().setState(state, enable)

        if state & (sfActive | sfDragging):
            self.lock()
            try:
                self.forEach(self.doSetState, sb)
            finally:
                self.unlock()

        if state & sfFocused:
            if self.current:
                self.current.setState(sfFocused, enable)

        if state & sfExposed:
            self.forEach(self.doExpose, enable)
            if not enable:
                self.freeBuffer()

    def handleEvent(self, event: Event):
        super().handleEvent(event)
        hs = HandleStruct(event, self)

        if event.what & focusedEvents:
            self.phase = self.phPreProcess
            self.forEach(self.doHandleEvent, hs)

            self.phase = self.phFocused
            self.doHandleEvent(self.current, hs)

            self.phase = self.phPostProcess
            self.forEach(self.doHandleEvent, hs)
        else:
            self.phase = self.phFocused
            if event.what & positionalEvents:
                p = self.firstThat(self.hasMouse, event)
                if p:
                    self.doHandleEvent(p, hs)
                elif event.what == evMouseDown:
                    Screen.makeBeep()
            else:
                self.forEach(self.doHandleEvent, hs)

    def drawSubViews(self, start, bottom=None):
        while start and start is not bottom:
            start.drawView()
            start = start.nextView()

    def changeBounds(self, bounds):
        d = Point()
        d.x = (bounds.bottomRight.x - bounds.topLeft.x) - self.size.x
        d.y = (bounds.bottomRight.y - bounds.topLeft.y) - self.size.y

        if d.x == 0 and d.y == 0:
            self.setBounds(bounds)
            self.drawView()
        else:
            self.freeBuffer()
            self.setBounds(bounds)
            self.clip = self.getExtent()
            self.getBuffer()
            self.lock()
            try:
                self.forEach(self.doCalcChange, d)
            finally:
                self.unlock()

    def consumesData(self):
        return any(c.consumesData() for c in self.children)

    def getData(self):
        children = (c for c in self.children if c.consumesData())
        data = []
        for c in children:
            data.append(c.getData())
        return data

    def setData(self, data):
        elements = zip((c for c in self.children if c.consumesData()), data)
        for c, data in elements:
            c.setData(data)

    def draw(self):
        if not self.buffer:
            self.getBuffer()
            if self.buffer:
                self.lockFlag += 1
                try:
                    self.redraw()
                finally:
                    self.lockFlag -= 1

        if self.buffer:
            self.writeBuf(0, 0, self.size.x, self.size.y, self.buffer)
        else:
            self.clip = self.getClipRect()
            self.redraw()
            self.clip = self.getExtent()

    def redraw(self):
        self.drawSubViews(self.first)

    def lock(self):
        if self.buffer or self.lockFlag:
            self.lockFlag += 1

    def unlock(self):
        if self.lockFlag:
            self.lockFlag -= 1
            if not self.lockFlag:
                self.drawView()

    def resetCursor(self):
        if self.current:
            self.current.resetCursor()

    def endModal(self, command: int):
        if self.state & sfModal:
            self.endState = command
        else:
            super().endModal(command)

    def eventError(self, event):
        if self.owner:
            self.owner.eventError(event)

    def getHelpCtx(self):
        h = hcNoContext

        if self.current:
            h = self.current.getHelpCtx()
        if h == hcNoContext:
            h = super().getHelpCtx()
        return h

    def valid(self, command: int) -> bool:
        if command == cmLoseFocus:
            return True

        if command == cmReleasedFocus:
            if self.current and (self.current.options & ofValidate):
                return self.current.valid(command)
            return True

        return self.firstThat(self.__isInvalid, command) is None

    def freeBuffer(self):
        if (self.options & ofBuffered) and self.buffer:
            self.buffer = None

    def getBuffer(self):
        if self.state & sfExposed:
            if (self.options & ofBuffered) and not self.buffer:
                self.buffer = BufferArray()

    def insert(self, p):
        self.insertBefore(p, self.first)

    def insertBefore(self, view, target):
        if view and not view.owner and (not target or target.owner is self):
            if view.options & ofCenterX:
                view.origin.x = (self.size.x - view.size.x) // 2

            if view.options & ofCenterY:
                view.origin.y = (self.size.y - view.size.y) // 2

            saveState = view.state
            view.hide()
            self.insertView(view, target)

            if saveState & sfVisible:
                view.show()
            if saveState & sfActive:
                view.setState(sfActive, True)

    def removeView(self, view):
        if self.children:
            self.children.remove(view)

    def insertView(self, view, target=None):
        view.owner = self
        if target:
            idx = self.children.index(target)
            self.children.insert(idx, view)
        else:
            self.children.append(view)

    def remove(self, view):
        if not view:
            return

        saveState = view.state
        view.hide()
        self.removeView(view)
        view.owner = None
        if saveState & sfVisible:
            view.show()

    def forEach(self, func, *args):
        for c in self.children:
            func(c, *args)

    @staticmethod
    def __isInvalid(view: View, command: int) -> bool:
        return not view.valid(command)

    def __findNext(self, forwards):
        if not self.current:
            return None

        idx = self.children.index(self.current)
        if forwards:
            kids = cycle(self.children)
            kids = islice(kids, idx + 1, idx + 1 + len(self.children))
        else:
            kids = cycle(reversed(self.children))
            kids = islice(kids, len(self.children) - idx, 2 * len(self.children) - idx)

        for p in kids:
            if p is self.current or ((p.state & (sfVisible | sfDisabled)) == sfVisible) and (p.options & ofSelectable):
                if p is not self.current:
                    return p
                break
        return None

    def __focusView(self, p, enable):
        if self.state & sfFocused and p and (not self.current or self.current.valid(cmLoseFocus)):
            p.setState(sfFocused, enable)
