# -*- coding:utf-8 -*-
from typing import Any

from vindauga.constants.command_codes import wnNoNumber, wpCyanWindow
from vindauga.constants.scrollbar_codes import sbHorizontal, sbVertical, sbHandleKeyboard
from vindauga.constants.drag_flags import dmLimitAll
from vindauga.constants.event_codes import evBroadcast
from vindauga.events.event import Event
from vindauga.utilities.message import message
from vindauga.types.palette import Palette
from vindauga.types.rect import Rect

from .message_list_viewer import MessageListViewer
from .program import Program
from .window import Window


cmFindMsgBox = 0x1000
cmInsMsgBox = 0x1001
cmFindInfoBox = 0x1002
cmInsInfoBox = 0x1003


class MessageWindow(Window):
    cpMessageWindow = '\x10\x11\x12\x13\x14\x15\x16\x17\x39\x3A\x3B\x3C\x3D'

    def __init__(self, bounds: Rect):
        super().__init__(bounds, 'Messages', wnNoNumber)
        self.dragMode = dmLimitAll
        self.palette = wpCyanWindow

        vBar = self.standardScrollBar(sbVertical | sbHandleKeyboard)
        hBar = self.standardScrollBar(sbHorizontal | sbHandleKeyboard)

        r = self.getExtent()
        r.topLeft.x = 1
        r.topLeft.y = 1
        r.bottomRight.x -= 1
        r.bottomRight.y -= 1
        self.msgViewer = MessageListViewer(r, 1, hBar, vBar)
        self.insert(self.msgViewer)

    def handleEvent(self, event: Event):
        super().handleEvent(event)
        if event.what == evBroadcast:
            emc = event.message.command
            if emc == cmFindMsgBox:
                self.clearEvent(event)
            elif emc == cmInsMsgBox:
                self.msgViewer.insert(event.message.infoPtr)
                self.clearEvent(event)
                self.drawView()

    def getPalette(self) -> Palette:
        return Palette(self.cpMessageWindow)


def postMessage(messageData: Any):
    # Send a message to the desktop to find the log window
    wPtr = message(Program.desktop, evBroadcast, cmFindMsgBox, None)
    if not wPtr:
        # There isn't one, so make one
        r = Program.desktop.getExtent()
        r.topLeft.y = r.bottomRight.y - 6
        wPtr = MessageWindow(r)
        Program.desktop.insert(wPtr)
        Program.desktop.drawView()

    message(wPtr, evBroadcast, cmInsMsgBox, str(messageData))
