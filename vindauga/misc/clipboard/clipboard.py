# -*- coding: utf-8 -*-
import sys


if sys.platform == 'cygwin':
    import subprocess

    class Clipboard:

        @staticmethod
        def sendToClipboard(data):
            subprocess.Popen(['clip'], stdin=subprocess.PIPE).communicate(data)

        @staticmethod
        def receiveFromClipboard():
            return open('/dev/clipboard', 'rb').read()

elif sys.platform == 'darwin':
    import pasteboard

    class Clipboard:

        @staticmethod
        def sendToClipboard(data):
            pb = pasteboard.Pasteboard()
            pb.set_contents(data)

        @staticmethod
        def receiveFromClipboard():
            pb = pasteboard.Pasteboard()
            return pb.get_contents(type=pasteboard.String)

else:  # windows
    from contextlib import contextmanager
    import ctypes

    class Clipboard:
        """
        Simple Text clipboard actions
        """

        strcpy = ctypes.cdll.msvcrt.strcpy
        OpenClipboard = ctypes.windll.user32.OpenClipboard
        EmptyClipboard = ctypes.windll.user32.EmptyClipboard
        GetClipboardData = ctypes.windll.user32.GetClipboardData
        SetClipboardData = ctypes.windll.user32.SetClipboardData
        CloseClipboard = ctypes.windll.user32.CloseClipboard
        GlobalAlloc = ctypes.windll.kernel32.GlobalAlloc
        GlobalLock = ctypes.windll.kernel32.GlobalLock  # Global Memory Locking
        GlobalUnlock = ctypes.windll.kernel32.GlobalUnlock
        GMEM_DDESHARE = 0x2000

        @contextmanager
        def openClipboard(self):
            """
            Open and close the clipboard as needed
            """
            self.OpenClipboard(None)
            yield
            self.CloseClipboard()

        def receiveFromClipboard(self):
            """
            Get the data in the clipboard

            :returns: string
            """
            with self.openClipboard():
                pContents = self.GetClipboardData(1)
                data = ctypes.c_char_p(pContents).value
                return data

        def sendToClipboard(self, data):
            """
            Put a string on the clipboard

            :param data: A string
            """
            with self.openClipboard():
                self.EmptyClipboard()
                data = data.encode("utf-8")
                handle = self.GlobalAlloc(self.GMEM_DDESHARE, len(data) + 1)
                lockedData = self.GlobalLock(handle)
                self.strcpy(ctypes.c_char_p(lockedData), data)
                self.GlobalUnlock(handle)
                self.SetClipboardData(1, handle)


if __name__ == "__main__":
    clipboard = Clipboard()
    print(clipboard.receiveFromClipboard())
    clipboard.sendToClipboard(b'Meh')
