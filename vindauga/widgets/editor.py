# -*- coding: utf-8 -*-
from __future__ import annotations
import logging
import string
from typing import List, Optional, Union, Tuple

import wcwidth

from vindauga.constants.command_codes import *
from vindauga.constants.edit_command_codes import *
from vindauga.constants.event_codes import *
from vindauga.constants.grow_flags import gfGrowHiX, gfGrowHiY
from vindauga.constants.keys import *
from vindauga.constants.option_flags import ofSelectable
from vindauga.constants.state_flags import sfVisible, sfCursorIns, sfActive, sfExposed
from vindauga.events.event import Event
from vindauga.types.records.find_dialog_record import FindDialogRecord
from vindauga.types.command_set import CommandSet
from vindauga.types.palette import Palette
from vindauga.types.point import Point
from vindauga.types.draw_buffer import BufferArray, DrawBuffer
from vindauga.types.rect import Rect
from vindauga.types.view import View
from vindauga.widgets.indicator import Indicator
from vindauga.widgets.scroll_bar import ScrollBar

logger = logging.getLogger(__name__)

firstKeys = {
    kbCtrlA: cmWordLeft,
    kbCtrlC: cmPageDown,
    kbCtrlD: cmCharRight,
    kbCtrlE: cmLineUp,
    kbCtrlF: cmWordRight,
    kbCtrlG: cmDelChar,
    kbCtrlH: cmBackSpace,
    kbCtrlK: 0xFF02,
    kbCtrlL: cmSearchAgain,
    kbCtrlM: cmNewLine,
    kbEnter: cmNewLine,
    kbCtrlO: cmIndentMode,
    kbCtrlQ: 0xFF01,
    kbCtrlR: cmPageUp,
    kbCtrlS: cmCharLeft,
    kbCtrlT: cmDelWord,
    kbCtrlU: cmUndo,
    kbCtrlV: cmInsMode,
    kbCtrlX: cmLineDown,
    kbCtrlY: cmDelLine,
    kbLeft: cmCharLeft,
    kbRight: cmCharRight,
    kbCtrlLeft: cmWordLeft,
    kbCtrlRight: cmWordRight,
    kbHome: cmLineStart,
    kbEnd: cmLineEnd,
    kbUp: cmLineUp,
    kbDown: cmLineDown,
    kbPgUp: cmPageUp,
    kbPgDn: cmPageDown,
    kbCtrlPgUp: cmTextStart,
    kbCtrlPgDn: cmTextEnd,
    kbIns: cmInsMode,
    kbDel: cmDelChar,
    kbShiftIns: cmPaste,
    kbShiftDel: cmCut,
    kbCtrlIns: cmCopy,
    kbCtrlDel: cmClear,
}

quickKeys = {
    'A': cmReplace,
    'C': cmTextEnd,
    'D': cmLineEnd,
    'F': cmFind,
    'H': cmDelStart,
    'R': cmTextStart,
    'S': cmLineStart,
    'Y': cmDelEnd,
}

blockKeys = {
    'B': cmStartSelect,
    'C': cmPaste,
    'H': cmHideSelect,
    'K': cmCopy,
    'Y': cmCut,
}

keyMaps = (firstKeys, quickKeys, blockKeys)


def isWordChar(ch: str) -> bool:
    return ch in string.ascii_letters or ch in string.digits or ch == ' '


def scanKeyMap(keyMap: dict, keyCode: Union[int, str]) -> int:
    if isinstance(keyCode, str):
        keyCode = ord(keyCode)
    codeHi, codeLow = divmod(keyCode, 256)

    for _map, command in keyMap.items():
        if isinstance(_map, str):
            _map = ord(_map)
        mapHi, mapLow = divmod(_map, 256)
        if (mapLow == codeLow) and ((mapHi == 0) or (mapHi == codeHi)):
            return command
    return 0


class Editor(View):
    name = 'Editor'
    cpEditor = "\x06\x07"
    clipboard = None

    def __init__(self, bounds: Rect, hScrollBar: ScrollBar, vScrollBar: ScrollBar, indicator: Optional[Indicator],
                 bufSize: int):
        super().__init__(bounds)

        self.delta = Point(0, 0)
        self.limit = Point(0, 0)
        self._currentPosition = Point(0, 0)
        self.hScrollBar = hScrollBar
        self.vScrollBar = vScrollBar
        self.indicator = indicator

        self.bufLen = 0
        self.canUndo = True
        self.selecting = False
        self.overwrite = False
        self.autoIndent = False
        self.modified = False

        self.gapLen = 0
        self.selStart = 0
        self.selEnd = 0
        self.curPtr = 0
        self.delCount = 0
        self.insCount = 0
        self.updateFlags = 0
        self.drawPtr = 0
        self.drawLine = 0
        self.lockCount = 0
        self.keyState = 0
        self.editorFlags = efBackupFiles | efPromptOnReplace
        self.tabSize = 8

        self.findStr = ''
        self.replaceStr = ''
        self.buffer = None

        self.growMode = gfGrowHiX | gfGrowHiY

        self.options |= ofSelectable
        self.eventMask = evMouseDown | evKeyDown | evCommand | evBroadcast

        self.showCursor()
        self.initBuffer(bufSize)
        self.isValid = True
        self.setBufLen(0)

    @staticmethod
    def editorDialog(_flag, *_args) -> int:
        logger.info('Unreplaced editorDialog')
        return cmCancel

    def bufChar(self, pos: int) -> str:
        o = 0
        if pos > self.curPtr:
            o = self.gapLen
        return chr(self.buffer[pos + o])

    def bufPtr(self, pos: int) -> int:
        if pos >= self.curPtr:
            return pos + self.gapLen
        return pos

    def shutdown(self):
        self.doneBuffer()
        super().shutdown()

    def changeBounds(self, bounds: Rect):
        self.setBounds(bounds)
        self.delta.x = max(0, min(self.delta.x, self.limit.x - self.size.x))
        self.delta.y = max(0, min(self.delta.y, self.limit.y - self.size.y))
        self.update(ufView)

    def charPos(self, p: int, target: int) -> int:
        pos = 0
        while p < target:
            if self.bufChar(p) == '\x09':
                pos += (self.tabSize - (pos % self.tabSize) - 1)

            pos += 1
            p += 1
        return pos

    def charPtr(self, p: int, target: int):
        pos = 0

        while pos < target and p < self.bufLen and self.bufChar(p) not in ('\n', '\r'):
            if self.bufChar(p) == '\x09':
                pos += (self.tabSize - (pos % self.tabSize) - 1)

            pos += 1
            p += 1

        if pos > target:
            p -= 1
        return p

    def clipCopy(self) -> bool:
        res = False
        if Editor.clipboard and Editor.clipboard is not self:
            res = Editor.clipboard.insertFrom(self)
            self.selecting = False
            self.update(ufUpdate)
        return res

    def clipCut(self):
        if self.clipCopy():
            self.deleteSelect()

    def clipPaste(self):
        if Editor.clipboard and Editor.clipboard is not self:
            self.insertFrom(Editor.clipboard)

    def convertEvent(self, event: Event):
        if event.what == evKeyDown:
            key = event.keyDown.keyCode
            if self.keyState:
                if kbCtrlA <= key <= kbCtrlZ:
                    key -= 0x40
                if ord('a') <= key <= ord('z'):
                    key -= 0x20

            key = scanKeyMap(keyMaps[self.keyState], key)
            self.keyState = 0
            if key:
                if key & 0xFF00 == 0xFF00:
                    self.keyState = (key & 0xFF)
                    self.clearEvent(event)
                else:
                    event.what = evCommand
                    event.message.command = key

    def isCursorVisible(self) -> bool:
        return self.delta.y <= self._currentPosition.y < (self.delta.y + self.size.y)

    def deleteRange(self, startPtr: int, endPtr: int, delSelect: bool):
        if self.hasSelection() and delSelect:
            self.deleteSelect()
        else:
            self.setSelect(self.curPtr, endPtr, True)
            self.deleteSelect()
            self.setSelect(startPtr, self.curPtr, False)
            self.deleteSelect()

    def deleteSelect(self):
        self.insertText('', 0, False)

    def doneBuffer(self):
        del self.buffer

    def doSearchReplace(self):
        done = False
        while not done:
            i = cmCancel
            if not self.search(self.findStr, self.editorFlags):
                if self.editorFlags & (efReplaceAll | efDoReplace) != (efReplaceAll | efDoReplace):
                    Editor.editorDialog(edSearchFailed)
            elif self.editorFlags & efDoReplace:
                i = cmYes

                if self.editorFlags & efPromptOnReplace:
                    c = self.makeGlobal(self._currentPosition)
                    i = Editor.editorDialog(edReplacePrompt, c)
                if i == cmYes:
                    self.lock()
                    try:
                        self.insertText(self.replaceStr, wcwidth.wcswidth(self.replaceStr), False)
                        self.trackCursor(False)
                    finally:
                        self.unlock()
            done = not (i != cmCancel and (self.editorFlags & efReplaceAll))

    def doUpdate(self):
        if self.updateFlags:
            self.setCursor(self._currentPosition.x - self.delta.x, self._currentPosition.y - self.delta.y)
            if self.updateFlags & ufView:
                self.drawView()
            elif self.updateFlags & ufLine:
                self.drawLines(self._currentPosition.y - self.delta.y, 1, self.lineStart(self.curPtr))

            if self.hScrollBar:
                self.hScrollBar.setParams(self.delta.x, 0,
                                          self.limit.x - self.size.x,
                                          self.size.x // 2, 1)

            if self.vScrollBar:
                self.vScrollBar.setParams(self.delta.y, 0,
                                          self.limit.y - self.size.y,
                                          self.size.y - 1, 1)

            if self.indicator:
                self.indicator.setValue(self._currentPosition, self.modified)

            if self.state & sfActive:
                self.updateCommands()
            self.updateFlags = 0

    def draw(self):
        if self.drawLine != self.delta.y:
            self.drawPtr = self.lineMove(self.drawPtr, self.delta.y - self.drawLine)
            self.drawLine = self.delta.y

        self.drawLines(0, self.size.y, self.drawPtr)

    def drawLines(self, y: int, count: int, linePtr: int):
        color = self.getColor(0x0201)

        for line in range(y, y + count):
            b = DrawBuffer(True)
            self.formatLine(b, linePtr, self.delta.x + self.size.x, color)
            self.writeBuf(0, line, self.size.x, 1, b[self.delta.x:])
            linePtr = self.nextLine(linePtr)

    def find(self):
        result, data = Editor.editorDialog(edFind, (self.editorFlags, self.findStr))
        if result != cmCancel:
            self.findStr = data[1].value
            self.editorFlags = data[0].value & ~efDoReplace
            self.doSearchReplace()

    def getMousePtr(self, m: Point) -> int:
        mouse = self.makeLocal(m)

        mouse.x = max(0, min(mouse.x, self.size.x - 1))
        mouse.y = max(0, min(mouse.y, self.size.y - 1))

        return self.charPtr(self.lineMove(self.drawPtr,
                                          mouse.y + self.delta.y - self.drawLine),
                            mouse.x + self.delta.x)

    def getPalette(self) -> Palette:
        palette = Palette(self.cpEditor)
        return palette

    def checkScrollBar(self, event: Event, scrollBar: ScrollBar, value: int) -> int:
        if event.message.infoPtr == scrollBar and scrollBar.value != value:
            value = scrollBar.value
            self.update(ufView)
        return value

    def handleEvent(self, event: Event):
        super().handleEvent(event)
        self.convertEvent(event)

        centerCursor = not self.isCursorVisible()
        selectMode = 0

        if (self.selecting or
                (event.what & evMouse and (event.mouse.controlKeyState & kbShift)) or
                (event.what & evKeyboard and (event.keyDown.controlKeyState & kbShift))):
            selectMode = smExtend

        what = event.what

        if what == evMouseDown:
            self._handleMouseEvent(event, selectMode)
        elif what == evKeyDown:
            if (event.keyDown.charScan.charCode == '\x09') or ('\x20' <= event.keyDown.charScan.charCode < '\xFF'):
                self._handleKeyDownEvent(centerCursor, event)
            else:
                return
        elif what == evCommand:
            c = event.message.command
            if c == cmFind:
                self.find()
            elif c == cmReplace:
                self.replace()
            elif c == cmSearchAgain:
                self.doSearchReplace()
            elif c in {
                    cmCut, cmCopy, cmPaste, cmUndo, cmClear, cmCharLeft, cmCharRight, cmWordLeft, cmWordRight,
                    cmLineStart, cmLineEnd, cmLineUp, cmLineDown, cmPageUp, cmPageDown, cmTextStart, cmTextEnd,
                    cmNewLine, cmBackSpace, cmDelChar, cmDelWord, cmDelStart, cmDelEnd, cmDelLine, cmInsMode,
                    cmStartSelect, cmHideSelect, cmIndentMode}:
                self._handleEditorCommand(c, centerCursor, selectMode)
            else:
                return
        elif what == evBroadcast:
            c = event.message.command
            if c == cmScrollBarChanged:
                if event.message.infoPtr in (self.hScrollBar, self.vScrollBar):
                    self.delta.x = self.checkScrollBar(event, self.hScrollBar, self.delta.x)
                    self.delta.y = self.checkScrollBar(event, self.vScrollBar, self.delta.y)
                else:
                    return
        else:
            return

        self.clearEvent(event)

    def hasSelection(self) -> bool:
        return self.selStart != self.selEnd

    def hideSelect(self):
        self.selecting = False
        self.setSelect(self.curPtr, self.curPtr, False)

    def initBuffer(self, bufSize: int):
        self.buffer = BufferArray([0] * bufSize)

    def countLines(self, start: int, count: int) -> int:
        return self.buffer[start:start + count].count(ord('\n'))

    @staticmethod
    def scan(buffer: BufferArray, size: int, pattern: str) -> int:
        result = ''.join(chr(c) for c in buffer[:size]).find(pattern)
        if result < 0:
            return sfSearchFailed
        return result

    @staticmethod
    def iScan(buffer: BufferArray, size: int, pattern: str) -> int:
        result = ''.join(chr(c) for c in buffer[:size]).lower().find(pattern.lower())
        if result < 0:
            return sfSearchFailed
        return result

    def insertBuffer(self, p: List[int], offset: int, length: int, allowUndo: bool, selectText: bool) -> bool:
        self.selecting = False
        selLen = self.selEnd - self.selStart

        if selLen == 0 and length == 0:
            return True

        delLen = 0
        if allowUndo:
            if self.curPtr == self.selStart:
                delLen = selLen
            elif selLen > self.insCount:
                delLen = selLen - self.insCount

        newSize = self.bufLen + self.delCount - selLen + delLen + length
        if newSize > self.bufLen + self.delCount:
            self.setBufSize(newSize)

        selLines = self.countLines(self.bufPtr(self.selStart), selLen)

        if self.curPtr == self.selEnd:
            if allowUndo:
                if delLen > 0:
                    o = self.curPtr + self.gapLen - self.delCount - delLen
                    self.memmove(o, self.selStart, delLen)

                self.insCount -= selLen - delLen

            self.curPtr = self.selStart
            self._currentPosition.y -= selLines

        if self.delta.y > self._currentPosition.y:
            self.delta.y -= selLines
            if self.delta.y < self._currentPosition.y:
                self.delta.y = self._currentPosition.y

        if length > 0:
            self.buffer[self.curPtr:self.curPtr + length] = BufferArray(p[offset:offset + length])

        lines = self.countLines(self.curPtr, length)
        self.curPtr += length
        self._currentPosition.y += lines

        self.drawLine = self._currentPosition.y
        self.drawPtr = self.lineStart(self.curPtr)
        self._currentPosition.x = self.charPos(self.drawPtr, self.curPtr)

        if not selectText:
            self.selStart = self.curPtr

        self.selEnd = self.curPtr

        self.bufLen += length - selLen
        self.gapLen -= length - selLen

        if allowUndo:
            self.delCount += delLen
            self.insCount += length

        self.limit.y += (lines - selLines)
        self.delta.y = max(0, min(self.delta.y, self.limit.y - self.size.y))

        if not self.isClipboard():
            self.modified = True

        self.setBufSize(self.bufLen + self.delCount)

        if not (selLines or lines):
            self.update(ufLine)
        else:
            self.update(ufView)
        return True

    def insertFrom(self, editor: Editor):
        pt = editor.bufPtr(editor.selStart)

        return self.insertBuffer(editor.buffer,
                                 pt, editor.selEnd - editor.selStart,
                                 self.canUndo, self.isClipboard())

    def insertText(self, text: str, length: int, selectText: bool) -> bool:
        return self.insertBuffer([ord(c) for c in text], 0, length, self.canUndo, selectText)

    def isClipboard(self) -> bool:
        return Editor.clipboard is self

    def lineMove(self, p: int, count: int) -> int:
        i = p
        p = self.lineStart(p)
        pos = self.charPos(p, i)
        while count != 0:
            i = p
            if count < 0:
                p = self.prevLine(p)
                count += 1
            else:
                p = self.nextLine(p)
                count -= 1

        if p != i:
            p = self.charPtr(p, pos)
        return p

    def lock(self):
        self.lockCount += 1

    def newLine(self):
        nl = '\n'
        self.insertText(nl, len(nl), False)

        if self.autoIndent:
            p = self.lineStart(self.curPtr)
            i = p
            while i < self.curPtr and chr(self.buffer[i]) in (' ', '\t'):
                i += 1
            self.insertText(self.buffer[p:], i - p, False)

    def nextLine(self, pos: int) -> int:
        return self.nextChar(self.lineEnd(pos))

    def nextWord(self, pos: int) -> int:
        while pos < self.bufLen and isWordChar(self.bufChar(pos)):
            pos = self.nextChar(pos)
        while pos < self.bufLen and not isWordChar(self.bufChar(pos)):
            pos = self.nextChar(pos)

        return pos

    def prevLine(self, pos: int) -> int:
        return self.lineStart(self.prevChar(pos))

    def prevWord(self, pos: int) -> int:
        while pos > 0 and not isWordChar(self.bufChar(self.prevChar(pos))):
            pos = self.prevChar(pos)
        while pos > 0 and isWordChar(self.bufChar(self.prevChar(pos))):
            pos = self.prevChar(pos)
        return pos

    def replace(self):
        replaceRec = (self.editorFlags, self.replaceStr, self.findStr)
        result, data = Editor.editorDialog(edReplace, replaceRec)

        if result != cmCancel:
            self.findStr = data[2].value
            self.replaceStr = data[1].value
            self.editorFlags = data[0].value | efDoReplace
            self.doSearchReplace()

    def scrollTo(self, x: int, y: int):
        x = max(0, min(x, self.limit.x - self.size.x))
        y = max(0, min(y, self.limit.y - self.size.y))
        if x != self.delta.x or y != self.delta.y:
            self.delta.x = x
            self.delta.y = y
            self.update(ufView)

    def search(self, findStr: str, opts: int):
        pos = self.curPtr
        done = False

        while not done:
            if opts & efCaseSensitive != 0:
                i = self.scan(self.buffer[self.bufPtr(pos):],
                              self.bufLen - pos, self.findStr)
            else:
                i = self.iScan(self.buffer[self.bufPtr(pos):],
                               self.bufLen - pos, self.findStr)

            if i != sfSearchFailed:
                i += pos

                if (opts & efWholeWordsOnly == 0 or
                        not (i != 0 and isWordChar(self.bufChar(i - 1)) or
                             (i + len(findStr) != self.bufLen and
                              isWordChar(self.bufChar(i + len(findStr)))))):
                    self.lock()
                    try:
                        self.setSelect(i, i + len(findStr), False)
                        self.trackCursor(not self.isCursorVisible())
                    finally:
                        self.unlock()
                    return True
                else:
                    pos = i + 1

            done = (i == sfSearchFailed)

        return False

    def setBufLen(self, length: int):
        self.bufLen = length
        self.gapLen = self.bufSize - length
        self.selStart = 0
        self.selEnd = 0
        self.curPtr = 0
        self.delta.x = 0
        self.delta.y = 0
        self._currentPosition.x = 0
        self._currentPosition.y = 0
        self.limit.x = maxLineLength
        self.limit.y = self.countLines(self.gapLen, self.bufLen) + 1
        self.drawLine = 0
        self.drawPtr = 0
        self.delCount = 0
        self.insCount = 0
        self.modified = False
        self.update(ufView)

    def setCmdState(self, command: int, enable: bool):
        s = CommandSet()

        s += command
        if enable and (self.state & sfActive):
            self.enableCommands(s)
        else:
            self.disableCommands(s)

    def setCurPtr(self, pos: int, selectMode: int):
        if not selectMode & smExtend:
            anchor = pos
        elif self.curPtr == self.selStart:
            anchor = self.selEnd
        else:
            anchor = self.selStart

        if pos < anchor:
            if selectMode & smDouble:
                pos = self.prevLine(self.nextLine(pos))
                anchor = self.nextLine(self.prevLine(anchor))
            self.setSelect(pos, anchor, True)
        else:
            if selectMode & smDouble:
                pos = self.nextLine(pos)
                anchor = self.prevLine(self.nextLine(anchor))
            self.setSelect(anchor, pos, False)

    def memmove(self, destination: int, source: int, length: int):
        blob = self.buffer[source: source + length]
        self.buffer[destination: destination + length] = blob

    def setSelect(self, newStart: int, newEnd: int, curStart: bool):
        if curStart:
            pos = newStart
        else:
            pos = newEnd

        flags = ufUpdate

        if newStart != self.selStart or newEnd != self.selEnd:
            if newStart != newEnd or self.selStart != self.selEnd:
                flags = ufView

        if pos != self.curPtr:
            if pos > self.curPtr:
                length = pos - self.curPtr
                self.memmove(self.curPtr, self.curPtr + self.gapLen, length)
                self._currentPosition.y += self.countLines(self.curPtr, length)
                self.curPtr = pos
            else:
                length = self.curPtr - pos
                self.curPtr = pos
                self._currentPosition.y -= self.countLines(self.curPtr, length)
                self.memmove(self.curPtr + self.gapLen, self.curPtr, length)

            self.drawLine = self._currentPosition.y
            self.drawPtr = self.lineStart(pos)
            self._currentPosition.x = self.charPos(self.drawPtr, pos)
            self.delCount = 0
            self.insCount = 0
            self.setBufSize(self.bufLen)
        self.selStart = newStart
        self.selEnd = newEnd
        self.update(flags)

    def setState(self, state: int, enable: bool):
        super().setState(state, enable)

        if state == sfActive:
            if self.hScrollBar:
                self.hScrollBar.setState(sfVisible, enable)
            if self.vScrollBar:
                self.vScrollBar.setState(sfVisible, enable)
            if self.indicator:
                self.indicator.setState(sfVisible, enable)
            self.updateCommands()
        elif state == sfExposed:
            if enable:
                self.unlock()

    def startSelect(self):
        self.hideSelect()
        self.selecting = True

    def toggleInsMode(self):
        self.overwrite = not self.overwrite
        self.setState(sfCursorIns, not self.getState(sfCursorIns))

    def trackCursor(self, center: bool):
        if center:
            self.scrollTo(self._currentPosition.x - self.size.x + 1,
                          self._currentPosition.y - self.size.y // 2)
        else:
            self.scrollTo(max(self._currentPosition.x - self.size.x + 1, min(self.delta.x, self._currentPosition.x)),
                          max(self._currentPosition.y - self.size.y + 1, min(self.delta.y, self._currentPosition.y)))

    def undo(self):
        if self.delCount or self.insCount:
            self.selStart = self.curPtr - self.insCount
            self.selEnd = self.curPtr
            length = self.delCount
            self.delCount = 0
            self.insCount = 0
            self.insertBuffer(self.buffer, self.curPtr + self.gapLen - length,
                              length, False, True)

    def unlock(self):
        if self.lockCount > 0:
            self.lockCount -= 1
            if not self.lockCount:
                self.doUpdate()

    def update(self, flags: int):
        self.updateFlags |= flags
        if not self.lockCount:
            self.doUpdate()

    def updateCommands(self):
        self.setCmdState(cmUndo, (self.delCount != 0 or self.insCount != 0))

        if not self.isClipboard():
            self.setCmdState(cmCut, self.hasSelection())
            self.setCmdState(cmCopy, self.hasSelection())
            self.setCmdState(cmPaste,
                             Editor.clipboard and (Editor.clipboard.hasSelection()))

        self.setCmdState(cmClear, self.hasSelection())
        self.setCmdState(cmFind, True)
        self.setCmdState(cmReplace, True)
        self.setCmdState(cmSearchAgain, True)

    def valid(self, *_args) -> bool:
        return self.isValid

    def lineStart(self, pos: int) -> int:
        while pos > self.curPtr:
            pos -= 1
            if self.buffer[pos + self.gapLen] == ord('\n'):
                return pos + 1
        if self.curPtr == 0:
            return 0

        while pos > 0:
            pos -= 1
            if self.buffer[pos] == ord('\n'):
                return pos + 1
        return 0

    def lineEnd(self, pos: int) -> int:
        if pos < self.curPtr:
            while pos < self.curPtr:
                if self.buffer[pos] == ord('\n'):
                    return pos
                pos += 1
            if self.curPtr == self.bufLen:
                return self.bufLen
        elif pos == self.bufLen:
            return self.bufLen

        while pos + self.gapLen < self.bufSize:
            if self.buffer[pos + self.gapLen] == ord('\n'):
                return pos
            pos += 1
        return pos

    def formatLine(self, drawBuf: DrawBuffer, linePtr: int, width: int, color: int):
        i = 0
        pos = linePtr  # Buffer

        while pos < self.curPtr and self.buffer[pos] != ord('\n') and i <= width:
            i, pos = self.__highlight(color, drawBuf, i, pos, width)

        if pos >= self.curPtr:
            pos += self.gapLen
            while (pos < self.bufSize) and self.buffer[pos] != ord('\n') and i <= width:
                i, pos = self.__highlight(color, drawBuf, i, pos, width)

        for j in range(i, width):
            if self.selStart <= pos < self.selEnd:
                curColor = ((color & 0xFF00) >> 8) << DrawBuffer.CHAR_WIDTH
            else:
                curColor = (color & 0xFF) << DrawBuffer.CHAR_WIDTH
            drawBuf[j] = 0x20 | curColor

    def nextChar(self, pos: int) -> int:
        if pos == self.bufLen:
            return pos
        return pos + 1

    @staticmethod
    def prevChar(pos: int):
        if not pos:
            return pos
        return pos - 1

    def setBufSize(self, newSize: int):
        if newSize < 0x1000:
            # At least a 4K buffer
            newSize = 0x1000
        elif newSize > self.bufSize and (newSize - self.bufSize) < 128:
            # extend in 128 byte blocks
            newSize = self.bufSize + 128

        if newSize > self.bufSize:
            temp = self.buffer
            nn = min(newSize, self.bufSize)
            self.buffer = BufferArray(temp[:nn])
            self.buffer.extend([0] * (newSize - nn))
            n = self.bufLen - self.curPtr + self.delCount
            self.buffer[newSize - n: newSize] = temp[self.bufSize - n: self.bufSize]
            self.gapLen = self.bufSize - self.bufLen
        return True

    @property
    def bufSize(self) -> int:
        return len(self.buffer)

    def _handleEditorCommand(self, command: int, centerCursor: bool, selectMode: int):
        self.lock()
        try:
            if command == cmCut:
                self.clipCut()
            elif command == cmCopy:
                self.clipCopy()
            elif command == cmPaste:
                self.clipPaste()
            elif command == cmUndo:
                self.undo()
            elif command == cmClear:
                self.deleteSelect()
            elif command == cmCharLeft:
                self.setCurPtr(self.prevChar(self.curPtr), selectMode)
            elif command == cmCharRight:
                self.setCurPtr(self.nextChar(self.curPtr), selectMode)
            elif command == cmWordLeft:
                self.setCurPtr(self.prevWord(self.curPtr), selectMode)
            elif command == cmWordRight:
                self.setCurPtr(self.nextWord(self.curPtr), selectMode)
            elif command == cmLineStart:
                self.setCurPtr(self.lineStart(self.curPtr), selectMode)
            elif command == cmLineEnd:
                self.setCurPtr(self.lineEnd(self.curPtr), selectMode)
            elif command == cmLineUp:
                self.setCurPtr(self.lineMove(self.curPtr, -1), selectMode)
            elif command == cmLineDown:
                self.setCurPtr(self.lineMove(self.curPtr, 1), selectMode)
            elif command == cmPageUp:
                self.setCurPtr(self.lineMove(self.curPtr, -self.size.y), selectMode)
            elif command == cmPageDown:
                self.setCurPtr(self.lineMove(self.curPtr, self.size.y), selectMode)
            elif command == cmTextStart:
                self.setCurPtr(0, selectMode)
            elif command == cmTextEnd:
                self.setCurPtr(self.bufLen, selectMode)
            elif command == cmNewLine:
                self.newLine()
            elif command == cmBackSpace:
                self.deleteRange(self.prevChar(self.curPtr), self.curPtr, True)
            elif command == cmDelChar:
                self.deleteRange(self.curPtr, self.nextChar(self.curPtr), True)
            elif command == cmDelWord:
                self.deleteRange(self.curPtr, self.nextWord(self.curPtr), False)
            elif command == cmDelStart:
                self.deleteRange(self.lineStart(self.curPtr), self.curPtr, False)
            elif command == cmDelEnd:
                self.deleteRange(self.curPtr, self.lineEnd(self.curPtr), False)
            elif command == cmDelLine:
                self.deleteRange(self.lineStart(self.curPtr),
                                 self.nextLine(self.curPtr), False)
            elif command == cmInsMode:
                self.toggleInsMode()
            elif command == cmStartSelect:
                self.startSelect()
            elif command == cmHideSelect:
                self.hideSelect()
            elif command == cmIndentMode:
                self.autoIndent = not self.autoIndent
            self.trackCursor(centerCursor)
        finally:
            self.unlock()

    def _handleKeyDownEvent(self, centerCursor: bool, event: Event):
        self.lock()
        try:
            if self.overwrite and not self.hasSelection():
                if self.curPtr != self.lineEnd(self.curPtr):
                    self.selEnd = self.nextChar(self.curPtr)
            self.insertText(event.keyDown.charScan.charCode, 1, False)
            self.trackCursor(centerCursor)
        finally:
            self.unlock()

    def _handleMouseEvent(self, event: Event, selectMode: int):
        if event.mouse.eventFlags & meDoubleClick:
            selectMode |= smDouble
        done = False
        while not done:
            self.lock()
            try:
                if event.what == evMouseAuto:
                    mouse = self.makeLocal(event.mouse.where)
                    d = Point(self.delta.x, self.delta.y)

                    if mouse.x < 0:
                        d.x -= 1
                    if mouse.x >= self.size.x:
                        d.x += 1

                    if mouse.y < 0:
                        d.y -= 1

                    if mouse.y >= self.size.y:
                        d.y += 1

                    self.scrollTo(d.x, d.y)

                self.setCurPtr(self.getMousePtr(event.mouse.where), selectMode)
                selectMode |= smExtend
            finally:
                self.unlock()

            done = (not self.mouseEvent(event, evMouseMove + evMouseAuto))

    def __highlight(self, color: int, drawBuf: DrawBuffer, i: int, pos: int, width: int) -> Tuple[int, int]:
        if self.selStart <= pos < self.selEnd:
            curColor = ((color & 0xFF00) >> 8) << DrawBuffer.CHAR_WIDTH
        else:
            curColor = (color & 0xFF) << DrawBuffer.CHAR_WIDTH
        if self.buffer[pos] == ord('\t'):
            _, r = divmod(i, self.tabSize)
            for j in range(r):
                drawBuf[i + j] = 0x20 | curColor
                i += 1
                if i + j > width:
                    break
            pos += 1
        else:
            drawBuf[i] = curColor | self.buffer[pos]
            pos += 1
            i += 1
        return i, pos
