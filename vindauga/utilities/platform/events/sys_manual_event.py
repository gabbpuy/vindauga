# -*- coding: utf-8 -*-
import logging
import platform

if platform.system().lower() == 'windows':
    from pywintypes import HANDLE
    from win32api import CloseHandle
    from win32event import CreateEvent, SetEvent, ResetEvent

    Handle = HANDLE
    SysHandle = HANDLE
else:
    try:
        from fcntl import fcntl, F_SETFD, FD_CLOEXEC
    except ImportError:
        # fcntl not available, create fallbacks
        fcntl = None
        F_SETFD = None
        FD_CLOEXEC = None
    from os import close, pipe, read, write

    Handle = tuple[int, int]
    SysHandle = int

logger = logging.getLogger(__file__)


class SysManualEvent:
    if platform.system().lower() == 'windows':

        @staticmethod
        def create_handle() -> Handle:
            return CreateEvent(None, True, False, None)

        def __del__(self):
            CloseHandle(self.h_event)

        def signal(self):
            logger.info('Windows %s.signal()', self)
            SetEvent(self.h_event)

        def clear(self):
            ResetEvent(self.h_event)

    else:

        @staticmethod
        def create_handle() -> Handle:
            fds = pipe()
            for fd in fds:
                try:
                    fcntl(fd, F_SETFD, FD_CLOEXEC)
                except (OSError, AttributeError):
                    break  # fcntl failed, but we can continue
            return fds

        def __del__(self):
            for fd in self.fds:
                close(fd)

        def signal(self):
            logger.info('"posix" %s.signal()', self)
            c = b'\x00'
            while write(self.fds[1], c) != 1:
                pass

        def clear(self):
            while len(read(self.fds[0], 1)) != 1:
                pass

    def __init__(self, handle: Handle = None):
        self.h_event = None
        self.fds = []
        if handle is not None:
            if platform.system().lower() == 'windows':
                self.h_event = handle
            else:
                self.fds = handle[0], handle[1]

    @staticmethod
    def get_waitable_handle(handle: Handle) -> SysHandle:
        if platform.system().lower() == 'windows':
            return handle
        return handle[0]
