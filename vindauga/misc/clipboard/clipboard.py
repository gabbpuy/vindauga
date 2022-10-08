# -*- coding: utf-8 -*-
import pyperclip


class Clipboard:
    @staticmethod
    def sendToClipboard(data):
        pyperclip.copy(data)

    @staticmethod
    def receiveFromClipboard():
        return pyperclip.paste()


if __name__ == "__main__":
    clipboard = Clipboard()
    print(clipboard.receiveFromClipboard())
    clipboard.sendToClipboard(b'Meh')
