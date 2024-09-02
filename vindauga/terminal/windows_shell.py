# -*- coding: utf-8 -*-
from dataclasses import dataclass
import io
import itertools
import logging
import os
import shlex
import time
from typing import BinaryIO

import msvcrt
import pywintypes
import win32api
import win32con
import win32pipe
import win32file
import win32process
import win32security

from vindauga.constants.message_flags import mfError, mfOKButton
from vindauga.dialogs.message_box import messageBox

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class WindowPipe:
    stdin: BinaryIO
    stdout: BinaryIO
    stderr: BinaryIO


counter = itertools.count(1)

# https://docs.microsoft.com/en-us/windows/desktop/procthread/creating-a-child-process-with-redirected-input-and-output


class WindowsShell:
    """
    Mostly works.. typed characters are not echoed back until CR is pressed.
    """
    BUFFER_SIZE = 128

    def __init__(self, cmdline):
        #self.cmdline = ' '.join(shlex.quote(c) for c in cmdline)
        self.cmdline = ' '.join(cmdline)
        self.hChildStdinWr = None
        self.hChildStdoutRd = None
        self.hChildStderrRd = None

        pid = os.getpid()
        self.stdoutPipeName = r'\\.\pipe\vindauga-stdout-%d-%d-%d' % (pid, next(counter), time.time())
        self.stderrPipeName = r'\\.\pipe\vindauga-stderr-%d-%d-%d' % (pid, next(counter), time.time())
        self.stdinPipeName = r'\\.\pipe\vindauga-stdin-%d-%d-%d' % (pid, next(counter), time.time())

    def __call__(self) -> WindowPipe:
        saAttr = win32security.SECURITY_ATTRIBUTES()
        saAttr.bInheritHandle = 1

        self.hChildStdoutRd = win32pipe.CreateNamedPipe(
            self.stdoutPipeName,
            win32con.PIPE_ACCESS_INBOUND | win32con.FILE_FLAG_OVERLAPPED,  # open mode
            win32con.PIPE_TYPE_BYTE,  # pipe mode
            1,  # max instances
            WindowsShell.BUFFER_SIZE,  # out buffer size
            WindowsShell.BUFFER_SIZE,  # in buffer size
            10,  # timeout
            saAttr)

        hChildStdoutWr = win32file.CreateFile(
            self.stdoutPipeName,
            win32con.GENERIC_WRITE,
            win32con.FILE_SHARE_READ | win32con.FILE_SHARE_WRITE,
            saAttr,
            win32con.OPEN_EXISTING,
            win32con.FILE_FLAG_OVERLAPPED,
            10)

        win32api.SetHandleInformation(self.hChildStdoutRd, win32con.HANDLE_FLAG_INHERIT, 0)

        self.hChildStderrRd = win32pipe.CreateNamedPipe(
            self.stderrPipeName,
            win32con.PIPE_ACCESS_INBOUND | win32con.FILE_FLAG_OVERLAPPED,  # open mode
            win32con.PIPE_TYPE_BYTE,  # pipe mode
            1,  # max instances
            WindowsShell.BUFFER_SIZE,  # out buffer size
            WindowsShell.BUFFER_SIZE,  # in buffer size
            10,  # timeout
            saAttr)

        hChildStderrWr = win32file.CreateFile(
            self.stderrPipeName,
            win32con.GENERIC_WRITE,
            win32con.FILE_SHARE_READ | win32con.FILE_SHARE_WRITE,
            saAttr,
            win32con.OPEN_EXISTING,
            win32con.FILE_FLAG_OVERLAPPED,
            10)

        win32api.SetHandleInformation(self.hChildStderrRd, win32con.HANDLE_FLAG_INHERIT, 0)

        # Create a pipe for the child process's STDIN. This one is opened
        # in duplex mode so we can read from it too in order to detect when
        # the child closes their end of the pipe.

        self.hChildStdinWr = win32pipe.CreateNamedPipe(
            self.stdinPipeName,
            win32con.PIPE_ACCESS_DUPLEX | win32con.FILE_FLAG_OVERLAPPED,  # open mode
            win32con.PIPE_TYPE_BYTE,  # pipe mode
            1,  # max instances
            WindowsShell.BUFFER_SIZE,  # out buffer size
            WindowsShell.BUFFER_SIZE,  # in buffer size
            10,  # timeout... 0 gives a default 50 ms
            saAttr)

        hChildStdinRd = win32file.CreateFile(
            self.stdinPipeName,
            win32con.GENERIC_READ,
            win32con.FILE_SHARE_READ | win32con.FILE_SHARE_WRITE,
            saAttr,
            win32con.OPEN_EXISTING,
            win32con.FILE_FLAG_OVERLAPPED | win32con.FILE_FLAG_NO_BUFFERING,
            10)

        win32api.SetHandleInformation(self.hChildStdinWr, win32con.HANDLE_FLAG_INHERIT, 0)

        # set the info structure for the new process.  This is where
        # we tell the process to use the pipes for stdout/err/in.
        StartupInfo = win32process.STARTUPINFO()
        StartupInfo.hStdOutput = hChildStdoutWr
        StartupInfo.hStdError = hChildStderrWr
        StartupInfo.hStdInput = hChildStdinRd
        StartupInfo.dwFlags = win32process.STARTF_USESTDHANDLES

        flags = win32process.CREATE_UNICODE_ENVIRONMENT

        try:
            processHandle, threadHandle, dwPid, dwTid = win32process.CreateProcess(
                None,  # name
                self.cmdline,  # command line
                None,  # process handle not inheritable
                None,  # thread handle not inheritable
                True,  # handles are inherited
                flags, # creation flags
                None,  # NULL, use parent environment
                None,  # current directory
                StartupInfo)  # STARTUPINFO pointer
        except pywintypes.error as e:
            logger.exception('%s\n%s\n', self.cmdline, e.strerror)
            messageBox(f'{self.cmdline}\n{e.strerror}', mfError, (mfOKButton,))
            return None

        win32file.CloseHandle(processHandle)
        win32file.CloseHandle(threadHandle)
        win32file.CloseHandle(hChildStderrWr)
        win32file.CloseHandle(hChildStdoutWr)
        win32file.CloseHandle(hChildStdinRd)

        self.stdin = io.open(msvcrt.open_osfhandle(int(self.hChildStdinWr), os.O_APPEND), 'wb', buffering=0)
        self.stdout = io.open(msvcrt.open_osfhandle(int(self.hChildStdoutRd), os.O_RDONLY), 'rb', buffering=0)
        self.stderr = io.open(msvcrt.open_osfhandle(int(self.hChildStderrRd), os.O_RDONLY), 'rb', buffering=0)

        fds = WindowPipe(stdin=self.stdin, stdout=self.stdout, stderr=self.stderr)
        return fds

    def write(self, buffer: bytes) -> int:
        """
        Write to the stdin pipe.

        :param buffer: encoded bytes buffer. Normally utf-8
        :return: # bytes written
        """
        error, written = win32file.WriteFile(self.hChildStdinWr, buffer)
        if error:
            logger.error('write() Error: -> %s', win32api.GetLastError())
        return written

    @staticmethod
    def __readPipe(handle) -> bytes:
        try:
            (buffer, available, result) = win32pipe.PeekNamedPipe(handle, 1)
        except pywintypes.error as e:
            raise BrokenPipeError

        if result == -1 and (lastError := win32api.GetLastError()):
             raise BrokenPipeError

        if available > 0:
            result, data = win32file.ReadFile(handle, available, None)
            if result < 0:
                raise BrokenPipeError
            return data

    def __readStderr(self) -> bytes:
        return self.__readPipe(self.hChildStderrRd)

    def __readStdout(self) -> bytes:
        return self.__readPipe(self.hChildStdoutRd)

    def read(self) -> bytes:
        data = self.__readStderr()
        if data:
            return data
        return self.__readStdout()
