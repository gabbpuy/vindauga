# -*- coding: utf-8 -*-
from __future__ import annotations

import logging
import os
import struct
import sys
from dataclasses import dataclass
from typing import Optional, IO

from vindauga.utilities.singleton import Singleton
from vindauga.types.point import Point

if sys.platform != 'win32':
    import fcntl
    import termios

if sys.platform == 'win32':
    import win32console
    from win32console import PyConsoleScreenBufferType
    import win32file
    INPUT = 0
    STARTUP_OUTPUT = 1
    ACTIVE_OUTPUT = 2


logger = logging.getLogger(__name__)


class ConsoleCtl(metaclass=Singleton):
    """
    Handles terminal type detection and capability management
    """

    def __init__(self):
        self._term_type = None
        self._setup_console()

    @classmethod
    def getInstance(cls) -> ConsoleCtl:
        """
        Get singleton ConsoleCtl instance
        """
        return cls()

    @classmethod
    def destroyInstance(cls):
        """
        Destroy singleton instance (called during cleanup)
        """
        if hasattr(cls, '_instance') and cls._instance:
            cls._instance._cleanup_console()
            cls._instance = None

    def get_input_fd(self) -> int:
        """
        Get input file descriptor for event polling (Unix only)
        """
        if sys.platform == 'win32' or not hasattr(self, 'fds'):
            return -1
        return self.fds[0]
    
    def get_output_fd(self) -> int:
        """
        Get output file descriptor (Unix only)
        """
        if sys.platform == 'win32' or not hasattr(self, 'fds'):
            return -1
        return self.fds[1]

    if sys.platform == 'win32':
        @dataclass
        class ConsoleHandle:
            handle: Optional[PyConsoleScreenBufferType] = None
            owning: bool = False

        def _setup_console(self):
            """
            Set up Windows console handles
            """
            self.cn = [self.ConsoleHandle() for _ in range(3)]
            self.owns_console = False

            # Check if we have console handles via standard handles
            channels = [
                (win32console.STD_INPUT_HANDLE, INPUT),
                (win32console.STD_OUTPUT_HANDLE, STARTUP_OUTPUT),
                (win32console.STD_ERROR_HANDLE, STARTUP_OUTPUT)
            ]

            have_console = False
            for std_handle_type, index in channels:
                try:
                    handle = win32console.GetStdHandle(std_handle_type)
                    if self._is_console_handle(handle):
                        have_console = True
                        if not self._is_valid_handle(self.cn[index].handle):
                            self.cn[index].handle = handle
                            self.cn[index].owning = False
                except Exception:
                    logger.exception('Failed to handle console handle: %s, %s', std_handle_type, index)
                    pass

            logger.info("Console handles created: %s", self.cn)
            # Allocate console if we don't have one
            if not have_console:
                try:
                    win32console.FreeConsole()
                    win32console.AllocConsole()
                    self.owns_console = True
                except Exception:
                    pass

            # Set up input handle if not already set
            if not self._is_valid_handle(self.cn[INPUT].handle):
                logger.info('Input Handle not Set, creating...')
                try:
                    handle = win32file.CreateFile(
                        'CONIN$',
                        win32file.GENERIC_READ | win32file.GENERIC_WRITE,
                        win32file.FILE_SHARE_READ,
                        None,
                        win32file.OPEN_EXISTING,
                        0,
                        0
                    )
                    # self.cn[INPUT] = {'handle': handle, 'owning': True}
                    self.cn[INPUT].handle = handle
                    self.cn[INPUT].owning = True
                except Exception:
                    pass

            # Set up startup output handle if not already set
            if not self._is_valid_handle(self.cn[STARTUP_OUTPUT].handle):
                logger.info('Startup Output Handle not Set, creating...')
                try:
                    handle = win32file.CreateFile(
                        'CONOUT$',
                        win32file.GENERIC_READ | win32file.GENERIC_WRITE,
                        win32file.FILE_SHARE_WRITE,
                        None,
                        win32file.OPEN_EXISTING,
                        0,
                        0
                    )
                    self.cn[STARTUP_OUTPUT].handle = handle
                    self.cn[STARTUP_OUTPUT].owning = True
                except Exception:
                    pass

            # Create active output screen buffer
            try:
                logger.info('Creating Active Output Handle')
                handle = win32console.CreateConsoleScreenBuffer(
                    win32file.GENERIC_READ | win32file.GENERIC_WRITE,
                    0,
                    None,
                    win32console.CONSOLE_TEXTMODE_BUFFER)
                self.cn[ACTIVE_OUTPUT].handle = handle
                self.cn[ACTIVE_OUTPUT].owning = True

                # Set screen buffer size to match window size
                try:
                    sb_handle: PyConsoleScreenBufferType = self.cn[STARTUP_OUTPUT].handle
                    sb_info = sb_handle.GetConsoleScreenBufferInfo()
                    window = sb_info['Window']
                    size = win32console.PyCOORDType(
                        window.Right - window.Left + 1,
                        window.Bottom - window.Top + 1
                    )
                    sb_handle.SetConsoleScreenBufferSize(size)
                except Exception:
                    logger.exception('Failed to get console screen buffer size')
                handle.SetConsoleActiveScreenBuffer()
            except Exception:
                logger.exception('Failed to create Active Output Handle')

        def _cleanup_console(self):
            """
            Clean up Windows console resources
            """
            try:
                # Restore startup output as active buffer
                if self._is_valid_handle(self.cn[STARTUP_OUTPUT].handle):  # startupOutput
                    sb_handle: PyConsoleScreenBufferType = self.cn[STARTUP_OUTPUT].handle
                    sb_handle.SetConsoleActiveScreenBuffer()

                # Close owned handles
                for console in self.cn:
                    if console.owning and self._is_valid_handle(console.handle):
                        try:
                            console.handle.Close()
                        except Exception:
                            pass

                # Free console if we allocated it
                if self.owns_console:
                    win32console.FreeConsole()
            except Exception:
                pass

        def write(self, data: str) -> None:
            """
            Write to Windows console
            """
            try:
                if data and self.cn[ACTIVE_OUTPUT].handle:  # activeOutput
                    self.cn[ACTIVE_OUTPUT].handle.WriteConsole(data)
            except Exception:
                pass

        def _is_valid_handle(self, handle):
            """
            Check if Windows handle is valid
            """
            return handle and handle != win32file.INVALID_HANDLE_VALUE

        def _is_console_handle(self, handle):
            """
            Check if Windows handle is a console handle
            """
            try:
                handle.GetConsoleMode()
                return True
            except Exception:
                return False

        def get_fds(self) -> list[int]:
            """
            Get file descriptors - not applicable on Windows
            """
            return []
        
        def get_size(self) -> Point:
            """
            Get console size
            """
            try:
                sb_handle: PyConsoleScreenBufferType = self.cn[ACTIVE_OUTPUT].handle
                sb_info = sb_handle.GetConsoleScreenBufferInfo()
                window = sb_info['Window']
                logger.info('Window Size is %s', window)
                return Point(
                    max(window.Right - window.Left + 1, 0),
                    max(window.Bottom - window.Top + 1, 0)
                )
            except Exception:
                logger.exception(
                    "Failed to get console size")
                return Point(0, 0)
        
        def get_font_size(self) -> Point:
            """
            Get console font size
            """
            try:
                sb_handle: PyConsoleScreenBufferType = self.cn[ACTIVE_OUTPUT].handle
                _, font_info = sb_handle.GetCurrentConsoleFont(False)  # activeOutput
                return Point(
                    font_info.X,
                    font_info.Y
                )
            except Exception:
                return Point(0, 0)

    else:
        def _setup_console(self):
            """
            Set up Unix console file descriptors
            """
            # Unix: file descriptors
            self.files: list[Optional[IO]] = [None, None]  # [input_file, output_file]
            self.fds: list[int] = [0, 1]  # [input_fd, output_fd]
            self.owns_files = False

            if os.environ.get('VINDAUGA_USE_STDIO') is not None:
                try:
                    self.files[0] = open('/dev/tty', 'r')
                    self.files[1] = open('/dev/tty', 'w')
                    self.owns_files = True
                    self.fds[0] = self.files[0].fileno()
                    self.fds[1] = self.files[1].fileno()

                    # Set FD_CLOEXEC on file descriptors (subprocesses must not inherit)
                    for fd in self.fds:
                        flags = fcntl.fcntl(fd, fcntl.F_GETFD)
                        fcntl.fcntl(fd, fcntl.F_SETFD, flags | fcntl.FD_CLOEXEC)

                except (OSError, IOError):
                    # Fall back to stdin/stdout
                    if self.files[0]:
                        self.files[0].close()
                    if self.files[1]:
                        self.files[1].close()
                    self.fds[0] = sys.stdin.fileno()  # STDIN_FILENO
                    self.fds[1] = sys.stdout.fileno()  # STDOUT_FILENO
                    self.files[0] = sys.stdin
                    self.files[1] = sys.stdout
                    self.owns_files = False
            else:
                self.fds[0] = sys.stdin.fileno()
                self.fds[1] = sys.stdout.fileno()
                self.files[0] = sys.stdin
                self.files[1] = sys.stdout
                self.owns_files = False

        def _cleanup_console(self):
            """
            Clean up Unix console resources
            """
            if self.owns_files:
                for file in self.files:
                    if file and file not in (sys.stdin, sys.stdout):
                        try:
                            file.close()
                        except Exception:
                            pass

        def write(self, data: str) -> None:
            """
            Write to Unix console
            """
            try:
                if self.files and self.files[1]:
                    self.files[1].flush()
                written = 0
                data = data.encode('utf-8')
                while written < len(data):
                    written += os.write(self.fds[1], data[written:])
            except Exception:
                pass

        def get_fds(self) -> tuple[int, int]:
            """
            Get both file descriptors
            """
            return tuple(self.fds)
        
        def get_size(self) -> Point:
            """
            Get console size
            """

            for fd in self.fds:
                try:
                    # TIOCGWINSZ ioctl to get window size
                    result = fcntl.ioctl(fd, termios.TIOCGWINSZ, struct.pack('HHHH', 0, 0, 0, 0))
                    rows, cols, xpixel, ypixel = struct.unpack('HHHH', result)
                    env_col = int(os.environ.get('COLUMNS', '999999'))
                    env_row = int(os.environ.get('LINES', '999999'))

                    return Point(
                        min(max(cols, 0), max(env_col, 0)),
                        min(max(rows, 0), max(env_row, 0))
                    )
                except (OSError, ValueError):
                    continue
            return Point(0, 0)
        
        def get_font_size(self) -> Point:
            """
            Get console font size
            """
            # Fallback: calculate from window size in pixels vs characters
            for fd in self.fds:
                try:
                    result = fcntl.ioctl(fd, termios.TIOCGWINSZ, struct.pack('HHHH', 0, 0, 0, 0))
                    rows, cols, xpixel, ypixel = struct.unpack('HHHH', result)
                    
                    if cols > 0 and rows > 0 and xpixel > 0 and ypixel > 0:
                        return Point(
                            xpixel // max(cols, 1),
                            ypixel // max(rows, 1)
                        )
                except (OSError, ValueError):
                    continue
            return Point(0, 0)
