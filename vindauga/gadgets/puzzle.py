# -*- coding: utf-8 -*-
import random

from vindauga.constants.command_codes import wnNoNumber
from vindauga.constants.window_flags import wfGrow, wfZoom
from vindauga.constants.event_codes import evKeyboard, evMouse, evMouseDown, evKeyDown
from vindauga.constants.keys import kbDown, kbUp, kbRight, kbLeft
from vindauga.constants.option_flags import ofSelectable
from vindauga.events.event import Event
from vindauga.types.draw_buffer import DrawBuffer
from vindauga.types.palette import Palette
from vindauga.types.point import Point
from vindauga.types.rect import Rect
from vindauga.types.view import View
from vindauga.widgets.window import Window


class PuzzleView(View):
    name = 'PuzzleView'

    cpPuzzlePalette = '\x06\x07'

    boardStart = 'A', 'B', 'C', 'D', 'E', 'F', 'G', 'H', 'I', 'J', 'K', 'L', 'M', 'N', 'O', ' '
    boardMap = 0, 1, 0, 1, 1, 0, 1, 0, 0, 1, 0, 1, 1, 0, 1
    solution = ''.join(boardStart)

    def __init__(self, bounds):
        super().__init__(bounds)
        random.seed()
        self.options |= ofSelectable
        self.board = [list(self.boardStart[i:i + 4]) for i in range(0, 16, 4)]
        self.solved = False
        self.moves = 0
        self.scramble()

    def draw(self):
        buf = DrawBuffer()

        colorBack = self.getColor(1)
        color = [colorBack, colorBack]
        if not self.solved:
            color[1] = self.getColor(2)

        for i in range(4):
            buf.moveChar(0, ' ', colorBack, 18)
            if i == 1:
                buf.moveStr(13, _('Move'), colorBack)
            if i == 2:
                tmp = f'{self.moves}'
                buf.moveStr(14, tmp, colorBack)

            for j in range(4):
                tmp = f' {self.board[i][j]} '
                if self.board[i][j] == ' ':
                    buf.moveStr(j * 3, tmp, color[0])
                else:
                    buf.moveStr(j * 3, tmp, color[self.boardMap[ord(self.board[i][j]) - ord('A')]])

            self.writeLine(0, i, 18, 1, buf)

    def getPalette(self) -> Palette:
        return Palette(self.cpPuzzlePalette)

    def handleEvent(self, event: Event):
        super().handleEvent(event)
        if self.solved and event.what & (evKeyboard | evMouse):
            self.scramble()
            self.clearEvent(event)

        if event.what == evMouseDown:
            self.moveTile(event.mouse.where)
            self.clearEvent(event)
            self.winCheck()
        elif event.what == evKeyDown:
            self.moveKey(event.keyDown.keyCode)
            self.clearEvent(event)
            self.winCheck()

    def moveKey(self, key: int):
        for i in range(16):
            if self.board[i // 4][i % 4] == ' ':
                break

        y, x = divmod(i, 4)

        if key == kbDown:
            if y > 0:
                self.board[y][x] = self.board[y - 1][x]
                self.board[y - 1][x] = ' '
                self.moves += 1
        elif key == kbUp:
            if y < 3:
                self.board[y][x] = self.board[y + 1][x]
                self.board[y + 1][x] = ' '
                self.moves += 1
        elif key == kbRight:
            if x > 0:
                self.board[y][x] = self.board[y][x - 1]
                self.board[y][x - 1] = ' '
                self.moves += 1
        elif key == kbLeft:
            if x < 3:
                self.board[y][x] = self.board[y][x + 1]
                self.board[y][x + 1] = ' '
                self.moves += 1

        self.drawView()

    def moveTile(self, point: Point):
        point = self.makeLocal(point)
        i = 0
        for i in range(16):
            if self.board[i // 4][i % 4] == ' ':
                break

        x = point.x // 3
        y = point.y

        p = y * 4 + x - i
        if p == -4:
            self.moveKey(kbDown)
        elif p == -1:
            self.moveKey(kbRight)
        elif p == 1:
            self.moveKey(kbLeft)
        elif p == 4:
            self.moveKey(kbUp)

        self.drawView()

    def scramble(self):
        keys = [kbUp, kbDown, kbRight, kbLeft]
        for i in range(500):
            self.moveKey(keys[random.randint(0, 64738) % 4])
        self.moves = 0
        self.solved = False
        self.drawView()

    def winCheck(self):
        for i in range(16):
            if self.board[i // 4][i % 4] != self.solution[i]:
                break
        if i == 15:
            self.solved = True
        self.drawView()


class PuzzleWindow(Window):
    def __init__(self):
        super().__init__(Rect(1, 1, 21, 7), _('Puzzle'), wnNoNumber)
        self.flags &= ~(wfZoom | wfGrow)
        self.growMode = 0
        r = self.getExtent()
        r.grow(-1, -1)
        self.insert(PuzzleView(r))
