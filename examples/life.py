# -*- coding: utf-8 -*-
"""
 * Copyright (c) 1988-91 by Patrick J. Naughton.
 *
 * Permission to use, copy, modify, and distribute this software and its
 * documentation for any purpose and without fee is hereby granted,
 * provided that the above copyright notice appear in all copies and that
 * both that copyright notice and this permission notice appear in
 * supporting documentation.
 *
 * This file is provided AS IS with no warranties of any kind.	The author
 * shall have no liability with respect to the infringement of copyrights,
 * trade secrets or any patents by this file or any part thereof.  In no
 * event will the author be liable for any lost revenue or profits or
 * other special, indirect and consequential damages.
"""

import array
from enum import IntEnum, auto
import logging
import random
from typing import Tuple

from vindauga.constants.buttons import bfDefault
from vindauga.constants.command_codes import cmMenu, cmQuit, cmClose, hcNoContext, \
    cmNext, cmZoom, cmOK, cmTile, cmCascade, cmResize, cmPrev
from vindauga.constants.grow_flags import gfGrowHiX, gfGrowHiY
from vindauga.constants.event_codes import evMouseDown, evMouseMove, evKeyDown, evCommand, evBroadcast, mbLeftButton, \
    mbRightButton
from vindauga.constants.keys import kbF10, kbAltX, kbCtrlW, kbF6, kbF9, kbNoKey, kbCtrlF5, kbF5, kbShiftF6
from vindauga.constants.option_flags import ofSelectable, ofFirstClick, ofTileable, ofCentered
from vindauga.events.event import Event
from vindauga.menus.menu_bar import MenuBar
from vindauga.menus.menu_item import MenuItem
from vindauga.menus.sub_menu import SubMenu
from vindauga.misc.message import message
from vindauga.types.command_set import CommandSet
from vindauga.types.draw_buffer import DrawBuffer
from vindauga.types.point import Point
from vindauga.types.rect import Rect
from vindauga.types.status_def import StatusDef
from vindauga.types.status_item import StatusItem
from vindauga.types.view import View
from vindauga.widgets.application import Application
from vindauga.widgets.button import Button
from vindauga.widgets.dialog import Dialog
from vindauga.widgets.static_text import StaticText
from vindauga.widgets.status_line import StatusLine
from vindauga.widgets.window import Window

logger = logging.getLogger('vindauga.examples.life')


# noinspection PyArgumentList
class CommandCodes(IntEnum):
    cmAbout = 101  # about box
    cmCreate = auto()  # creates a new life window
    cmOneStep = auto()  # advance     one    step
    cmUpdate = auto()  # issued     when    idle
    cmStartStop = auto()  # starts or stops a life window
    cmClearBoard = auto()  # clears     the    life    board    
    cmRandom = auto()  # randomly     fills    the    life    board
    cmPat01 = auto()
    cmPat02 = auto()
    cmPat03 = auto()
    cmPat04 = auto()
    cmPat05 = auto()
    cmPat06 = auto()
    cmPat07 = auto()
    cmPat08 = auto()
    cmPat09 = auto()
    cmPat10 = auto()
    cmPat11 = auto()
    cmPat12 = auto()
    cmPat13 = auto()
    cmPat14 = auto()
    cmPat15 = auto()
    cmPat16 = auto()
    cmPat17 = auto()
    cmPat18 = auto()
    cmPat19 = auto()
    cmPat20 = auto()
    cmPat21 = auto()
    cmPat22 = auto()
    cmPat23 = auto()
    cmPat24 = auto()
    cmPat25 = auto()
    cmPat26 = auto()
    cmPat27 = auto()
    cmPat28 = auto()
    cmPat29 = auto()


patterns = (
    (  # GLIDER GUN */
        (6, -4),
        (5, -3), (6, -3),
        (- 6, -2), (- 5, -2), (8, -2), (9, -2), (16, -2),
        (- 7, -1), (8, -1), (9, -1), (10, -1), (16, -1), (17, -1),
        (-18, 0), (-17, 0), (-8, 0), (8, 0), (9, 1),
        (-17, 1), (- 8, 1), (5, 1), (6, 1),
        (- 8, 2), (6, 2),
        (- 7, 3),
        (- 6, 4), (-5, 4),
    ),
    (  # /* FIGURE EIGHT */
        (-3, -3), (-2, -3), (-1, -3),
        (-3, -2), (-2, -2), (-1, -2),
        (-3, -1), (-2, -1), (-1, -1),
        (0, 0), (1, 0), (2, 0),
        (0, 1), (1, 1), (2, 1),
        (0, 2), (1, 2), (2, 2),
    ),
    (  # /* PULSAR */
        (-2, -1), (-1, -1), (0, -1), (1, -1), (2, -1),
        (-2, 0), (2, 0),
    ),
    (  # /* BARBER POLE P2 */
        (-6, -6), (-5, -6),
        (-6, -5), (-4, -5),
        (-4, -3), (-2, -3),
        (-2, -1), (0, -1),
        (0, 1), (2, 1),
        (2, 3), (4, 3),
        (5, 4),
        (4, 5), (5, 5),
    ),
    (  # /* ACHIM P5 */
        (-6, -6), (-5, -6),
        (-6, -5),
        (-4, -4),
        (-4, -3), (-2, -3),
        (-2, -1), (0, -1),
        (0, 1), (2, 1),
        (2, 3), (3, 3),
        (5, 4),
        (4, 5), (5, 5),
    ),
    (  # /* HERTZ P4 */
        (-2, -5), (-1, -5),
        (-2, -4), (-1, -4),
        (-7, -2), (-6, -2), (-2, -2), (-1, -2), (0, -2), (1, -2), (5, -2), (6, -2),
        (-7, -1), (-5, -1), (-3, -1), (2, -1), (4, -1), (6, -1),
        (-5, 0), (-3, 0), (-2, 0), (2, 0), (4, 0),
        (-7, 1), (-5, 1), (-3, 1), (2, 1), (4, 1), (6, 1),
        (-7, 2), (-6, 2), (-2, 2), (-1, 2), (0, 2), (1, 2), (5, 2), (6, 2),
        (-2, 4), (-1, 4),
        (-2, 5), (-1, 5),
    ),
    (  # /* TUMBLER */
        (-2, -3), (-1, -3), (1, -3), (2, -3),
        (-2, -2), (-1, -2), (1, -2), (2, -2),
        (-1, -1), (1, -1),
        (-3, 0), (-1, 0), (1, 0), (3, 0),
        (-3, 1), (-1, 1), (1, 1), (3, 1),
        (-3, 2), (-2, 2), (2, 2), (3, 2),
    ),
    (  # /* PULSE1 P4 */
        (0, -3), (1, -3),
        (-2, -2), (0, -2),
        (-3, -1), (3, -1),
        (-2, 0), (2, 0), (3, 0),
        (0, 2), (2, 2),
        (1, 3),
    ),
    (  # /* SHINING FLOWER P5 */
        (-1, -4), (0, -4),
        (-2, -3), (1, -3),
        (-3, -2), (2, -2),
        (-4, -1), (3, -1),
        (-4, 0), (3, 0),
        (-3, 1), (2, 1),
        (-2, 2), (1, 2),
        (-1, 3), (0, 3),
    ),
    (  # /* PULSE2 P6 */
        (0, -4), (1, -4),
        (-4, -3), (-3, -3), (-1, -3),
        (-4, -2), (-3, -2), (0, -2), (3, -2),
        (1, -1), (3, -1),
        (2, 0),
        (1, 2), (2, 2),
        (1, 3), (2, 3),
    ),
    (  # /* PINWHEEL, CLOCK P4 */
        (-2, -6), (-1, -6),
        (-2, -5), (-1, -5),
        (-2, -3), (-1, -3), (0, -3), (1, -3),
        (-3, -2), (-1, -2), (2, -2), (4, -2), (5, -2),
        (-3, -1), (1, -1), (2, -1), (4, -1), (5, -1),
        (-6, 0), (-5, 0), (-3, 0), (0, 0), (2, 0),
        (-6, 1), (-5, 1), (-3, 1), (2, 1),
        (-2, 2), (-1, 2), (0, 2), (1, 2),
        (0, 4), (1, 4),
        (0, 5), (1, 5),
    ),
    (  # /* PENTADECATHOLON */
        (-5, 0), (-4, 0), (-3, 0), (-2, 0), (-1, 0), (0, 0), (1, 0), (2, 0), (3, 0), (4, 0),
    ),
    (  # /* PISTON */
        (1, -3), (2, -3),
        (0, -2),
        (-10, -1), (-1, -1),
        (-11, 0), (-10, 0), (-1, 0), (9, 0), (10, 0),
        (-1, 1), (9, 1),
        (0, 2),
        (1, 3), (2, 3),
    ),
    (  # /* PISTON2 */
        (-3, -5),
        (-14, -4), (-13, -4), (-4, -4), (-3, -4), (13, -4), (14, -4),
        (-14, -3), (-13, -3), (-5, -3), (-4, -3), (13, -3), (14, -3),
        (-4, -2), (-3, -2), (0, -2), (1, -2),
        (-4, 2), (-3, 2), (0, 2), (1, 2),
        (-14, 3), (-13, 3), (-5, 3), (-4, 3), (13, 3), (14, 3),
        (-14, 4), (-13, 4), (-4, 4), (-3, 4), (13, 4), (14, 4),
        (-3, 5),
    ),
    (  # /* SWITCH ENGINE */
        (-12, -3), (-10, -3),
        (-13, -2),
        (-12, -1), (-9, -1),
        (-10, 0), (-9, 0), (-8, 0),
        (13, 2), (14, 2),
        (13, 3),
    ),
    (  # /* GEARS (gear, flywheel, blinker) */
        (-1, -4),
        (-1, -3), (1, -3),
        (-3, -2),
        (2, -1), (3, -1),
        (-4, 0), (-3, 0),
        (2, 1),
        (-2, 2), (0, 2),
        (0, 3),

        (5, 3),
        (3, 4), (4, 4),
        (5, 5), (6, 5),
        (4, 6),

        (8, 0),
        (8, 1),
        (8, 2),
    ),
    (  # /* TURBINE8 */
        (-4, -4), (-3, -4), (-2, -4), (-1, -4), (0, -4), (1, -4), (3, -4), (4, -4),
        (-4, -3), (-3, -3), (-2, -3), (-1, -3), (0, -3), (1, -3), (3, -3), (4, -3),
        (3, -2), (4, -2),
        (-4, -1), (-3, -1), (3, -1), (4, -1),
        (-4, 0), (-3, 0), (3, 0), (4, 0),
        (-4, 1), (-3, 1), (3, 1), (4, 1),
        (-4, 2), (-3, 2),
        (-4, 3), (-3, 3), (-1, 3), (0, 3), (1, 3), (2, 3), (3, 3), (4, 3),
        (-4, 4), (-3, 4), (-1, 4), (0, 4), (1, 4), (2, 4), (3, 4), (4, 4),
    ),
    (  # /* P16 */
        (-3, -6), (1, -6), (2, -6),
        (-3, -5), (0, -5), (3, -5),
        (3, -4),
        (-5, -3), (-4, -3), (1, -3), (2, -3), (5, -3), (6, -3),
        (-6, -2), (-3, -2),
        (-6, -1), (-3, -1),
        (-5, 0), (5, 0),
        (3, 1), (6, 1),
        (3, 2), (6, 2),
        (-6, 3), (-5, 3), (-2, 3), (-1, 3), (4, 3), (5, 3),
        (-3, 4),
        (-3, 5), (0, 5), (3, 5),
        (-2, 6), (-1, 6), (3, 6),
    ),
    (  # /* PUFFER */
        (1, -9),
        (2, -8),
        (-2, -7), (2, -7),
        (-1, -6), (0, -6), (1, -6), (2, -6),
        (-2, -2),
        (-1, -1), (0, -1),
        (0, 0),
        (0, 1),
        (-1, 2),
        (1, 5),
        (2, 6),
        (-2, 7), (2, 7),
        (-1, 8), (0, 8), (1, 8), (2, 8),
    ),
    (  # /* ESCORT */
        (3, -8),
        (4, -7),
        (-2, -6), (4, -6),
        (-1, -5), (0, -5), (1, -5), (2, -5), (3, -5), (4, -5),
        (-5, -1), (-4, -1), (-3, -1), (-2, -1), (-1, -1), (0, -1),
        (1, -1), (2, -1), (3, -1), (4, -1), (5, -1), (6, -1),
        (-6, 0), (6, 0),
        (6, 1),
        (5, 2),
        (3, 4),
        (4, 5),
        (-2, 6), (4, 6),
        (-1, 7), (0, 7), (1, 7), (2, 7), (3, 7), (4, 7),
    ),
    (  # /* DART SPEED 1/3 */
        (3, -7),
        (2, -6), (4, -6),
        (1, -5), (2, -5),
        (4, -4),
        (0, -3), (4, -3),
        (-3, -2), (0, -2),
        (-4, -1), (-2, -1), (1, -1), (2, -1), (3, -1), (4, -1),
        (-5, 0), (-2, 0),
        (-4, 1), (-2, 1), (1, 1), (2, 1), (3, 1), (4, 1),
        (-3, 2), (0, 2),
        (0, 3), (4, 3),
        (4, 4),
        (1, 5), (2, 5),
        (2, 6), (4, 6),
        (3, 7),
    ),
    (  # /* PERIOD 4 SPEED 1/2 */
        (-3, -5),
        (-4, -4), (-3, -4), (-2, -4), (-1, -4), (0, -4),
        (-5, -3), (-4, -3), (0, -3), (1, -3), (3, -3),
        (-4, -2), (4, -2),
        (-3, -1), (-2, -1), (1, -1), (3, -1),
        (-3, 1), (-2, 1), (1, 1), (3, 1),
        (-4, 2), (4, 2),
        (-5, 3), (-4, 3), (0, 3), (1, 3), (3, 3),
        (-4, 4), (-3, 4), (-2, 4), (-1, 4), (0, 4),
        (-3, 5),
    ),
    (  # /* ANOTHER PERIOD 4 SPEED 1/2 */
        (-4, -7), (-3, -7), (-1, -7), (0, -7), (1, -7), (2, -7), (3, -7), (4, -7),
        (-5, -6), (-4, -6), (-3, -6), (-2, -6), (5, -6),
        (-6, -5), (-5, -5),
        (-5, -4), (5, -4),
        (-4, -3), (-3, -3), (-2, -3), (0, -3),
        (-2, -2),
        (-2, -1),
        (-1, 0),
        (-2, 1),
        (-2, 2),
        (-4, 3), (-3, 3), (-2, 3), (0, 3),
        (-5, 4), (5, 4),
        (-6, 5), (-5, 5),
        (-5, 6), (-4, 6), (-3, 6), (-2, 6), (5, 6),
        (-4, 7), (-3, 7), (-1, 7), (0, 7), (1, 7), (2, 7), (3, 7), (4, 7),
    ),
    (  # /* SMALLEST KNOWN PERIOD 3 SPACESHIP SPEED 1/3 */
        (0, -8),
        (-1, -7), (1, -7),
        (-1, -6), (1, -6),
        (-1, -5),
        (-2, -3), (-1, -3),
        (-1, -2), (1, -2),
        (-2, -1), (0, -1),
        (-2, 0), (-1, 0), (0, 0),
        (-1, 2), (1, 2),
        (-1, 3), (0, 3),
        (0, 4),
        (0, 5), (2, 5),
        (0, 6), (2, 6),
        (1, 7),
    ),
    (  # /* TURTLE SPEED 1/3 */
        (-4, -5), (-3, -5), (-2, -5), (6, -5),
        (-4, -4), (-3, -4), (0, -4), (2, -4), (3, -4), (5, -4), (6, -4),
        (-2, -3), (-1, -3), (0, -3), (5, -3),
        (-4, -2), (-1, -2), (1, -2), (5, -2),
        (-5, -1), (0, -1), (5, -1),
        (-5, 0), (0, 0), (5, 0),
        (-4, 1), (-1, 1), (1, 1), (5, 1),
        (-2, 2), (-1, 2), (0, 2), (5, 2),
        (-4, 3), (-3, 3), (0, 3), (2, 3), (3, 3), (5, 3), (6, 3),
        (-4, 4), (-3, 4), (-2, 4), (6, 4),
    ),
    (  # /* SMALLEST KNOWN PERIOD 5 SPEED 2/5 */
        (1, -7), (3, -7),
        (-2, -6), (3, -6),
        (-3, -5), (-2, -5), (-1, -5), (4, -5),
        (-4, -4), (-2, -4),
        (-5, -3), (-4, -3), (-1, -3), (0, -3), (5, -3),
        (-4, -2), (-3, -2), (0, -2), (1, -2), (2, -2), (3, -2), (4, -2),
        (-4, 2), (-3, 2), (0, 2), (1, 2), (2, 2), (3, 2), (4, 2),
        (-5, 3), (-4, 3), (-1, 3), (0, 3), (5, 3),
        (-4, 4), (-2, 4),
        (-3, 5), (-2, 5), (-1, 5), (4, 5),
        (-2, 6), (3, 6),
        (1, 7), (3, 7),
    ),
    (  # /* SYM PUFFER */
        (1, -4), (2, -4), (3, -4), (4, -4),
        (0, -3), (4, -3),
        (4, -2),
        (-4, -1), (-3, -1), (0, -1), (3, -1),
        (-4, 0), (-3, 0), (-2, 0),
        (-4, 1), (-3, 1), (0, 1), (3, 1),
        (4, 2),
        (0, 3), (4, 3),
        (1, 4), (2, 4), (3, 4), (4, 4),
    ),
    (  # /* ], NEAR SHIP, PI HEPTOMINO */
        (-2, -1), (-1, -1), (0, -1),
        (1, 0),
        (-2, 1), (-1, 1), (0, 1),
    ),
    (  # /* R PENTOMINO */
        (0, -1), (1, -1),
        (-1, 0), (0, 0),
        (0, 1),
    )
)


class Board:
    def __init__(self, width: int, height: int):
        self.__width = width
        self.__height = height
        self.__board = array.array('B', [0, ] * (width * height))

    def __getitem__(self, loc: Tuple[int, int]):
        x, y = loc
        return self.__board[y * self.__width + x]

    def __setitem__(self, loc: Tuple[int, int], val: int):
        x, y = loc
        self.__board[y * self.__width + x] = val

    @property
    def board(self) -> array.array:
        return self.__board


class LifeInterior(View):
    def __init__(self, bounds: Rect):
        super().__init__(bounds)
        self.__running = False
        self.__board = Board(self.size.x, self.size.y)
        self.eventMask = evMouseDown | evKeyDown | evCommand | evBroadcast
        self.growMode = gfGrowHiX | gfGrowHiY
        self.options |= ofSelectable
        self.getPattern(0)

    def changeBounds(self, bounds: Rect):
        if not self.__board:
            return
        oldSize = self.size
        newSize = bounds.bottomRight
        work = Board(newSize.x, newSize.y)
        for y in range(oldSize.y):
            h = y * oldSize.y
            work.board[h:h + oldSize.x] = self.__board.board[h:h + oldSize.x]
        self.__board = work

        super().changeBounds(bounds)

    def clearBoard(self):
        if not self.__board:
            return
        self.__board = Board(self.size.x, self.size.y)

    def draw(self):
        color = 0x4F if self.__running else 0x1F
        i = self.size.x * self.size.y
        buf = array.array('L', [0x20, ] * (self.size.x * self.size.y))
        for x in range(i):
            if self.__board.board[x]:
                buf[x] = color << DrawBuffer.CHAR_WIDTH | 0x00D6
        self.writeBuf(0, 0, self.size.x, self.size.y, buf)

    def getPattern(self, pat: int):
        if not self.__board:
            return
        self.clearBoard()

        i = pat % len(patterns)
        for col, row in patterns[i]:
            col += self.size.x // 2
            row += self.size.y // 2
            self.__board[col, row] = 1

    def handleEvent(self, event: Event):
        super().handleEvent(event)

        if event.what == evBroadcast:
            if event.message.command == CommandCodes.cmUpdate and self.__running:
                self.iterateBoard()
                self.drawView()
        elif event.what == evCommand:
            if CommandCodes.cmPat01 <= event.message.command < CommandCodes.cmPat01 + len(patterns):
                self.getPattern(event.message.command - CommandCodes.cmPat01)
                self.drawView()
            else:
                if event.message.command == CommandCodes.cmOneStep:
                    self.iterateBoard()
                    self.drawView()
                elif event.message.command == CommandCodes.cmClearBoard:
                    self.clearBoard()
                    self.drawView()
                elif event.message.command == CommandCodes.cmRandom:
                    self.randomizeBoard()
                    self.drawView()
                elif event.message.command == CommandCodes.cmStartStop:
                    self.__running = not self.__running
                    self.drawView()
                else:
                    return
            self.clearEvent(event)
        elif event.what == evMouseDown:
            self.handleMouse(event)

    def handleMouse(self, event: Event):
        clickRect = self.getExtent()

        processing = True
        while processing:
            mouse = self.makeLocal(event.mouse.where)
            if clickRect.contains(mouse):
                if event.mouse.buttons & mbLeftButton:
                    self.__board[mouse.x, mouse.y] = 1
                if event.mouse.buttons & mbRightButton:
                    self.__board[mouse.x, mouse.y] = 0
                self.drawView()
            processing = self.mouseEvent(event, evMouseMove)

    def iterateBoard(self):
        if not self.__board:
            return
        work = Board(self.size.x, self.size.y)

        differences = 0
        for y in range(self.size.y):
            for x in range(self.size.x):
                n = (self.present(x - 1, y - 1) + self.present(x, y - 1) +
                     self.present(x + 1, y - 1) + self.present(x - 1, y) +
                     self.present(x + 1, y) + self.present(x - 1, y + 1) +
                     self.present(x, y + 1) + self.present(x + 1, y + 1))

                if self.__board[x, y] == 1:
                    if n in {2, 3}:
                        work[x, y] = 1
                if self.__board[x, y] == 0:
                    if n == 3:
                        work[x, y] = 1
                if self.__board[x, y] != work[x, y]:
                    differences += 1

        self.__board = work
        if not differences:
            self.__running = False

    def present(self, x: int, y: int):
        if not (0 < x < self.size.x and 0 < y < self.size.y):
            return 0
        if self.__board[x, y] == 0:
            return 0
        return 1

    def randomizeBoard(self):
        if not self.__board:
            return
        self.clearBoard()

        howMany = self.size.x * self.size.y // 5
        for i in range(howMany):
            processing = True
            x = y = 0
            while processing:
                x = random.randint(0, self.size.x - 1)
                y = random.randint(0, self.size.y - 1)
                processing = self.__board[x, y] != 0
            self.__board[x, y] = 1


class LifeWindow(Window):
    minW = 28
    minH = 11

    def __init__(self, bounds: Rect, title: str, windowNumber: int):
        super().__init__(bounds, title, windowNumber)
        self.options |= ofFirstClick | ofTileable

        r = self.getClipRect()
        r.grow(-1, -1)
        self.life = LifeInterior(r)
        self.insert(self.life)

    def sizeLimits(self, minLimit: Point, maxLimit: Point):
        super().sizeLimits(minLimit, maxLimit)
        minLimit.x = self.minW
        minLimit.y = self.minH


class LifeApp(Application):
    def __init__(self):
        super().__init__()
        self.windowCommands = self.__getCommands()

    def aboutBox(self):
        box = Dialog(Rect(0, 0, 32, 10), 'About')
        box.insert(StaticText(Rect(1, 2, 31, 7),
                              """\x03Conway's Game of Life\n\x03The classic life example"""))
        box.insert(Button(Rect(11, 7, 21, 9), 'O~K~', cmOK, bfDefault))
        box.options |= ofCentered
        self.executeDialog(box, None)

    def createLifeWindow(self):
        r = self.desktop.getExtent()
        r.grow(-1, -1)
        w = self.validView(LifeWindow(r, 'Life', 0))
        if w:
            self.desktop.insert(w)

    def handleEvent(self, event: Event):
        super().handleEvent(event)

        if event.what == evCommand:
            emc = event.message.command
            if emc == CommandCodes.cmAbout:
                self.aboutBox()
            elif emc == cmCascade:
                self.desktop.cascade(self.desktop.getExtent())
            elif emc == CommandCodes.cmCreate:
                self.createLifeWindow()
            elif emc == cmTile:
                self.desktop.tile(self.desktop.getExtent())
            else:
                return
            self.clearEvent(event)

    @staticmethod
    def isTileable(view: View, *_args) -> bool:
        return bool(view.options & ofTileable)

    def idle(self):
        super().idle()
        if self.desktop.firstThat(self.isTileable):
            View.enableCommands(self.windowCommands)
        else:
            View.disableCommands(self.windowCommands)
        message(self.desktop, evBroadcast, CommandCodes.cmUpdate, 0)

    def initMenuBar(self, bounds: Rect) -> MenuBar:
        sub1 = (SubMenu('~≡~', 0, hcNoContext) +
                MenuItem('~A~bout...', CommandCodes.cmAbout, kbNoKey, hcNoContext))
        sub2 = (SubMenu('~F~ile', 0) +
                MenuItem('~L~ife Window', CommandCodes.cmCreate, kbF9, hcNoContext, 'F9') +
                MenuItem.newLine() +
                MenuItem('E~x~it', cmQuit, kbAltX, hcNoContext, 'Alt+X'))
        sub3 = (SubMenu('~A~ction', 0) +
                MenuItem('~C~lear', CommandCodes.cmClearBoard, kbNoKey, hcNoContext) +
                MenuItem('~O~ne Step', CommandCodes.cmOneStep, kbNoKey, hcNoContext) +
                MenuItem('~R~andomize', CommandCodes.cmRandom, kbNoKey, hcNoContext) +
                MenuItem('~S~tart/Stop', CommandCodes.cmStartStop, kbNoKey, hcNoContext))
        sub4 = (SubMenu('~W~indow', 0) +
                MenuItem('~S~ize/Move', cmResize, kbCtrlF5, hcNoContext, 'Ctrl+F5') +
                MenuItem('~Z~oom', cmZoom, kbF5, hcNoContext, 'F5') +
                MenuItem('~N~ext', cmNext, kbF6, hcNoContext, 'F6') +
                MenuItem('~P~revious', cmPrev, kbShiftF6, hcNoContext, 'Shift+F6') +
                MenuItem('~C~lose', cmClose, kbCtrlW, hcNoContext, 'Ctrl+W') +
                MenuItem.newLine() +
                MenuItem('~T~ile', cmTile, kbNoKey, hcNoContext) +
                MenuItem('C~a~scade', cmCascade, kbNoKey, hcNoContext)
                )

        _ = lambda name, comm: MenuItem(name, comm, kbNoKey, hcNoContext)

        sub5 = (SubMenu('Patterns ~1~', 0) +
                _("Glider Gun", CommandCodes.cmPat01) +
                _("Figure Eight", CommandCodes.cmPat02) +
                _("Pulsar", CommandCodes.cmPat03) +
                _("Barber Pole P2", CommandCodes.cmPat04) +
                _("Achim P5", CommandCodes.cmPat05) +
                _("Hertz P4", CommandCodes.cmPat06) +
                _("Tumbler", CommandCodes.cmPat07) +
                _("Pulse1 P4", CommandCodes.cmPat08) +
                _("Shining Flower P5", CommandCodes.cmPat09) +
                _("Pulse2 P6", CommandCodes.cmPat10) +
                _("Pinwheel, Clock P4", CommandCodes.cmPat11) +
                _("Pentadecatholon", CommandCodes.cmPat12) +
                _("Piston", CommandCodes.cmPat13) +
                _("Piston2", CommandCodes.cmPat14) +
                _("Switch Engine", CommandCodes.cmPat15)
                )
        sub6 = (SubMenu('Patterns ~2~', 0) +
                _("Gears (Gear, Flywheel, Blinker)", CommandCodes.cmPat16) +
                _("Turbine8", CommandCodes.cmPat17) +
                _("P16", CommandCodes.cmPat18) +
                _("Puffer", CommandCodes.cmPat19) +
                _("Escort", CommandCodes.cmPat20) +
                _("Dart Speed 1/3", CommandCodes.cmPat21) +
                _("Period 4 Speed 1/2", CommandCodes.cmPat22) +
                _("Another Period 4 Speed 1/2", CommandCodes.cmPat23) +
                _("Smallest Known Period 3 Spaceship Speed 1/3", CommandCodes.cmPat24) +
                _("Turtle Speed 1/3", CommandCodes.cmPat25) +
                _("Smallest Known Period 5 Speed 2/5", CommandCodes.cmPat26) +
                _("Sym Puffer", CommandCodes.cmPat27) +
                _("], Near Ship, Pi Heptomino", CommandCodes.cmPat28) +
                _("R Pentomino", CommandCodes.cmPat29)
                )
        bounds.bottomRight.y = bounds.topLeft.y + 1
        return MenuBar(bounds, sub1 + sub2 + sub3 + sub4 + sub5 + sub6)

    def initStatusLine(self, bounds: Rect) -> StatusLine:
        bounds.topLeft.y = bounds.bottomRight.y - 1
        return StatusLine(bounds,
                          StatusDef(0, 50) +
                          StatusItem('~Alt+X~ Exit', kbAltX, cmQuit) +
                          StatusItem('~F9~ Life Window', kbF9, CommandCodes.cmCreate) +
                          StatusItem('~Ctrl+W~ Close', kbCtrlW, cmClose) +
                          StatusItem('One Step', kbNoKey, CommandCodes.cmOneStep) +
                          StatusItem('Randomize', kbNoKey, CommandCodes.cmRandom) +
                          StatusItem('Start/Stop', kbNoKey, CommandCodes.cmStartStop) +
                          StatusItem('', kbF10, cmMenu) +
                          StatusItem('', kbF5, cmZoom) +
                          StatusItem('', kbCtrlF5, cmResize)
                          )

    @staticmethod
    def __getCommands() -> CommandSet:
        wc = CommandSet()
        wc += cmCascade

        for c in CommandCodes:
            wc += c.value

        wc -= CommandCodes.cmAbout
        wc -= CommandCodes.cmCreate
        wc -= CommandCodes.cmUpdate
        return wc


def setupLogging():
    vin_logger = logging.getLogger('vindauga')
    vin_logger.propagate = False
    log_format = '%(name)s\t %(message)s'
    vin_logger.setLevel(logging.DEBUG)
    handler = logging.StreamHandler(open('vindauga.log', 'wt'))
    handler.setFormatter(logging.Formatter(log_format))
    vin_logger.addHandler(handler)


if __name__ == '__main__':
    setupLogging()
    app = LifeApp()
    app.run()
