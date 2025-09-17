# -*- coding: utf-8 -*-
from __future__ import annotations
import logging
import os
import struct
import sys
from typing import Optional, IO

if sys.platform != 'win32':
    import termios

from vindauga.types.point import Point

if sys.platform == 'win32':
    import win32console
    import win32file
else:
    import fcntl


logger = logging.getLogger(__name__)


class ConsoleCtl:
    """
    Handles terminal type detection and capability management
    """
    
    _instance: Optional[ConsoleCtl] = None
    
    def __init__(self):
        self._term_type = None
        self._setup_console()

    @classmethod
    def getInstance(cls) -> ConsoleCtl:
        """
        Get singleton ConsoleCtl instance (tvision-compatible API)
        """
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance
    
    @classmethod
    def destroyInstance(cls):
        """
        Destroy singleton instance (called during cleanup)
        """
        if cls._instance:
            cls._instance._cleanup_console()
        cls._instance = None

    def getTerminalType(self) -> str:
        """
        Get terminal type string
        """
        return self._term_type

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
        def _setup_console(self):
            """
            Set up Windows console handles - mirrors C++ ConsoleCtl constructor for Windows
            """
            # Windows: console handles
            self.cn = [{'handle': None, 'owning': False} for _ in range(3)]  # input, startupOutput, activeOutput
            self.owns_console = False

            INPUT = 0
            STARTUP_OUTPUT = 1
            ACTIVE_OUTPUT = 2

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
                        if not self._is_valid_handle(self.cn[index]['handle']):
                            self.cn[index] = {'handle': handle, 'owning': False}
                except Exception:
                    pass

            # Allocate console if we don't have one
            if not have_console:
                try:
                    win32console.FreeConsole()
                    win32console.AllocConsole()
                    self.owns_console = True
                except Exception:
                    pass

            # Set up input handle if not already set
            if not self._is_valid_handle(self.cn[INPUT]['handle']):
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
                    self.cn[INPUT] = {'handle': handle, 'owning': True}
                except Exception:
                    pass

            # Set up startup output handle if not already set
            if not self._is_valid_handle(self.cn[STARTUP_OUTPUT]['handle']):
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
                    self.cn[STARTUP_OUTPUT] = {'handle': handle, 'owning': True}
                except Exception:
                    pass

            # Create active output screen buffer
            try:
                handle = win32console.CreateConsoleScreenBuffer(
                    win32file.GENERIC_READ | win32file.GENERIC_WRITE,
                    0,
                    None,
                    win32console.CONSOLE_TEXTMODE_BUFFER,
                    None
                )
                self.cn[ACTIVE_OUTPUT] = {'handle': handle, 'owning': True}

                # Set screen buffer size to match window size
                try:
                    sb_info = win32console.GetConsoleScreenBufferInfo(self.cn[STARTUP_OUTPUT]['handle'])
                    window = sb_info['Window']
                    size = win32console.PyCOORDType(
                        window.Right - window.Left + 1,
                        window.Bottom - window.Top + 1
                    )
                    win32console.SetConsoleScreenBufferSize(handle, size)
                except Exception:
                    pass

                # Set as active screen buffer
                win32console.SetConsoleActiveScreenBuffer(handle)
            except Exception:
                pass

        def _cleanup_console(self):
            """
            Clean up Windows console resources
            """
            try:
                # Restore startup output as active buffer
                if self._is_valid_handle(self.cn[1]['handle']):  # startupOutput
                    win32console.SetConsoleActiveScreenBuffer(self.cn[1]['handle'])

                # Close owned handles
                for console in self.cn:
                    if console['owning'] and self._is_valid_handle(console['handle']):
                        try:
                            win32file.CloseHandle(console['handle'])
                        except Exception:
                            pass

                # Free console if we allocated it
                if self.owns_console:
                    win32console.FreeConsole()
            except Exception:
                pass

        def write(self, data: str) -> None:
            """
            Write to Windows console - mirrors C++ Windows version
            """
            try:
                if data and self.cn[2]['handle']:  # activeOutput
                    win32console.WriteConsoleA(self.cn[2]['handle'], data.encode('utf-8'))
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
                win32console.GetConsoleMode(handle)
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
            Get console size - mirrors C++ ConsoleCtl::getSize for Windows
            """
            try:
                sb_info = win32console.GetConsoleScreenBufferInfo(self.cn[2]['handle'])  # activeOutput
                window = sb_info['Window']
                return Point(
                    max(window.Right - window.Left + 1, 0),
                    max(window.Bottom - window.Top + 1, 0)
                )
            except Exception:
                return Point(0, 0)
        
        def get_font_size(self) -> Point:
            """
            Get console font size - mirrors C++ ConsoleCtl::getFontSize for Windows
            """
            try:
                font_info = win32console.GetCurrentConsoleFont(self.cn[2]['handle'], False)  # activeOutput
                return Point(
                    font_info['X'],
                    font_info['Y']
                )
            except Exception:
                return Point(0, 0)

    else:
        def _setup_console(self):
            """
            Set up Unix console file descriptors - mirrors C++ ConsoleCtl constructor for Unix
            """
            # Unix: file descriptors
            self.files: list[Optional[IO]] = [None, None]  # [input_file, output_file]
            self.fds: list[int] = [0, 1]  # [input_fd, output_fd]
            self.owns_files = False

            # Try to open /dev/tty if TVISION_USE_STDIO is not set
            if os.environ.get('TVISION_USE_STDIO') is not None:
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
            Get console size - mirrors C++ ConsoleCtl::getSize for Unix
            """

            for fd in self.fds:
                try:
                    # TIOCGWINSZ ioctl to get window size
                    result = fcntl.ioctl(fd, termios.TIOCGWINSZ, struct.pack('HHHH', 0, 0, 0, 0))
                    rows, cols, xpixel, ypixel = struct.unpack('HHHH', result)
                    # Check environment variables like C++ version
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
            Get console font size - mirrors C++ ConsoleCtl::getFontSize for Unix
            """
            import struct
            import termios
            
            # Try KDFONTOP ioctl first (Linux console)
            for fd in self.fds:
                try:
                    # This would need linux/kd.h constants, skip for now
                    pass
                except Exception:
                    pass
            
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
