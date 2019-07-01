# -*- coding: utf-8 -*-
import logging
import sys

from vindauga.constants.command_codes import (cmClose, cmNext, cmPrev, cmZoom, cmResize, cmReleasedFocus, cmCancel,
                                              cmReceivedFocus,
                                              hcNoContext, hcDragging
                                              )
from vindauga.constants.drag_flags import dmDragMove, dmDragGrow, dmLimitLoX, dmLimitLoY, dmLimitHiX, dmLimitHiY
from vindauga.constants.grow_flags import gfGrowLoX, gfGrowLoY, gfGrowHiX, gfGrowHiY, gfGrowRel, gfFixed
from vindauga.constants.event_codes import evMouseDown, evKeyDown, evMouseMove, evNothing, evBroadcast, evMouseUp, \
    evCommand
from vindauga.constants.keys import (kbLeft, kbRight, kbUp, kbDown, kbCtrlLeft, kbCtrlRight, kbShift, kbHome, kbEnd,
                                     kbPgUp, kbPgDn, kbEsc, kbEnter)
from vindauga.constants.option_flags import ofSelectable, ofTopSelect, ofFirstClick, ofValidate
from vindauga.constants.state_flags import (sfVisible, sfCursorVis, sfCursorIns, sfShadow, sfSelected,
                                            sfFocused, sfDragging, sfDisabled, sfModal, sfExposed)
from vindauga.events.event import Event
from vindauga.misc.message import message
from vindauga.misc.util import clamp
from .command_set import CommandSet
from .draw_buffer import DrawBuffer, BufferArray, LINE_WIDTH
from .palette import Palette
from .point import Point
from .rect import Rect
from .screen import Screen
from .vindauga_object import VindaugaObject

logger = logging.getLogger('vindauga.types.view')

SHADOW_SIZE = Point(2, 1)
SHADOW_ATTR = 0x08


def initCommands():
    temp = CommandSet()
    for i in range(256):
        if i not in {cmZoom, cmClose, cmResize, cmNext, cmPrev}:
            temp.enableCmd(i)
    return temp


class TargetContext:
    def __init__(self, context=None):
        self.target = None
        self.offset = 0
        self.y = 0
        self.__saved = []
        if context:
            self.restore(context)

    def restore(self, context):
        self.y = context.y
        self.offset = context.offset
        self.target = context.target

    def __enter__(self):
        self.__saved.append(TargetContext(self))
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.restore(self.__saved.pop())


class View(VindaugaObject):
    """
     The base of all visible objects.

     Most programs make use of the `View` derivatives: `Frame`,
    `ScrollBar`, `Scroller`, `ListViewer`, `Group`, and
    `Window` objects.

    `View` objects are rarely instantiated in programs. The `View`
    class exists to provide basic data and functionality for its derived
    classes. You'll probably never need to construct an instance of `View`
    itself, but most of the common behavior of visible elements in applications
    comes from `View`.
    """
    name = 'View'

    phFocused = 0
    phPreProcess = 1
    phPostProcess = 2

    normalSelect = 0
    enterSelect = 1
    leaveSelect = 2

    # Static friends
    curCommandSet = initCommands()
    commandSetChanged = False
    showMarkers = False
    errorAttr = 0xCF

    MOVE_COMMANDS = {kbLeft: Point(-1, 0),
                     kbRight: Point(1, 0),
                     kbUp: Point(0, -1),
                     kbDown: Point(0, 1),
                     kbCtrlLeft: (-8, 0),
                     kbCtrlRight: (8, 0)}

    TheTopView = None

    def __init__(self, bounds):
        super().__init__()
        self.options = 0
        self.eventMask = (evMouseDown | evKeyDown | evCommand)
        self.state = sfVisible
        self.growMode = 0
        self.dragMode = dmLimitLoY
        self.helpCtx = hcNoContext
        self.owner = None
        self.origin = Point()
        self.size = Point()
        self.cursor = Point()
        self.setBounds(bounds)
        self.context = TargetContext()
        self.savedBuffer = None
        self.children = []

    @property
    def next(self):
        children = self.owner.children
        return children[(children.index(self) + 1) % len(children)]

    @property
    def prev(self):
        children = self.owner.children
        return children[(children.index(self) - 1) % len(children)]

    @property
    def TopView(self):
        if View.TheTopView:
            return View.TheTopView
        p = self
        while p and not (p.state & sfModal):
            p = p.owner
        return p

    @staticmethod
    def commandEnabled(command):
        return command > 255 or command in View.curCommandSet

    @staticmethod
    def disableCommands(commands):
        """
        Disables the commands specified in the `commands` argument. If the
        command set is changed by this call, `commandSetChanged` is set True.

        :param commands: Commands to to disable
        """
        View.commandSetChanged = View.commandSetChanged or (View.curCommandSet & commands)
        View.curCommandSet.disableCmd(commands)

    @staticmethod
    def disableCommand(command):
        """
        Disables the given command. If the  command set is changed by the call, `commandSetChanged` is set True.
        :param command: Command to disable
        """
        View.commandSetChanged = View.commandSetChanged or command in View.curCommandSet
        View.curCommandSet.disableCmd(command)

    @staticmethod
    def enableCommands(commands):
        """
        Enables all the commands in the `commands` argument. If the
        command set is changed by this call, `commandSetChanged` is set True.

        :param commands: Commands to enable
        """
        View.commandSetChanged = View.commandSetChanged or (View.curCommandSet & commands) != commands
        View.curCommandSet.enableCmd(commands)

    @staticmethod
    def enableCommand(command):
        """
        Enables the given command. If the command set is changed by this call, `commandSetChanged` is set True.

        :param command: Command to enable
        """
        View.commandSetChanged = View.commandSetChanged or command not in View.curCommandSet
        View.curCommandSet.enableCmd(command)

    @staticmethod
    def getCommands():
        """
        Returns the current command set
        :return: `CommandSet` object
        """
        return View.curCommandSet

    @staticmethod
    def setCommands(commands):
        """
        Changes the current command set to the given `commands` argument

        :param commands: Commands to set
        """
        View.commandSetChanged = View.commandSetChanged or View.curCommandSet != commands
        View.curCommandSet = commands

    @staticmethod
    def setCmdState(commands, enable):
        """
        Set or disable commands

        :param commands: Command set to change
        :param enable: True to enable
        """
        if enable:
            View.enableCommands(commands)
        else:
            View.disableCommands(commands)

    def doRefresh(self):
        if Screen.lockRefresh:
            return
        if self.owner and not self.owner.lockFlag:
            Screen.refresh()

    def shutdown(self):
        self.hide()
        if self.owner:
            self.owner.remove(self)
        super().shutdown()

    def sizeLimits(self, minLimit, maxLimit):
        """
        Sets, in the `minLimit` and `maxLimit` arguments, the minimum and maximum values
        that `size` data member may assume.

        The default `View.sizeLimits` returns (0, 0) in `minLimit` and `owner.size`
        in `maxLimit`. If `owner` data member is 0, `maxLimit.x' and `maxLimit.y' are both
        set to `sys.maxsize`.

        :param minLimit: minimum size limit
        :param maxLimit: maximum size limit
        """
        minLimit.x = minLimit.y = 0
        if not (self.growMode & gfFixed) and self.owner:
            maxLimit.x = self.owner.size.x
            maxLimit.y = self.owner.size.y
        else:
            maxLimit.x = maxLimit.y = sys.maxsize

    def getBounds(self):
        """
        Returns the current value of size, the bounding rectangle of the view
        in its owner's coordinate system.

        :return: `Rect` with the bounding area
        """
        os = self.origin + self.size
        return Rect(self.origin.x, self.origin.y, os.x, os.y)

    def getExtent(self):
        """
        Returns the extent rectangle of the view with 0, 0 in the topLeft

        :return: `Rect` with the bounding area
        """
        return Rect(0, 0, self.size.x, self.size.y)

    def getClipRect(self):
        """
        Returns the clipping rectangle: the smallest rectangle which needs
        to be redrawn in a `draw()` call.

        For complicated views, `draw()` can use `getClipRect()` to improve
        performance.

        :return: `Rect` with clipping rectangle
        """
        clip = self.getBounds()
        if self.owner:
            clip.intersect(self.owner.clip)
        clip.move(-self.origin.x, -self.origin.y)
        return clip

    def mouseInView(self, mouse):
        """
        Returns True if the `mouse` argument (given in global coordinates) is
        within the calling view. Call `makeGlobal` and `makeLocal` to
        convert one point between different coordinate systems.

        :param mouse: `Point` representing the mouse
        :return: True if the global mouse coordinates in inside this view
        """
        mouse = self.makeLocal(mouse)
        r = self.getExtent()
        return mouse in r

    def containsMouse(self, event):
        """
        Returns True if a mouse event occurs inside the calling view, otherwise
        returns False. Returns True if the view is visible and the mouse
        coordinates (defined in `event.mouse.where') are within this view.

        :param event: Mouse `Event`
        :return: True if the mouse is inside this view
        """

        return (self.state & sfVisible) and self.mouseInView(event.mouse.where)

    def locate(self, bounds):
        """
        Changes the bounds of the view to those of the `bounds` argument.
        The view is redrawn in its new location.

        `locate()` calls `sizeLimits()` to verify that the given bounds are
        valid, and then calls `changeBounds()` to change the bounds and
        redraw the view.

        :param bounds: bounds to relocate the view to
        """
        minBounds = Point()
        maxBounds = Point()
        self.sizeLimits(minBounds, maxBounds)

        bounds.bottomRight.x = bounds.topLeft.x + clamp(bounds.bottomRight.x - bounds.topLeft.x, minBounds.x,
                                                        maxBounds.x)
        bounds.bottomRight.y = bounds.topLeft.y + clamp(bounds.bottomRight.y - bounds.topLeft.y, minBounds.y,
                                                        maxBounds.y)

        r = self.getBounds()

        if bounds != r:
            self.changeBounds(bounds)
            if self.owner and (self.state & sfVisible):
                if self.state & sfShadow:
                    r.union(bounds)
                    r.bottomRight += SHADOW_SIZE
                self.drawUnderRect(r, None)

    def dragView(self, event, mode, limits, minSize, maxSize):
        """
        Drags the view in the ways specified by the `mode` argument, that is
        interpreted like the `growMode` data member.

        `limits` specifies the rectangle (in the owner's coordinate system)
        within which the view can be moved, and `minSize` and `maxSize` specify the
        minimum and maximum sizes the view can shrink or grow to.

        The event leading to the dragging operation is needed in `event` to
        distinguish mouse dragging from use of the cursor keys.

        :param event: Originating event
        :param mode: drag mode
        :param limits: Limits allowed for dragging
        :param minSize: Minimum size
        :param maxSize: Maximim size
        """
        self.setState(sfDragging, True)

        if event.what == evMouseDown:
            self.__handleMouseDownDrag(event, mode, limits, minSize, maxSize)
        else:
            self.__handleKeyDownDrag(event, mode, limits, minSize, maxSize)

        self.setState(sfDragging, False)

    def calcBounds(self, delta):
        """
        When a view's owner changes size, the owner repeatedly calls
        `calcBounds()` and `changeBounds()` for all its subviews.

        `calcBounds()` must calculate the new bounds of the view given that its
        owner's size has changed by `delta`, and return the new bounds in
        `bounds`.

        `calcBounds()` calculates the new bounds using the flags specified
        in `growMode` data member.

        :param delta: `Rect` with the change in size
        :return: `Rect` with new bounds
        """
        bounds = self.getBounds()
        gSize = self.owner.size.x
        gDelta = delta.x

        if self.growMode & gfGrowLoX:
            bounds.topLeft.x = self._grow(bounds.topLeft.x, gSize, gDelta)

        if self.growMode & gfGrowHiX:
            bounds.bottomRight.x = self._grow(bounds.bottomRight.x, gSize, gDelta)

        gSize = self.owner.size.y
        gDelta = delta.y

        if self.growMode & gfGrowLoY:
            bounds.topLeft.y = self._grow(bounds.topLeft.y, gSize, gDelta)

        if self.growMode & gfGrowHiY:
            bounds.bottomRight.y = self._grow(bounds.bottomRight.y, gSize, gDelta)

        minLim = Point()
        maxLim = Point()
        self.sizeLimits(minLim, maxLim)
        bounds.bottomRight.x = bounds.topLeft.x + clamp(bounds.bottomRight.x - bounds.topLeft.x, minLim.x, maxLim.x)
        bounds.bottomRight.y = bounds.topLeft.y + clamp(bounds.bottomRight.y - bounds.topLeft.y, minLim.y, maxLim.y)
        return bounds

    def changeBounds(self, bounds):
        """
        `changeBounds()` changes the view's bounds (`origin` and `size`
        data members) to the rectangle given by the `bounds` parameter.
        Having changed the bounds, `changeBounds()` redraws the view.

        `changeBounds()` is called by various `View` member functions, but should
        never be called directly.

        `changeBounds()` first calls `setBounds(bounds)` and then calls `drawView()`.

        :param bounds: New bounds
        """
        self.setBounds(bounds)
        self.drawView()

    def growTo(self, x, y):
        """
        Grows or shrinks the view to the given size using a call to `locate().`

        :param x: width to grow
        :param y: height to grow
        """
        r = Rect(self.origin.x, self.origin.y, self.origin.x + x, self.origin.y + y)
        self.locate(r)

    def moveTo(self, x, y):
        """
        Moves the origin to the point (x,y) relative to the owner's view. The view's size is unchanged.

        :param x: X coord to move to
        :param y: Y coord to move to
        """
        r = Rect(x, y, x + self.size.x, y + self.size.y)
        self.locate(r)

    def setBounds(self, bounds):
        """
        Sets the bounding rectangle of the view to the value given by the
        `bounds` parameter. The `origin` data member is set to `bounds.topLeft',
        and the `size` data member is set to the difference between `bounds.bottomRight' and `bounds.topLeft'.

        The `setBounds()` member function is intended to be called only from
        within an overridden `changeBounds()` member function. You should never call `setBounds()` directly.

        :param bounds: Bounds to resize to
        """
        self.origin = Point(bounds.topLeft.x, bounds.topLeft.y)
        self.size = bounds.bottomRight - bounds.topLeft

    def getHelpCtx(self):
        """
        `getHelpCtx()` returns the view's help context. The default `getHelpCtx()`
        returns the value in the `helpCtx` data member, or returns `hcDragging` if the view is being dragged
        (see `sfDragging`).

        :return: A Help context
        """
        if self.state & sfDragging:
            return hcDragging
        return self.helpCtx

    def valid(self, command):
        """
        Use this member function to check the validity of a view after it has
        been constructed or at the point in time when a modal state ends (due
        to a call to `endModal()`).

        A `command` argument of `cmValid` (zero) indicates that the view should
        check the result of its constructor: `valid(cmValid)` should return True
        if the view was successfully constructed and is now ready to be used,
        False otherwise.

        Any other `command` argument indicates that the current modal state
        (such as a modal dialog box) is about to end with a resulting
        value of `command`. In this case, `valid()` should check the validity of
        the view.

        It is the responsibility of `valid()` to alert the user in case the view
        is invalid. The default `View.valid()` simply returns True.

        :param command: A command code
        :return: True if view is valid
        """
        return True

    def hide(self):
        """
        Hides the view by calling `setState()` to clear the `sfVisible` flag in the `state` data member.
        """
        if self.state & sfVisible:
            self.setState(sfVisible, False)

    def show(self):
        """
        If the view is `sfVisible`, nothing happens. Otherwise, `show()`
        displays the view by calling `setState()` to set the `sfVisible`
        flag in `state` data member.
        """
        if not self.state & sfVisible:
            self.setState(sfVisible, True)

    def draw(self):
        """
        Draws the view on the screen.

        Called whenever the view must draw (display) itself. `draw()` must cover
        the entire area of the view.

        This member function must be overridden appropriately for each derived
        class. draw() is seldom called directly, since it is more efficient to
        use @ref drawView(), which draws only views that are exposed; that is,
        some or all of the view is visible on the screen.

        If required, draw can call `getClipRect()` to obtain the rectangle
        that needs redrawing, and then only draw that area. For complicated
        views, this can improve performance noticeably.

        To perform its task, `draw()` usually uses a `DrawBuffer` object.
        """
        b = DrawBuffer()
        b.moveChar(0, ' ', self.getColor(1), self.size.x)
        self.writeLine(0, 0, self.size.x, self.size.y, b)

    def drawView(self):
        """
        Draws the view on the screen.

        Calls `draw()` if `exposed()` returns True, indicating that the
        view is exposed (see `sfExposed`). If `exposed()` returns False,
        `drawView()` does nothing.

        You should call `drawView()` (not `draw()`) whenever you need to redraw a
        view after making a change that affects its visual appearance.
        """
        exposed = self.exposed()
        if exposed:
            self.draw()
            self.drawCursor()

    def exposedChildren(self, left, right, siblings, context):
        for i, child in enumerate(siblings):
            if child is context.target:
                return self.exposedParent(left, right, child.owner)

            if (not (child.state & sfVisible)) or context.y < child.origin.y:
                continue

            if context.y < child.origin.y + child.size.y:
                if left < child.origin.x:
                    if right <= child.origin.x:
                        continue
                    if right > child.origin.x + child.size.x:
                        _siblings = siblings[i + 1:]
                        if self.exposedChildren(left, child.origin.x, _siblings, context):
                            return True
                        left = child.origin.x + child.size.x
                    else:
                        right = child.origin.x
                else:
                    if left < child.origin.x + child.size.x:
                        left = child.origin.x + child.size.x
                    if left >= right:
                        return False

    def exposedParent(self, left, right, item):
        if not (item.state & sfVisible):
            return False

        if (not item.owner) or item.owner.buffer:
            return True

        with self.context as context:
            context.y += item.origin.y

            left += item.origin.x
            right += item.origin.x
            context.target = item

            group = item.owner
            # Is my parent overlapping me?
            if not group.clip.topLeft.y <= context.y < group.clip.bottomRight.y:
                return False

            left = max(left, group.clip.topLeft.x)
            right = min(right, group.clip.bottomRight.x)

            if left >= right:
                return False

            return self.exposedChildren(left, right, group.children, context)

    def exposed(self):
        """
        Checks if the view is exposed.

        Returns True if any part of the view is visible on the screen. The view
        is exposed if:

        * it has the `sfExposed` bit set in `state` data member
        * it has the `sfVisible` bit set in `state` data member
        * its coordinates make it fully or partially visible on the screen.

        :return: True if the view is exposed
        """
        if (not (self.state & sfExposed)) or self.size.x <= 0 or self.size.y <= 0:
            return False

        return any(self.exposedParent(0, self.size.x, self) for self.context.y in range(self.size.y))

    def focus(self):
        """
        Tries to grab the focus.

        The view can grab the focus if:

        * the view is not selected (bit `sfSelected` cleared in `state`)
        * the view is not modal (bit `sfModal` cleared in `state`)
        * the owner exists and it is focused

        If all the above conditions are True, the `focus()` method calls
        `select()` to get the focus.

        :return: True if the view grabbed focus
        """
        result = True

        if self.state & (sfSelected | sfModal) == 0 and self.owner:
            result = self.owner.focus()
            if result:
                if (not self.owner.current or
                        not self.owner.current.options & ofValidate or
                        self.owner.current.valid(cmReleasedFocus)):
                    self.select()
                else:
                    return False
        return result

    def hideCursor(self):
        """
        Hides the cursor by calling `setState()` to clear the
        `sfCursorVis` flag in the `state` data member.
        """
        self.setState(sfCursorVis, False)

    def drawHide(self, lastView):
        """
        Calls `drawCursor()` followed by `drawUnderView()`. The latter
        redraws all subviews (with shadows if required) until the given
        `lastView` is reached.

        :param lastView: Last view of the subviews to draw
        """
        self.drawCursor()
        self.drawUnderView(bool(self.state & sfShadow), lastView)

    def drawShow(self, lastView):
        """
        Calls `drawView()`, then if `state` data member has the
        `sfShadow` bit set, `drawUnderView()` is called to draw the
        shadow.

        :param lastView: Last view of the subviews to draw
        """
        self.drawView()
        if self.state & sfShadow:
            self.drawUnderView(True, lastView)

    def drawUnderRect(self, r, lastView):
        """
        Calls `owner.clip.intersect(r)` to set the area that needs drawing.
        Then, all the subviews from the next view to the given `lastView` are
        drawn using `drawSubViews()`. Finally, `owner.clip` is reset to
        owner.getExtent().

        :param r: Rectangle to draw under
        :param lastView: Last view of the subviews to draw
        """
        self.owner.clip.intersect(r)
        self.owner.drawSubViews(self.nextView(), lastView)
        self.owner.clip = self.owner.getExtent()

    def drawUnderView(self, doShadow, lastView):
        """
        Calls `drawUnderRect(r, lastView)`, where `r` is the calling view's
        current bounds. If `doShadow` is True, the view's bounds are first
        increased by shadowSize.

        :param doShadow: Draw shadows?
        :param lastView: Last view of the subviews to draw
        """
        r = self.getBounds()
        if doShadow:
            r.bottomRight += SHADOW_SIZE
        self.drawUnderRect(r, lastView)

    def consumesData(self):
        """
        Any non-zero returns indicates the view can get and set data
        :return:
        """
        return False

    def getData(self):
        """
        getData() must copies data from the view to the data record . The data record mechanism is
        typically used only in views that implement controls for dialog boxes.
        """
        pass

    def setData(self, rec):
        """
        setData() copies data from the data record to the view. The data record mechanism is
        typically used only in views that implement controls for dialog boxes.
        """
        pass

    def awaken(self):
        pass

    def blockCursor(self):
        """
        Sets `sfCursorIns` in `state` data member to change the cursor
        to a solid block. The cursor will only be visible if `sfCursorVis`
        is also set (and the view is visible).
        """
        self.setState(sfCursorIns, True)

    def normalCursor(self):
        """
        Clears the `sfCursorIns` bit in `state` data member, thereby
        making the cursor into an underline. If `sfCursorVis` is set, the
        new cursor will be displayed.
        """
        self.setState(sfCursorIns, False)

    def resetCursor(self):
        """
        Resets the cursor
        """
        if self.state & (sfVisible | sfCursorVis | sfFocused) == (sfVisible | sfCursorVis | sfFocused):
            p = self
            cur = Point()
            cur.x = self.cursor.x
            cur.y = self.cursor.y

            while True:
                if not (0 <= cur.x < p.size.x and 0 <= cur.y < p.size.y):
                    break

                cur.x += p.origin.x
                cur.y += p.origin.y
                p2 = p
                owner = p.owner
                if not owner:
                    if self.state & sfCursorIns:
                        Screen.setBigCursor()
                    else:
                        Screen.setSmallCursor()
                    Screen.moveCursor(cur.x, cur.y)
                    Screen.drawCursor(1)
                    return

                if not (owner.state & sfVisible):
                    break

                for p in owner.children:
                    if p == p2:
                        p = p.owner
                        # continue outer loop
                        break

                    if ((p.state & sfVisible) and
                            p.origin.x <= cur.x < p.size.x + p.origin.x and
                            p.origin.y <= cur.y < p.size.y + p.origin.y):
                        Screen.drawCursor(0)
                        return
        Screen.drawCursor(0)

    def setCursor(self, x, y):
        """
        Moves the (virtual) hardware cursor to the point (x, y) using view-relative
        (local) coordinates. (0, 0) is the top-left corner.

        :param x: X coordinate to move to
        :param y: Y coordinate to move to
        """
        self.cursor.x = x
        self.cursor.y = y
        self.drawCursor()

    def showCursor(self):
        """
        Turns on the hardware cursor by setting the `sfCursorVis` bit in
        `state` data member. Note that the cursor is invisible by default.
        """
        self.setState(sfCursorVis, True)

    def drawCursor(self):
        """
        If the view is `sfFocused`, the cursor is reset with a call to `resetCursor()`
        """
        if self.state & sfFocused:
            self.resetCursor()

    def clearEvent(self, event: Event):
        """
        Standard member function used in `handleEvent()` to signal that the
        view has successfully handled the event.

        Sets `event.what` to `evNothing` and `event.message.infoPtr` to `self`.

        :param event: Event to clear.
        """
        event.clear(self)
        event.what = evNothing

    def eventAvail(self):
        """
        Calls `getEvent()` and returns True if an event is available. Calls
        `putEvent()` to set the event as pending.

        :return: True if an event is pending
        """
        event = Event(evNothing)
        self.getEvent(event)
        if event.what != evNothing:
            self.putEvent(event)
        return event.what != evNothing

    def getEvent(self, event: Event):
        """
        Returns the next available event in the `event` argument. Returns
        `evNothing` if no event is available. By default, it calls the
        view's owner's `getEvent()`.

        :param event: Event to modify with pending event
        """
        if self.owner:
            self.owner.getEvent(event)

    def handleEvent(self, event: Event):
        """
        `handleEvent()` is the central member function through which all
        event handling is implemented. The `what` data member of the
        `event` parameter contains the event class (evXXXX), and the remaining
        `event` data members further describe the event.

        To indicate that it has handled an event, `handleEvent()` should call
        `clearEvent()`. `handleEvent()` is almost always overridden in derived
        classes.

        The default `handleEvent()` handles `evMouseDown` events as
        follows:

        If the view is:

        * not selected (see `sfSelected` in `state`)
        * and not disabled (see `sfDisabled` in `state`)
        * and if the view is selectable (see `ofSelectable` in
          `options`

        then the view selects itself by calling `select()`. No other events
        are handled by the default `handleEvent()`.

        :param event: Event to handle
        """
        if event.what == evMouseDown:
            if (not (self.state & (sfSelected | sfDisabled))) and self.options & ofSelectable:
                if not self.focus() or not (self.options & ofFirstClick):
                    self.clearEvent(event)

    def putEvent(self, event):
        """
        Puts the event given by `event` into the event queue, causing it to be
        available to be returned by `getEvent()`.

        Often used by views to generate command events; for example,

        ```
        event.what = evCommand
        event.command = cmSaveAll
        event.infoPtr = None
        self.putEvent(event)
        ```

        The default TView::putEvent() calls the view's owner's putEvent().

        :param event: The event to put
        """
        if self.owner:
            self.owner.putEvent(event)

    def endModal(self, command):
        """
        Calls `TopView()` to seek the top most modal view. If there is none
        such (that is, if TopView() returns None) no further action is taken. If
        there is a modal view, that view calls `endModal()`, and so on.

        The net result is that `endModal()` terminates the current modal state.
        The `command` argument is passed to the `Group.execView()` that
        created the modal state in the first place.

        :param command: Command to pass
        """
        if self.TopView:
            self.TopView.endModal(command)

    def execute(self):
        """
        Is called from `Group.execView()` whenever a view becomes modal.
        If a view is to allow modal execution, it must override `execute()` to
        provide an event loop. The value returned by `execute()` will be the
        value returned by `Group.execView()`.

        The default `execute()` simply returns cmCancel.
        :return:
        """
        return cmCancel

    def getColor(self, color):
        """
        Maps the palette indices in the low and high bytes of `color` into
        physical character attributes by tracing through the palette of the
        view and the palettes of all its owners.

        :param color: Color to map
        :return: Color pair
        """
        colorPair = (color >> 8) & 0xFF
        if colorPair:
            colorPair = self.mapColor(colorPair) << 8
        colorPair |= self.mapColor(color & 0xFF)
        return colorPair

    def getPalette(self):
        """
        `getPalette()` returns `Palette` object representing the view's palette.

        This can be 0 (empty string) if the view has no palette. `getPalette()`
        is called by `writeChar()` and `writeStr()` when converting
        palette indices to physical character attributes.

        The default return value of 0 causes no color translation to be
        performed by this view. getPalette() is almost always overridden in
        derived classes.

        :return: `Palette` object
        """
        return Palette('')

    def mapColor(self, color):
        """
        Maps the given color to an offset into the current palette. `mapColor()`
        works by calling `getPalette()` for each owning group in the chain.

        It successively maps the offset in each palette until the ultimate
        owning palette is reached.

        If `color` is invalid (for example, out of range) for any of the
        palettes encountered in the chain, `mapColor()` returns `errorAttr`.

        :param color: Color to map
        :return: Color
        """
        if not color:
            return self.errorAttr

        current = self
        while current:
            palette = current.getPalette()
            paletteLen = len(palette)
            if paletteLen:
                if color > paletteLen:
                    return self.errorAttr
                color = palette[color]
                if color == 0:
                    return self.errorAttr
            current = current.owner
        return color

    def getState(self, state):
        """
        Returns True if the state given in `state` is set in the data member
        `state.`

        :param state: State to check
        :return: True if state is set
        """
        return (self.state & state) == state

    def select(self):
        """
        Selects the view (see `sfSelected`). If the view's owner is focused,
        then the view also becomes focused (see `sfFocused`).

        If the view has the `ofTopSelect` flag set in its `options` data
        member, then the view is moved to the top of its owner's subview list
        (using a call to `makeFirst()`).
        """
        if not (self.options & ofSelectable):
            return
        if self.options & ofTopSelect:
            self.makeFirst()
        elif self.owner:
            self.owner.setCurrent(self, self.normalSelect)

    def setState(self, state, enable):
        """
        Sets or clears a state flag in the `state` data member.
        The `state` parameter specifies the state flag to modify, and the
        `enable` parameter specifies whether to turn the flag off (False) or
        on (True).

        `setState()` then carries out any appropriate action to reflect the new
        state, such as redrawing views that become exposed when the view is
        hidden (`sfVisible`).

        `setState()` is sometimes overridden to trigger additional actions that
        are based on state flags. Another common reason to override `setState()`
        is to enable or disable commands that are handled by a particular view.

        :param state: State to set
        :param enable: True to enable
        """

        if enable:
            self.state |= state
        else:
            self.state &= ~state

        if not self.owner:
            return

        if state == sfVisible:
            if self.owner.state & sfExposed:
                self.setState(sfExposed, enable)

            if enable:
                self.drawShow(None)
            else:
                self.drawHide(None)

            if self.options & ofSelectable:
                self.owner.resetCurrent()

        elif state in {sfCursorVis, sfCursorIns}:
            self.drawCursor()
        elif state == sfShadow:
            self.drawUnderView(True, None)
        elif state == sfFocused:
            self.resetCursor()
            command = cmReceivedFocus if enable else cmReleasedFocus
            message(self.owner, evBroadcast, command, self)

    def keyEvent(self, event):
        """
        Returns, in the `event` variable, the next `evKeyDown` event.
        It waits, ignoring all other events, until a keyboard event becomes
        available.

        :param event: Event to modify
        """
        keyIsDown = True
        while keyIsDown:
            self.getEvent(event)
            keyIsDown = (event.what == evKeyDown)

    def mouseEvent(self, event, mask):
        """
        Sets the next mouse event in the `event` argument.
        Returns True if this event is in the `mask` argument. Also returns
        False if an `evMouseUp` event occurs.

        This member function lets you track a mouse while its button is down;
        for example, in drag block-marking operations for text editors.

        :param event: Event to modify
        :param mask: Mouse masks to wait for
        :return: Boolean indicating mouse up
        """
        mouseIsDown = True
        mask |= evMouseUp
        while mouseIsDown:
            self.getEvent(event)
            mouseIsDown = not (event.what & mask)
        return event.what != evMouseUp

    def makeGlobal(self, source):
        """
        Converts the `source` point coordinates from local (view) to global
        (screen) and returns the result.

        :param source: Source point
        :return: Global point
        """
        temp = source + self.origin
        cur = self
        while cur.owner:
            cur = cur.owner
            temp += cur.origin
        return temp

    def makeLocal(self, source):
        """
        Converts the `source` point coordinates from global (screen) to local
        (view) and returns the result.

        Useful for converting the event.where data member of an evMouse event
        from global coordinates to local coordinates.

        :param source: Source point
        :return: local coordinates
        """
        temp = source - self.origin
        cur = self
        while cur.owner:
            cur = cur.owner
            temp -= cur.origin
        return temp

    def nextView(self):
        """
        Returns the next subview in the owner's subview list. None is returned if the
        calling view is the last one in its owner's list.

        :return: Next view or None
        """
        if self is self.owner.last:
            return None
        return self.next

    def prevView(self):
        """
        Returns the previous subview in the owner's subview list. None is returned if the
        calling view is the first one in its owner's list.

        :return: Next view or None
        """
        if self is self.owner.first:
            return None
        return self.prev

    def makeFirst(self):
        """
        Moves the view to the top of its owner's subview list. A call to
        `makeFirst()` corresponds to `putInFrontOf(owner.first())`.
        """
        self.putInFrontOf(self.owner.first)

    def putInFrontOf(self, target):
        """
        Moves the calling view in front of the `target` view in the owner's
        subview list. The call

        ```
        MyView.putInFrontOf(owner.first);
        ```

        is equivalent to `MyView.makeFirst()`. This member function works by
        changing pointers in the subview list.

        Depending on the position of the other views and their visibility
        states, putInFrontOf() may obscure (clip) underlying views.

        If the view is selectable (see `ofSelectable`) and is put in front
        of all other subviews, then the view becomes selected.

        :param target: Target view to place in front of
        """
        if (self.owner and target is not self and target is not self.nextView() and
                (not target or target.owner is self.owner)):

            if not self.state & sfVisible:
                self.owner.removeView(self)
                self.owner.insertView(self, target)
            else:
                lastView = self.nextView()
                index = self.owner.children.index
                if (not (self in self.owner.children)) or index(target) < index(self):
                    lastView = target

                self.state &= ~sfVisible

                if lastView is target:
                    self.drawHide(target)

                self.owner.removeView(self)
                self.owner.insertView(self, target)
                self.state |= sfVisible

                if lastView is not target:
                    self.drawShow(lastView)

                if self.options & ofSelectable:
                    self.owner.resetCurrent()

    def writeBuf(self, x, y, w, h, buf):
        """
        Writes the given buffer to the screen starting at the coordinates
        (x, y), and filling the region of width `w` and height `h`. Should only
        be used in `draw()` member functions.

        :param x: Left
        :param y: Top
        :param w: Width
        :param h: Height
        :param buf: Buffer
        """

        Screen.lockRefresh += 1
        try:
            for row in range(h):
                self.__writeView(x, x + w, y + row, buf[row * w: w * (row + 1)])
        finally:
            Screen.lockRefresh -= 1
        self.doRefresh()

    def writeChar(self, x, y, c, color, count):
        """
        Beginning at the point (x, y), writes `count` copies of the character
        `c` in the color determined by the color'th entry in the current view's
        palette. Should only be used in `draw()` functions.

        :param x: left
        :param y: top
        :param c: character
        :param color: color
        :param count: count
        """
        if x < 0:
            x = 0

        if x + count > LINE_WIDTH:
            return

        b = DrawBuffer()
        b.moveChar(0, c, self.mapColor(color), count)
        self.__writeView(x, x + count, y, b)

    def writeLine(self, x, y, w, h, buf):
        """
        Writes the line contained in the buffer `b` to the screen, beginning at
        the point (x, y) within the rectangle defined by the width `w` and the
        height `h`. If `h` is greater than 1, the line will be repeated `h`
        times. Should only be used in `draw()` member functions.

        :param x: left
        :param y: top
        :param w: width
        :param h: height
        :param buf: Buffer
        """
        if not h:
            return
        width = x + w
        Screen.lockRefresh += 1
        try:
            for row in range(y, y + h):
                self.__writeView(x, width, row, buf)
        finally:
            Screen.lockRefresh -= 1
        self.doRefresh()

    def writeStr(self, x, y, text, color):
        """
        Writes the string `text` with the color attributes of the color'th entry
        in the view's palette, beginning at the point (x, y). Should only be
        used in `draw()` member functions.

        :param x: left
        :param y: top
        :param text: text to write
        :param color: color
        """
        if not text:
            return

        textLen = len(text)
        b = DrawBuffer()
        b.moveStr(0, text, color)
        self.__writeView(x, x + textLen, y, b)

    def at(self, index):
        return self.children[index]

    def _grow(self, initial, size, delta):
        if self.growMode & gfGrowRel:
            initial = (initial * size + ((size - delta) >> 1)) // (size - delta)
        else:
            initial += delta
        return initial

    @staticmethod
    def __change(mode, delta, point, size, ctrlState):
        """
        Alter point and size depending on the drag/move mode

        :param mode: dragging mode
        :param delta: size delta
        :param point: point
        :param size: size
        :param ctrlState: ctrl state
        :return: point, size tuple (which are also modified in place).
        """
        if (mode & dmDragMove) and not (ctrlState & kbShift):
            point += delta
        elif (mode & dmDragGrow) and (ctrlState & kbShift):
            size += delta
        return point, size

    def __writeChildrenViewRec(self, left, right, children, shadowCounter, context):
        for i, view in enumerate(children):
            if view is context.target:
                if view.owner.buffer:
                    if not shadowCounter:
                        self.__paintWithoutShadow(context, view, left, right)
                    else:  # Paint with shadow
                        self.__paintWithShadow(context, view, left, right)

                    if view.owner.buffer is Screen.screenBuffer:
                        Screen.drawMouse(True)
                if not view.owner.lockFlag:
                    self.__writeViewRec2(left, right, view.owner, shadowCounter)
                return

            if (not (view.state & sfVisible)) or context.y < view.origin.y:
                continue

            if context.y < view.origin.y + view.size.y:
                if left < view.origin.x:
                    if right <= view.origin.x:
                        continue
                    _children = children[i + 1:]
                    self.__writeChildrenViewRec(left, view.origin.x, _children, shadowCounter, context)
                    left = view.origin.x

                if right <= view.origin.x + view.size.x:
                    return

                if left < view.origin.x + view.size.x:
                    left = view.origin.x + view.size.x

                if (view.state & sfShadow) and (context.y >= view.origin.y + SHADOW_SIZE.y):
                    if left < view.origin.x + view.size.x + SHADOW_SIZE.x:
                        shadowCounter += 1
                        if right > view.origin.x + view.size.x + SHADOW_SIZE.x:
                            _children = children[i + 1:]
                            self.__writeChildrenViewRec(left, view.origin.x + view.size.x + SHADOW_SIZE.x, _children,
                                                        shadowCounter, context)
                            left = view.origin.x + view.size.x + SHADOW_SIZE.x
                            shadowCounter -= 1
                        continue
                else:
                    continue

            if (view.state & sfShadow) and (context.y < view.origin.y + view.size.y + SHADOW_SIZE.y):
                if left < view.origin.x + SHADOW_SIZE.x:
                    if right <= view.origin.x + SHADOW_SIZE.x:
                        continue
                    _children = children[i + 1:]
                    self.__writeChildrenViewRec(left, view.origin.x + SHADOW_SIZE.x, _children, shadowCounter, context)
                    left = view.origin.x + SHADOW_SIZE.x

                if left >= view.origin.x + SHADOW_SIZE.x + view.size.x:
                    continue

                shadowCounter += 1

                if right > view.origin.x + view.size.x + SHADOW_SIZE.x:
                    _children = children[i + 1:]
                    self.__writeChildrenViewRec(left, view.origin.x + view.size.x + SHADOW_SIZE.x, _children,
                                                shadowCounter, context)
                    left = view.origin.x + view.size.x + SHADOW_SIZE.x
                    shadowCounter -= 1

    def __writeViewRec2(self, left, right, view, shadowCounter):
        if not (view.state & sfVisible) or not view.owner:
            return

        with self.context as context:
            context.y += view.origin.y
            left += view.origin.x
            right += view.origin.x
            context.offset += view.origin.x
            context.target = view

            group = view.owner

            if not (group.clip.topLeft.y <= context.y < group.clip.bottomRight.y):
                return

            left = max(left, group.clip.topLeft.x)
            right = min(right, group.clip.bottomRight.x)

            if left >= right:
                return

            self.__writeChildrenViewRec(left, right, group.children, shadowCounter, context)

    def __writeView(self, left, right, y, buf):

        if not (0 <= y < self.size.y):
            return

        left = max(left, 0)
        right = min(right, self.size.x)

        if left >= right:
            return

        with self.context as context:
            context.offset = left
            context.y = y

            self.savedBuffer = buf
            self.__writeViewRec2(left, right, self, 0)
            self.doRefresh()

    def __moveGrow(self, point, size, limits, minSize, maxSize, mode):
        size.x = min(max(size.x, minSize.x), maxSize.x)
        size.y = min(max(size.y, minSize.y), maxSize.y)

        point.x = min(max(point.x, limits.topLeft.x - size.x + 1), limits.bottomRight.x - 1)
        point.y = min(max(point.y, limits.topLeft.y - size.y + 1), limits.bottomRight.y - 1)

        if mode & dmLimitLoX:
            point.x = max(point.x, limits.topLeft.x)

        if mode & dmLimitLoY:
            point.y = max(point.y, limits.topLeft.y)

        if mode & dmLimitHiX:
            point.x = min(point.x, limits.bottomRight.x - size.x)

        if mode & dmLimitHiY:
            point.y = min(point.y, limits.bottomRight.y - size.y)

        r = Rect(point.x, point.y, point.x + size.x, point.y + size.y)
        self.locate(r)

    def __paintWithoutShadow(self, context, view, left, right):
        width = (right - left)
        pOwner = view.owner
        offset = context.offset
        soff = left - offset
        if pOwner.buffer is Screen.screenBuffer:
            # Write something to the screen.
            Screen.writeRow(left, context.y, self.savedBuffer[soff: soff + width], width)

        poff = pOwner.size.x * context.y + left
        pOwner.buffer[poff: poff + width] = BufferArray(self.savedBuffer[soff: soff + width])

    def __paintWithShadow(self, context, view, left, right):
        width = right - left
        dst1 = view.owner.size.x * context.y + left
        start = left - context.offset
        src = self.savedBuffer[start: start + width]
        for offset, d in enumerate(src):
            d = d & DrawBuffer.CHAR_MASK | (SHADOW_ATTR << DrawBuffer.CHAR_WIDTH)
            if view.owner.buffer is Screen.screenBuffer:
                Screen.writeRow(offset + left, context.y, [d], 1)
            view.owner.buffer[dst1 + offset] = d

    def __handleMouseDownDrag(self, event, mode, limits, minSize, maxSize):
        """
        Handle mouse down event
        """
        if mode & dmDragMove:
            point = self.origin - event.mouse.where
            working = True
            while working:
                event.mouse.where += point
                self.__moveGrow(event.mouse.where, self.size, limits, minSize, maxSize, mode)
                working = self.mouseEvent(event, evMouseMove)
            # Pop the window to the mouse-up coords
            event.mouse.where += point
            self.__moveGrow(event.mouse.where, self.size, limits, minSize, maxSize, mode)
        else:
            point = self.size - event.mouse.where
            working = True
            while working:
                event.mouse.where += point
                self.__moveGrow(self.origin, event.mouse.where, limits, minSize, maxSize, mode)
                working = self.mouseEvent(event, evMouseMove)
            # Grow to the mouse-up
            event.mouse.where += point
            self.__moveGrow(self.origin, event.mouse.where, limits, minSize, maxSize, mode)

    def __handleKeyDownDrag(self, event, mode, limits, minSize, maxSize):
        """
        Handle key down event
        """
        saveBounds = self.getBounds()
        done = False
        while not done:
            point = self.origin
            size = self.size
            self.keyEvent(event)
            kd = event.keyDown
            ckState = kd.controlKeyState
            kSwitch = kd.keyCode & 0xFF00

            if kSwitch in self.MOVE_COMMANDS:
                point, size = self.__change(mode, self.MOVE_COMMANDS[kSwitch], point, size, ckState)
            elif kSwitch == kbHome:
                point.x = limits.topLeft.x
            elif kSwitch == kbEnd:
                point.x = limits.bottomRight.x - size.x
            elif kSwitch == kbPgUp:
                point.y = limits.topLeft.y
            elif kSwitch == kbPgDn:
                point.y = limits.bottomRight.y - size.y

            self.__moveGrow(point, size, limits, minSize, maxSize, mode)
            done = event.keyDown.keyCode in {kbEsc, kbEnter}
        if event.keyDown.keyCode == kbEsc:
            self.locate(saveBounds)
