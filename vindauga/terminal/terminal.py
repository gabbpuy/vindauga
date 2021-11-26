# -*- coding: utf-8 -*-
import copy
import curses
from dataclasses import dataclass
import logging
import os
from os import kill, execvpe, waitpid
import platform
import select
import struct
import signal

PLATFORM_WINDOWS = platform.platform().lower().startswith('windows')
if not PLATFORM_WINDOWS:
    import fcntl
    import pwd
    import termios
    import pty
else:
    from .windows_shell import WindowsShell

logger = logging.getLogger(__name__)


@dataclass
class Texel:
    char: str = ''
    attr: int = 0
    color: int = 0


@dataclass
class Color:
    fg: int
    bg: int


defaultFg = 7
defaultBg = 0

MAX_CSI_ESC_PARAMS = 32
ESC_SEQ_BUF_SIZE = 128

STATE_ALT_CHARSET = (1 << 1)
STATE_ESCAPE_MODE = (1 << 2)
STATE_PIPE_ERR = (1 << 3)
STATE_CHILD_EXITED = (1 << 4)
STATE_CURSOR_INVIS = (1 << 5)
# scrolling region is not full height
STATE_SCROLL_SHORT = (1 << 6)
STATE_MOUSE = (1 << 7)
STATE_TITLE_CHANGED = (1 << 8)


class Terminal:

    def __init__(self, width, height, flags, command=None, *commandArgs):
        self.rows = height
        self.cols = width
        self.col = []
        self.currRow = 0
        self.currCol = 0
        self.currAttr = curses.A_NORMAL
        self.savedX = 0
        self.savedY = 0
        self.scrollMin = 0
        self.scrollMax = height - 1
        self.flags = flags
        self.state = 0
        self.fg = defaultFg
        self.bg = defaultBg
        self.__childPid = -1
        self.__ptyFd = None
        self.colors = defaultFg | defaultBg
        if command:
            self.command = command
            self.commandArgs = [os.path.basename(command)]
            self.commandArgs.extend(commandArgs)
        else:
            self.command, self.commandArgs = self.getShell()
        logger.info('Command is %s, %s', self.command, self.commandArgs)
        self.csiParam = []
        self.escBuf = ''
        self.colorValues = [
            0, 4, 2, 6, 1, 5, 3, 7
            ]
        self.initColors()
        self.title = ''
        self.cells = [[Texel() for _x in range(width)] for _y in range(height)]
        self.erase()
        self.executeCommand()

    @staticmethod
    def getShell():
        if not PLATFORM_WINDOWS:
            profile = pwd.getpwuid(os.getuid())
            if not profile:
                shell = '/bin/sh'
            elif not profile.pw_shell:
                shell = '/bin/sh'
            else:
                shell = profile.pw_shell
            return shell, [os.path.basename(shell), '-l']
        return 'cmd.exe', []

    if not PLATFORM_WINDOWS:
        def executeCommand(self):
            try:
                self.__childPid, self.__ptyFd = pty.fork()
                logger.info('pid: %s, fd: %s', self.__childPid, self.__ptyFd)
            except:
                raise

            if not self.__childPid:
                # Child
                env = os.environ.copy()
                signal.signal(signal.SIGINT, signal.SIG_DFL)
                env['TERM'] = 'rxvt'
                logger.info('Executing %s, %s', self.command, self.commandArgs)
                execvpe(self.command, self.commandArgs, env=env)

            if self.__childPid == -1:
                raise RuntimeError
    else:
        def executeCommand(self):
            command = [self.command] + self.commandArgs[1:]
            self.__childPid = WindowsShell(command)
            self.__ptyFd = self.__childPid()
            logger.info('handles: %s', self.__ptyFd)
            if self.__ptyFd is None:
                raise RuntimeError

    def destroy(self):
        try:
            kill(self.__childPid, signal.SIGKILL)
        except:
            pass

    def initColors(self):
        self.col.append(Color(0, 0))
        for i in range(8):
            for j in range(8):
                if i != 7 or j != 0:
                    self.col.append(Color(fg=i, bg=j))

    @property
    def pid(self):
        return self.__childPid

    @property
    def ptyFd(self):
        return self.__ptyFd

    def setColors(self, _fg, _bg):
        self.colors = defaultFg | (defaultBg << 4)
        return 0

    def getColors(self):
        return self.colors

    def pairContentVision(self, c):
        return self.col[c].fg, self.col[c].bg

    def findColorPair(self, fg, bg):
        for i in range(64):
            if self.col[i].fg == fg and self.col[i].bg == bg:
                return i
        return 0

    def startCSI(self):
        logger.info('startCSI() -> %s', self.escBuf)
        verb = self.escBuf[-1]
        self.csiParam = []

        for p in self.escBuf[1:-1]:
            if not ('0' <= p <= '9' or p in {';', '?'}):
                break
            if p == '?':
                continue

            if p == ';':
                if len(self.csiParam) > MAX_CSI_ESC_PARAMS:
                    return
                self.csiParam.append(0)
            else:
                if not self.csiParam:
                    self.csiParam.append(0)

                self.csiParam[-1] *= 10
                self.csiParam[-1] += (ord(p) - ord('0'))

        if verb == 'm':
            # Set Graphics
            self.do_SGR()
        elif verb == 'l':
            # Reset Mode
            self.do_DEC_RM()
        elif verb == 'h':
            # Set Mode
            self.do_DEC_SM()
        elif verb == 'J':
            # Erase Display
            self.do_ED()
        elif verb in {'H', 'f'}:
            # Cursor Up
            self.do_CUP()
        elif verb in 'ABCDEFGead`':
            # Relative Cursor Movement
            self.do_CUx(verb)
        elif verb == 'K':
            # Erase Line
            self.do_EL()
        elif verb == '@':
            # Insert Chars
            self.do_ICH()
        elif verb == 'P':
            # Delete Char
            self.do_DCH()
        elif verb == 'L':
            # Insert Line
            self.do_IL()
        elif verb == 'M':
            # Delete Line
            self.do_DL()
        elif verb == 'X':
            # Erase Chars
            self.do_ECH()
        elif verb == 'r':
            # Start Scrolling Region
            self.do_DECSTBM()
        elif verb == 's':
            # Save Cursor
            self.do_SAVECUR()
        elif verb == 'u':
            # Restore Cursor
            self.do_RESTORECUR()
        else:
            # NFI
            pass

    def do_CUP(self):
        """
        Cursor Up
        """
        if not self.csiParam:
            self.currRow = 0
            self.currCol = 0
            return
        if len(self.csiParam) < 2:
            return
        self.currRow = self.csiParam[0] - 1
        self.currCol = self.csiParam[1] - 1
        self.clampCursorToBounds()

    def do_CUx(self, verb):
        """
        Relative Cursor
        :param verb: Cursor command
        """
        n = self.getNumber()
        if verb == 'A':
            # Up
            self.currRow -= n
        elif verb in 'Be':
            # Down
            self.currRow += n
        elif verb in 'Ca':
            # Right
            self.currCol += n
        elif verb == 'D':
            # Left
            self.currCol -= n
        elif verb == 'E':
            self.currRow += n
            self.currCol = 0
        elif verb == 'F':
            self.currRow -= n
            self.currCol = 0
        elif verb == 'G`':
            self.currCol = self.csiParam[0] - 1
        elif verb == 'd':
            self.currRow = self.csiParam[0] - 1
        self.clampCursorToBounds()

    def do_DCH(self):
        """
        Delete Chars
        """
        logger.info('do_DCH()')
        n = self.getNumber()

        columns = self.cells[self.currRow]
        end = max(self.cols, self.currCol + n)

        columns[self.currCol: end] = columns[self.currCol + n: self.currCol + n + n]
        for i in range(end, self.cols):
            columns[i] = Texel()
            self._resetCell(columns[i])

        #for i in range(self.currCol, self.cols):
        #    if i + n < self.cols:
        #        columns[i] = copy.deepcopy(columns[i + n])
        #    else:
        #        self._resetCell(columns[i])

    def do_DECSTBM(self):
        """
        Start Scroll Region
        """
        if not self.csiParam:
            newTop = 0
            newBottom = self.rows - 1
        elif len(self.csiParam) < 2:
            return
        else:
            newTop = self.csiParam[0] - 1
            newBottom = self.csiParam[1] - 1

        newTop = max(min(self.rows, newTop), 0)
        newBottom = max(min(self.rows, newBottom), 0)

        if newTop > newBottom:
            return

        self.scrollMin = newTop
        self.scrollMax = newBottom

        if self.scrollMin:
            self.state |= STATE_SCROLL_SHORT

        if self.scrollMax != self.rows - 1:
            self.state |= STATE_SCROLL_SHORT

        if not self.scrollMin and self.scrollMax == self.rows - 1:
            self.state &= ~STATE_SCROLL_SHORT

    def _resetCell(self, cell):
        cell.char = 0x20
        cell.attr = self.currAttr
        cell.color = self.colors

    def do_DL(self):
        """
        Delete Lines
        """
        n = self.getNumber()

        for i in range(self.currRow, self.scrollMax):

            if i + n < self.scrollMax:
                self.cells[i] = copy.deepcopy(self.cells[i + n])
            else:
                columns = self.cells[i]
                for j in range(self.cols):
                    self._resetCell(columns[j])

    def do_ECH(self):
        """
        Erase Chars
        """
        n = self.getNumber()

        columns = self.cells[self.currRow]
        for i in range(self.currCol, self.currCol + n):
            if i > self.cols:
                break
            self._resetCell(columns[i])

    def do_ED(self):
        """
        Erase Display
        """
        startRow = 0
        startCol = 0

        if self.csiParam and self.csiParam[0] == 2:
            endRow = self.rows - 1
            endCol = self.cols - 1
        elif self.csiParam and self.csiParam[0] == 1:
            endRow = self.currRow
            endCol = self.currCol
        else:
            startRow = self.currRow
            startCol = self.currCol
            endRow = self.rows - 1
            endCol = self.cols - 1

        for r in range(startRow, endRow + 1):
            columns = self.cells[r]
            for c in range(startCol, endCol + 1):
                self._resetCell(columns[c])

    def do_EL(self):
        """
        Erase Line
        """
        logger.info('do_EL() -> %s', self.csiParam)
        cmd = 0
        if self.csiParam:
            cmd = self.csiParam[0]

        if cmd == 1:
            eraseStart = 0
            eraseEnd = self.currCol
        elif cmd == 2:
            eraseStart = 0
            eraseEnd = self.cols - 1
        else:
            eraseStart = self.currCol
            eraseEnd = self.cols - 1

        logger.info('Erase %s - %s', eraseStart, eraseEnd)

        columns = self.cells[self.currRow]
        for i in range(eraseStart, eraseEnd + 1):
            self._resetCell(columns[i])

    def do_ICH(self):
        """
        Insert Chars
        """
        n = self.getNumber()

        columns = self.cells[self.currRow]
        for i in range(self.cols, self.cols + n):
            columns[i] = copy.deepcopy(columns[i - n])
        for i in range(self.currCol, self.currCol + n):
            self._resetCell(columns[i])

    def getNumber(self):
        n = 1
        if self.csiParam and self.csiParam[0] > 0:
            n = self.csiParam[0]
        return n

    def do_IL(self):
        n = self.getNumber()

        for i in range(self.scrollMax, self.currRow - 1, -1):
            self.cells[i] = copy.deepcopy(self.cells[i - n])
        for i in range(self.currRow, self.currRow + n):
            if i > self.scrollMax:
                break
            columns = self.cells[i]
            for j in range(self.cols):
                self._resetCell(columns[j])

    def do_RESTORECUR(self):
        """
        Restore Cursor
        """
        self.currCol = self.savedX
        self.currRow = self.savedY

    def do_SAVECUR(self):
        """
        Save Cursor
        """
        self.savedX = self.currCol
        self.savedY = self.currRow

    def do_SGR(self):
        """
        Set Graphics
        """
        logger.info('do_SGR() -> %s', self.csiParam)
        if not self.csiParam:
            # Reset
            self.currAttr = curses.A_NORMAL
            self.colors = defaultFg | (defaultBg << 4)
            self.fg = 7
            self.bg = 0
            return

        for param in self.csiParam:
            if param == 0:
                # Reset
                self.currAttr = curses.A_NORMAL
                self.colors = defaultFg | (defaultBg << 4)
                self.fg = 7
                self.bg = 0
                continue

            if param in {1, 2, 4}:
                # Bold
                self.currAttr |= curses.A_BOLD
                self.colors |= 8
                continue

            if param == 5:
                # Blink
                self.currAttr |= curses.A_BLINK
                self.colors |= 128
                continue

            if param == 7:
                # Reverse
                self.currAttr |= curses.A_REVERSE
                continue

            if param == 27:
                # Reverse Off
                self.currAttr &= ~curses.A_REVERSE
                continue

            if param == 8:
                # Invisible
                self.currAttr |= curses.A_INVIS
                continue

            if param == 10:
                self.state &= ~STATE_ALT_CHARSET
                continue

            if param == 11:
                self.state |= STATE_ALT_CHARSET
                continue

            if param in {22, 24}:
                # Bold Off
                self.currAttr &= ~curses.A_BOLD
                self.colors &= ~8
                continue

            if param == 25:
                # Blink Off
                self.currAttr &= ~curses.A_BLINK
                self.colors &= ~128
                continue

            if param == 28:
                # Invisible Off
                self.currAttr &= ~curses.A_INVIS
                continue

            if 30 <= param <= 37:
                # Set fg color
                self.fg = self.colorValues[param - 30] & 0xF
            elif 40 <= param <= 47:
                # set bg color
                self.bg = self.colorValues[param - 40] & 0x7
            elif param == 39:
                # Reset fg
                self.fg = defaultFg
            elif param == 49:
                self.bg = defaultBg

            self.colors = self.fg | (self.bg << 4)
            if self.currAttr & curses.A_BOLD:
                self.colors |= 8
            if self.currAttr & curses.A_BLINK:
                self.colors |= 128

    def do_DEC_RM(self):
        """
        Reset Mode
        """
        logger.info('do_DEC_RM() -> %s', self.csiParam)
        if not self.csiParam:
            return
        for param in self.csiParam:
            if param == 25:
                self.state |= STATE_CURSOR_INVIS
            elif param == 9:
                self.state &= ~STATE_MOUSE

    def do_DEC_SM(self):
        """
        Set Mode
        """
        logger.info('do_DEC_SM() %s', self.csiParam)
        if not self.csiParam:
            return

        for param in self.csiParam:
            if param == 25:
                self.state &= ~STATE_CURSOR_INVIS
            elif param == 9:
                self.state |= STATE_MOUSE

    def erase(self):
        for row in self.cells:
            for cell in row:
                self._resetCell(cell)

    def eraseRow(self, rowNum):
        if rowNum == -1:
            rowNum = self.currRow

        columns = self.cells[rowNum]
        for i in range(self.cols):
            self._resetCell(columns[i])

    def eraseRows(self, startRow):
        if startRow < 0:
            return

        for row in range(startRow, self.rows):
            self.eraseRow(row)

    def eraseCol(self, col):
        if col == -1:
            col = self.currCol

        for i in range(self.rows):
            self._resetCell(self.cells[i][col])

    def eraseCols(self, startCol):
        if startCol < 0:
            return

        for col in range(startCol, self.cols):
            self.eraseCol(col)

    def escapeStart(self):
        self.state |= STATE_ESCAPE_MODE
        self.escBuf = ''

    def escapeCancel(self):
        self.state &= ~STATE_ESCAPE_MODE
        self.escBuf = ''

    def setTitle(self):
        logger.info('setTitle() -> %s', self.escBuf)
        if self.escBuf[1] != '0' or self.escBuf[2] != ';':
            return
        self.title = ''
        for i in range(3, 79):
            if self.escBuf[i] == '\a':
                break
            self.title += self.escBuf[i]

        self.state |= STATE_TITLE_CHANGED

    def tryEscapeSequence(self):
        firstChar = self.escBuf[0]
        lastChar = self.escBuf[-1]

        if not firstChar:
            return
        if firstChar == 'M':
            self.scrollUp()
            self.escapeCancel()
            return
        if firstChar == '(' and len(self.escBuf) > 1:
            if self.escBuf[1] == 'B':
                self.state &= ~STATE_ALT_CHARSET
                self.escapeCancel()
            elif self.escBuf[1] == '0':
                self.state |= STATE_ALT_CHARSET
                self.escapeCancel()
            return
        if firstChar not in '[]':
            self.escapeCancel()
            return

        if firstChar == '[' and self.validEscapeSuffix(lastChar):
            self.startCSI()
            self.escapeCancel()
        elif firstChar == ']' and lastChar == '\a':
            self.setTitle()
            self.escapeCancel()
        if len(self.escBuf) + 1 >= ESC_SEQ_BUF_SIZE:
            self.escapeCancel()

    @staticmethod
    def validEscapeSuffix(c):
        return (
                ('a' <= c <= 'z') or
                ('A' <= c <= 'Z') or
                c in '@`'
        )

    def clampCursorToBounds(self):
        self.currRow = max(min(self.rows, self.currRow), 0)
        self.currCol = max(min(self.cols, self.currCol), 0)

    def putChar(self, c):
        if self.currCol >= self.cols:
            self.currCol = 0
            self.scrollDown()

        columns = self.cells[self.currRow]
        columns[self.currCol].char = c
        columns[self.currCol].attr = self.currAttr
        columns[self.currCol].color = self.colors
        self.currCol += 1

    def renderCtrlChar(self, c):
        c = chr(c)
        if c == '\r':
            self.currCol = 0
        elif c == '\n':
            self.scrollDown()
        elif c == '\b':
            if self.currCol > 0:
                self.currCol -= 1
        elif c == '\t':
            self.putChar(0x20)
            while self.currCol % 8:
                self.putChar(0x20)

        elif c == '\x1B':
            self.escapeStart()
        elif c == '\x0E':
            # Enter Graphical Char Mode
            self.state |= STATE_ALT_CHARSET
        elif c == '\x0F':
            # Exit Graphical Char Mode
            self.state &= ~STATE_ALT_CHARSET
        elif c == '\x9B':
            # 8-bit Esc equivalent
            self.escapeStart()
            self.escBuf += '['
        elif c in '\x18\x1A':
            self.escapeCancel()
        elif c == '\a':
            # Beep
            pass
        else:
            # NFI
            pass

    def isModeACS(self):
        return self.state & STATE_ALT_CHARSET

    def isModeEscaped(self):
        return self.state & STATE_ESCAPE_MODE

    def render(self, data):
        for c in data:
            c = ord(c)
            if c == 0:
                continue
            if self.isModeEscaped() and len(self.escBuf) < ESC_SEQ_BUF_SIZE:
                self.escBuf += chr(c)
                self.tryEscapeSequence()
            else:
                if 1 <= c <= 31:
                    self.renderCtrlChar(c)
                    continue
                self.putChar(c)

    def resize(self, width, height):
        if not (width and height):
            return

        deltaX = width - self.cols
        deltaY = height - self.rows
        startX = self.cols
        startY = self.rows

        cells = self.cells
        self.cells = [[Texel() for _x in range(width)] for _y in range(height)]
        for i, c in enumerate(cells):
            if i < len(self.cells):
                self.cells[i][:width] = c[:width]
            if deltaX > 0:
                self.cells[i].extend(Texel() for _ in range(deltaX))

        self.cols = width
        self.rows = height

        if not self.state & STATE_SCROLL_SHORT:
            self.scrollMax = height - 1

        self.clampCursorToBounds()
        if deltaX > 0:
            self.eraseCols(startX)
        if deltaY > 0:
            self.eraseRows(startY)
        self.currCol = 0
        self.currRow = 0

        if not PLATFORM_WINDOWS:
            b = struct.pack('HHHH', height, width, 0, 0)
            fcntl.ioctl(self.__ptyFd, termios.TIOCSWINSZ, b)
            kill(self.__childPid, signal.SIGWINCH)

    def scrollDown(self):
        self.currRow += 1
        if self.currRow <= self.scrollMax:
            return

        self.currRow = self.scrollMax
        for i in range(self.scrollMin, self.scrollMax):
            self.cells[i] = self.cells[i + 1]
        self.cells[self.scrollMax] = [Texel() for _ in range(self.cols)]
        self.eraseRow(self.scrollMax)

    def scrollUp(self):
        self.currRow -= 1
        if self.currRow >= self.scrollMin:
            return

        self.currRow = self.scrollMin
        for i in range(self.scrollMax, self.scrollMin, -1):
            self.cells[i] = self.cells[i - 1]
        self.cells[self.scrollMin] = [Texel() for _ in range(self.cols)]
        self.eraseRow(self.scrollMin)

    def write(self, keyCode):
        logger.info('write(%s)', keyCode)
        keyTrans = {
            '\n': b'\r',
            curses.KEY_UP: b'\x1B[A',
            curses.KEY_DOWN: b'\x1B[B',
            curses.KEY_RIGHT: b'\x1B[C',
            curses.KEY_LEFT: b'\x1B[D',
            curses.KEY_BACKSPACE: b'\x1B\b',
            curses.KEY_IC: b'\x1b[2~',
            curses.KEY_DC: b'\x1b[3~',
            curses.KEY_HOME: b'\x1b[7~',
            curses.KEY_END: b'\x1b[8~',
            curses.KEY_PPAGE: b'\x1b[5~',
            curses.KEY_NPAGE: b'\x1b[6~',
            curses.KEY_SUSPEND: b'\x1A',
            curses.KEY_F1: b'\x1b[11~',
            curses.KEY_F2: b'\x1b[12~',
            curses.KEY_F3: b'\x1b[13~',
            curses.KEY_F4: b'\x1b[14~',
            curses.KEY_F5: b'\x1b[15~',
            curses.KEY_F6: b'\x1b[17~',
            curses.KEY_F7: b'\x1b[18~',
            curses.KEY_F8: b'\x1b[19~',
            curses.KEY_F9: b'\x1b[20~',
            curses.KEY_F10: b'\x1b[21~',
            curses.KEY_F11: b'\x1b[23~',
            curses.KEY_F12: b'\x1b[24~',
        }
        buffer = keyTrans.get(keyCode)
        if not buffer:
            self.writePipe(keyCode)
        else:
            self.writePipe(buffer)

    if not PLATFORM_WINDOWS:
        def readPipe(self):
            if self.__ptyFd < 0:
                return -1

            try:
                childPid, status = waitpid(self.__childPid, os.WNOHANG)
            except ChildProcessError:
                self.state |= STATE_CHILD_EXITED
                return -1

            if childPid in {self.__childPid, -1}:
                logger.info('waitpid returns: %s', childPid)
                self.state |= STATE_CHILD_EXITED
                return -1

            poller = select.poll()
            poller.register(self.__ptyFd, select.POLLIN)
            count = 0
            while poller.poll(10):
                try:
                    buffer = os.read(self.__ptyFd, 16384).decode('utf-8')
                    if buffer:
                        try:
                            self.render(buffer)
                        except:
                            logger.exception('terminal.render()')
                        count += len(buffer)
                    else:
                        break
                except:
                    break
                break
            return count
    else:
        def readPipe(self):
            count = 0
            try:
                buffer = self.__childPid.read()
            except BrokenPipeError:
                return -1

            if buffer:
                buffer = buffer.decode('utf-8')
                count = len(buffer)
                try:
                    self.render(buffer)
                except:
                    logger.exception('terminal.render()')
            return count

    if not PLATFORM_WINDOWS:
        def writePipe(self, keyCode):
            os.write(self.__ptyFd, bytes(keyCode, encoding='utf-8'))
    else:
        def writePipe(self, keyCode):
            if keyCode == '\r':
                keyCode = '\n'
            self.__childPid.write(bytes(keyCode, encoding='utf-8'))

