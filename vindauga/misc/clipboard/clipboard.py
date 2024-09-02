# -*- coding: utf-8 -*-
import pyperclip


class Clipboard:
    @staticmethod
    def sendToClipboard(data):
        pyperclip.copy(data)

    @staticmethod
    def receiveFromClipboard():
        return pyperclip.paste()
