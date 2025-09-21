# -*- coding: utf-8 -*-
import functools

import atexit
from copy import copy
import curses
from functools import lru_cache
import itertools
import logging
import os
from os import kill, execvpe, waitpid
import platform
import select
from signal import *
import struct
from typing import Tuple, Union

from vindauga.utilities.text.text import Text
from vindauga.utilities.screen.screen_cell import ScreenCell
from vindauga.utilities.colours.colour_attribute import ColourAttribute
from vindauga.utilities.platform.events.utf8_handler import UTF8CharacterAssembler


TERMINAL_KEY_TRANSLATION = {
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

PLATFORM_WINDOWS = platform.platform().lower().startswith('windows')
if not PLATFORM_WINDOWS:
    import fcntl
    import pwd
    import termios
    import pty
    signals = [SIGINT, SIGQUIT]
else:
    from .windows_shell import WindowsShell
    signals = [SIGINT, SIGBREAK]

logger = logging.getLogger(__name__)

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

    def __init__(self, width: int, height: int, flags: int, command=None, shell_type='pwsh', *commandArgs):
        self.rows = height
        self.cols = width
        self.shell_type = shell_type
        self.col = []
        self.currRow = 0
        self.currCol = 0
        self.currAttr = curses.A_NORMAL
        self.savedX = 0
        self.savedY = 0
        self.scrollMin = 0
        self.scrollMax = height - 1
        self._utf8_assembler = UTF8CharacterAssembler()  # Handles UTF-8 character assembly
        self.flags = flags
        self.state = 0
        self.fg = defaultFg
        self.bg = defaultBg
        self.__childPid = -1
        self.__ptyFd = None
        if command:
            self.command = command
            self.commandArgs = [os.path.basename(command)]
            self.commandArgs.extend(commandArgs)
        else:
            self.command, self.commandArgs = self.getShell(self.shell_type)
        logger.info('Command is %s, %s', self.command, self.commandArgs)
        self.csiParam = []
        self.escBuf = ''
        self.colorValues = [
            0, 4, 2, 6, 1, 5, 3, 7
            ]
        self.initColors()
        self._color_cache = {}
        # Initialize colors after initColors() is called
        self.colors = self._create_colour_attribute(defaultFg, defaultBg)
        self.title = ''
        # Initialize cells with ScreenCell objects containing space characters
        self.cells = []
        for _y in range(height):
            row = []
            for _x in range(width):
                cell = ScreenCell()
                cell.char = ' '  # Use string instead of int
                cell.attr = self._create_colour_attribute()  # Use proper ColourAttribute
                row.append(cell)
            self.cells.append(row)
        self.executeCommand()
        atexit.register(self._destroy, self.__childPid)

        from .terminal_view import TerminalView
        if not TerminalView.OriginalSignals:
            TerminalView.OriginalSignals = {s: signal(s, SIG_IGN) for s in signals}

    def _create_colour_attribute(self, fg: int = None, bg: int = None, attr: int = 0) -> ColourAttribute:
        """
        Convert terminal colors to ColourAttribute
        """
        # Use current colors if not specified
        if fg is None:
            fg = self.fg if hasattr(self, 'fg') else defaultFg
        if bg is None:
            bg = self.bg if hasattr(self, 'bg') else defaultBg
            
        # Create ColourAttribute from terminal color values
        # Terminal uses standard ANSI colors (0-15), map to BIOS-style attributes
        bios_attr = (bg << 4) | fg
        
        # Add terminal attributes like reverse, bold, etc.
        if attr & curses.A_REVERSE:
            bios_attr = ((bios_attr & 0x0F) << 4) | ((bios_attr & 0xF0) >> 4)
        if attr & curses.A_BOLD:
            bios_attr |= 0x08  # High intensity

        if bios_attr not in self._color_cache:
            self._color_cache[bios_attr] = ColourAttribute.from_bios(bios_attr)
        return self._color_cache[bios_attr]

    @staticmethod
    def getShell(shell_type: str = 'pwsh') -> Tuple[str, list]:
        if not PLATFORM_WINDOWS:
            profile = pwd.getpwuid(os.getuid())
            if not profile:
                shell = '/bin/sh'
            elif not profile.pw_shell:
                shell = '/bin/sh'
            else:
                shell = profile.pw_shell
            return shell, [os.path.basename(shell), '-l']

        # Windows shell options
        if shell_type.lower() == 'cmd':
            # cmd.exe with UTF-8 encoding
            return 'cmd.exe', ['/c', 'chcp 65001 >nul: & cmd.exe /E:ON /F:ON']
        elif shell_type.lower() in ('pwsh', 'powershell'):
            # PowerShell Core (pwsh) - interactive mode with completion enabled
            return 'pwsh', ['-NoLogo']
        else:
            # Default to PowerShell Core
            return 'pwsh', ['-NoLogo']

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
                env['TERM'] = 'rxvt'
                env['COLUMNS'] = str(self.cols)
                env['LINES'] = str(self.rows)
                env["LANG"] = 'en_US.UTF-8'
                env["LC_CTYPE"] = 'en_US.UTF-8'
                logger.info('Executing %s, %s', self.command, self.commandArgs)
                execvpe(self.command, self.commandArgs, env=env)

            if self.__childPid == -1:
                raise RuntimeError
    else:
        def executeCommand(self):
            command = [self.command] + self.commandArgs
            self.__childPid = WindowsShell(command)
            self.__ptyFd = self.__childPid()
            if self.__ptyFd is None:
                logger.error("*** __ptyFd is None, raising RuntimeError")
                raise RuntimeError

    @staticmethod
    def _destroy(pid):
        try:
            kill(pid, SIGKILL)
        except:
            pass

    def destroy(self):
        try:
            kill(self.__childPid, SIGKILL)
        except:
            pass
        from .terminal_view import TerminalView
        if not TerminalView.ActiveTerminals:
            # Restore original signal handlers, we were the last terminal
            for signal_, handler in TerminalView.OriginalSignals.items():
                signal(signal_, handler)

    def initColors(self):
        """
        Initialize color palette with ColourAttribute objects
        """
        self.col.append(ColourAttribute.from_bios(0))  # Default: black on black
        for bg, fg in itertools.product(range(8), range(8)):
            if bg != 7 or fg != 0:  # Skip white on black (default is reversed)
                bios_attr = (bg << 4) | fg
                self.col.append(ColourAttribute.from_bios(bios_attr))

    @property
    def pid(self) -> int:
        return self.__childPid

    @property
    def ptyFd(self) -> int:
        return self.__ptyFd

    def setColors(self, fg: int, bg: int):
        """
        Set current foreground and background colors
        """
        self.fg = fg
        self.bg = bg
        self.colors = self._create_colour_attribute(fg, bg)

    def getColors(self) -> ColourAttribute:
        """
        Get current colors as ColourAttribute
        """
        return self.colors

    def startCSI(self):
        verb = self.escBuf[-1]
        self.csiParam = []

        for p in self.escBuf[1:-1]:
            if not ('0' <= p <= '9' or p in {';', '?'}):
                break
            if p == '?':
                continue

            if p == ';':
                if len(self.csiParam) >= MAX_CSI_ESC_PARAMS:
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
        Move Cursor
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

    def do_CUx(self, verb: str):
        """
        Relative Cursor
        CUU, CUD, CUF, CUB, CNL, CPL, CHA, HPT, VPA, VPR, HPA

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
        elif verb in 'G`':
            self.currCol = self.csiParam[0] - 1
        elif verb == 'd':
            self.currRow = self.csiParam[0] - 1
        self.clampCursorToBounds()

    def do_DCH(self):
        """
        Delete Chars
        """
        n = self.getNumber()
        columns = self.cells[self.currRow]
        for i in range(self.currCol, self.cols):
            if i + n < self.cols:
                columns[i] = columns[i + n]
            else:
                cell = columns[i]
                cell.char = ' '
                cell.attr = self._create_colour_attribute()

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

    def do_DL(self):
        """
        Delete Lines
        """
        n = self.getNumber()

        for i in range(self.currRow, self.scrollMax + 1):
            if i + n <= self.scrollMax:
                self.cells[i] = self.cells[i + n]
            else:
                self._resetRow(i)

    def do_ECH(self):
        """
        Erase Chars
        """
        n = self.getNumber()

        columns = self.cells[self.currRow]
        for i in range(self.currCol, max(self.cols, self.currCol + n)):
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

        columns = self.cells[self.currRow]
        for i in range(eraseStart, eraseEnd + 1):
            self._resetCell(columns[i])

    def do_ICH(self):
        """
        Insert Blank Chars
        """
        n = self.getNumber()

        columns = self.cells[self.currRow]
        for i in range(self.cols - 1, self.currCol + n - 1, -1):
            columns[i] = columns[i - n]

        for i in range(self.currCol, self.currCol + n):
            self._resetCell(columns[i])

    def do_IL(self):
        """
        Insert Line
        """
        n = self.getNumber()
        for i in range(self.scrollMax, self.currRow + n - 1, -1):
            self.cells[i] = copy(self.cells[i - n])
        for i in range(self.currRow, max(self.scrollMax, self.currRow + n)):
            self._resetRow(i)

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
                # 1=bold, 4=underline
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
                # Bold/Underline Off
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
            elif 90 <= param <= 97:
                self.fg = self.colorValues[param - 90] & 0xF
                self.currAttr |= curses.A_BOLD
            elif 100 <= param <= 107:
                self.bg = self.colorValues[param - 100] & 0x7
                self.currAttr |= curses.A_BOLD
            elif param == 39:
                # Reset fg
                self.fg = defaultFg
            elif param == 49:
                self.bg = defaultBg

            self.colors = self._create_colour_attribute(self.fg, self.bg, self.currAttr)

    def do_DEC_RM(self):
        """
        Reset Mode
        """
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
        if not self.csiParam:
            return

        for param in self.csiParam:
            if param == 25:
                self.state &= ~STATE_CURSOR_INVIS
            elif param == 9:
                self.state |= STATE_MOUSE

    def getNumber(self) -> int:
        n = 1
        if self.csiParam and self.csiParam[0] > 0:
            n = self.csiParam[0]
        return n

    def erase(self):
        for i in range(self.rows):
            self._resetRow(i)

    def eraseRow(self, rowNum: int):
        if rowNum == -1:
            rowNum = self.currRow

        self._resetRow(rowNum)

    def eraseRows(self, startRow: int):
        if startRow < 0:
            return

        for row in range(startRow, self.rows):
            self.eraseRow(row)

    def eraseCol(self, col: int):
        if col < 0:
            col = self.currCol

        for i in range(self.rows):
            self._resetCell(self.cells[i][col])

    def eraseCols(self, startCol: int):
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
        if self.escBuf[1] != '0' or self.escBuf[2] != ';':
            return
        self.title = ''
        title, _ = self.escBuf[3:].split('\a', 1)
        self.title = title
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
            return
        elif firstChar == ']' and lastChar == '\a':
            self.setTitle()
            self.escapeCancel()
            return
        if len(self.escBuf) + 1 >= ESC_SEQ_BUF_SIZE:
            self.escapeCancel()


    @staticmethod
    @lru_cache(maxsize=256)
    def validEscapeSuffix(c: str) -> bool:
        return (
                ('a' <= c <= 'z') or
                ('A' <= c <= 'Z') or
                c in '@`'
        )

    def clampCursorToBounds(self):
        self.currRow = max(min(self.rows - 1, self.currRow), 0)
        self.currCol = max(min(self.cols - 1, self.currCol), 0)

    def putChar(self, c: str):
        """
        Put a UTF-8 character, handling combining characters properly
        """
        if self.currCol >= self.cols:
            self.currCol = 0
            self.scrollDown()

        cell = self.cells[self.currRow][self.currCol]
        
        # Check if this is a combining character (width = 0)
        char_width = Text.width(c)
        if char_width == 0 and self.currCol > 0:
            # Combining character - add to previous cell
            prev_cell = self.cells[self.currRow][self.currCol - 1]
            if prev_cell.char:
                prev_cell.char += c
            return  # Don't advance cursor for combining characters
        
        # Normal character
        cell.char = c
        cell.attr = self._create_colour_attribute(attr=self.currAttr)
        
        # Advance cursor by character width (1 for normal chars, 2 for wide chars)
        self.currCol += max(1, char_width)

    def renderCtrlChar(self, c: str):
        if c == '\r':
            # carriage return
            self.currCol = 0
        elif c == '\n':
            # line feed
            self.scrollDown()
        elif c == '\b':
            # backspace
            if self.currCol > 0:
                self.currCol -= 1
        elif c == '\t':
            # tab
            if not self.currCol % 8:
                self.putChar(' ')
            while self.currCol % 8:
                self.putChar(' ')
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

    def isModeACS(self) -> bool:
        return bool(self.state & STATE_ALT_CHARSET)

    def isModeEscaped(self) -> bool:
        return bool(self.state & STATE_ESCAPE_MODE)

    def render(self, data: str):
        """
        Render UTF-8 text properly, handling combining characters and escape sequences
        """
        text_pos = 0
        
        while text_pos < len(data):
            # Get next character with proper UTF-8 handling
            success, new_text_pos, char_width = Text.next_with_width(data, text_pos)
            if not success:
                break
                
            char = data[text_pos:new_text_pos]
            
            # Skip null characters
            if char == '\x00':
                text_pos = new_text_pos
                continue
                
            if self.isModeEscaped() and len(self.escBuf) < ESC_SEQ_BUF_SIZE:
                self.escBuf += char
                self.tryEscapeSequence()
            else:
                # Check if it's a control character
                if len(char) == 1 and 1 <= ord(char) <= 31:
                    self.renderCtrlChar(char)
                else:
                    # Normal character (including combining characters)
                    self.putChar(char)
            
            text_pos = new_text_pos

    def resize(self, width: int, height: int):
        if not (width and height):
            return

        deltaX = width - self.cols
        deltaY = height - self.rows
        startX = self.cols
        startY = self.rows

        if deltaY < 0:
            cells = self.cells[-deltaY:]
            self.currRow += deltaY
        else:
            cells = self.cells[:]

        # Initialize cells with ScreenCell objects
        self.cells = []
        for _y in range(height):
            row = []
            for _x in range(width):
                cell = ScreenCell()
                cell.char = ' '
                cell.attr = self._create_colour_attribute()
                row.append(cell)
            self.cells.append(row)

        for i, c in enumerate(cells):
            if i < len(self.cells):
                self.cells[i][:width] = c[:width]
                if deltaX > 0:
                    for _ in range(deltaX):
                        cell = ScreenCell()
                        cell.char = ' '
                        cell.attr = self._create_colour_attribute()
                        self.cells[i].append(cell)

        self.cols = width
        self.rows = height

        if not self.state & STATE_SCROLL_SHORT:
            self.scrollMax = height - 1

        self.clampCursorToBounds()
        if deltaX > 0:
            self.eraseCols(startX)
        if deltaY > 0:
            self.eraseRows(startY)

        if self.currRow >= self.rows:
            self.currRow = 0

        if self.currCol >= self.cols:
            self.currCol = 0

        if not PLATFORM_WINDOWS:
            b = struct.pack('HHHH', height, width, 0, 0)
            fcntl.ioctl(self.__ptyFd, termios.TIOCSWINSZ, b)
            kill(self.__childPid, SIGWINCH)

    def scrollDown(self):
        self.currRow += 1
        if self.currRow <= self.scrollMax:
            return

        self.currRow = self.scrollMax
        self.cells[self.scrollMin: self.scrollMax] = self.cells[self.scrollMin + 1: self.scrollMax + 1]
        # Create new row of ScreenCells
        new_row = []
        for _ in range(self.cols):
            cell = ScreenCell()
            cell.char = ' '
            cell.attr = self._create_colour_attribute()
            new_row.append(cell)
        self.cells[self.scrollMax] = new_row

    def scrollUp(self):
        self.currRow -= 1
        if self.currRow >= self.scrollMin:
            return

        self.currRow = self.scrollMin
        self.cells[self.scrollMin + 1:self.scrollMax] = self.cells[self.scrollMin:self.scrollMax - 1]
        # Create new row of ScreenCells
        new_row = []
        for _ in range(self.cols):
            cell = ScreenCell()
            cell.char = ' '
            cell.attr = self._create_colour_attribute()
            new_row.append(cell)
        self.cells[self.scrollMin] = new_row

    def write(self, keyCode):
        if buffer := TERMINAL_KEY_TRANSLATION.get(keyCode):
            self.writePipe(buffer)
        else:
            self.writePipe(keyCode)

    if not PLATFORM_WINDOWS:
        def readPipe(self) -> int:
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
            while poller.poll(5):
                try:
                    # Read raw bytes and let Text class handle UTF-8 decoding
                    buffer = os.read(self.__ptyFd, 16380)
                    if buffer:
                        # Process each byte through UTF8 assembler
                        decoded_text = ""
                        for byte_val in buffer:
                            char = self._utf8_assembler.add_byte(byte_val)
                            if char is not None:
                                decoded_text += char

                        if decoded_text:
                            try:
                                self.render(decoded_text)
                            except:
                                logger.exception('terminal.render()')
                            count += len(decoded_text)
                    else:
                        break
                except:
                    break
            return count
    else:
        def readPipe(self) -> int:
            count = 0
            try:
                buffer = self.__childPid.read()
            except BrokenPipeError:
                self.state |= STATE_CHILD_EXITED
                logger.exception('readPipe() - child exited?')
                return -1

            if buffer:
                # Process each byte through UTF8 assembler
                decoded_text = ""
                for byte_val in buffer:
                    char = self._utf8_assembler.add_byte(byte_val)
                    if char is not None:
                        decoded_text += char

                if decoded_text:
                    count = len(decoded_text)
                    try:
                        self.render(decoded_text)
                    except:
                        logger.exception('terminal.render()')
            return count

    if not PLATFORM_WINDOWS:
        def writePipe(self, keyCode):
            if not isinstance(keyCode, bytes):
                keyCode = bytes(keyCode, encoding='utf-8')
            os.write(self.__ptyFd, keyCode)
    else:
        def writePipe(self, keyCode):
            if keyCode == '\r':
                self.__childPid.write(bytes(keyCode, encoding='utf-8'))
                keyCode = '\n'
            if isinstance(keyCode, str):
                self.__childPid.write(bytes(keyCode, encoding='utf-8'))
            else:
                self.__childPid.write(keyCode)

    def _resetCell(self, cell: ScreenCell):
        cell.char = ' '
        cell.attr = self._create_colour_attribute()

    def _resetRow(self, rowNum: int):
        new_row = []
        for _ in range(self.cols):
            cell = ScreenCell()
            cell.char = ' '
            cell.attr = self._create_colour_attribute()
            new_row.append(cell)
        self.cells[rowNum] = new_row
