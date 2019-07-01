# -*- coding: utf-8 -*-
import itertools
import logging
import string

from vindauga.constants.command_codes import *
from vindauga.constants.edit_command_codes import *
from vindauga.constants.event_codes import *
from vindauga.constants.grow_flags import gfGrowHiX, gfGrowHiY
from vindauga.constants.keys import *
from vindauga.constants.option_flags import ofSelectable
from vindauga.constants.state_flags import sfVisible, sfCursorIns, sfActive, sfExposed
from vindauga.types.records.find_dialog_record import FindDialogRecord
from vindauga.types.records.replace_dialog_record import ReplaceDialogRecord
from vindauga.types.command_set import CommandSet
from vindauga.types.palette import Palette
from vindauga.types.point import Point
from vindauga.types.draw_buffer import BufferArray, DrawBuffer
from vindauga.types.view import View

TAB_MASK = 7

logger = logging.getLogger('vindauga.widgets.editor')

firstKeys = (
    (kbCtrlA, cmWordLeft),
    (kbCtrlC, cmPageDown),
    (kbCtrlD, cmCharRight),
    (kbCtrlE, cmLineUp),
    (kbCtrlF, cmWordRight),
    (kbCtrlG, cmDelChar),
    (kbCtrlH, cmBackSpace),
    (kbCtrlK, 0xFF02),
    (kbCtrlL, cmSearchAgain),
    (kbCtrlM, cmNewLine),
    (kbCtrlO, cmIndentMode),
    (kbCtrlQ, 0xFF01),
    (kbCtrlR, cmPageUp),
    (kbCtrlS, cmCharLeft),
    (kbCtrlT, cmDelWord),
    (kbCtrlU, cmUndo),
    (kbCtrlV, cmInsMode),
    (kbCtrlX, cmLineDown),
    (kbCtrlY, cmDelLine),
    (kbLeft, cmCharLeft),
    (kbRight, cmCharRight),
    (kbCtrlLeft, cmWordLeft),
    (kbCtrlRight, cmWordRight),
    (kbHome, cmLineStart),
    (kbEnd, cmLineEnd),
    (kbUp, cmLineUp),
    (kbDown, cmLineDown),
    (kbPgUp, cmPageUp),
    (kbPgDn, cmPageDown),
    (kbCtrlPgUp, cmTextStart),
    (kbCtrlPgDn, cmTextEnd),
    (kbIns, cmInsMode),
    (kbDel, cmDelChar),
    (kbShiftIns, cmPaste),
    (kbShiftDel, cmCut),
    (kbCtrlIns, cmCopy),
    (kbCtrlDel, cmClear),
)

quickKeys = (
    ('A', cmReplace),
    ('C', cmTextEnd),
    ('D', cmLineEnd),
    ('F', cmFind),
    ('H', cmDelStart),
    ('R', cmTextStart),
    ('S', cmLineStart),
    ('Y', cmDelEnd),
)

blockKeys = (
    ('B', cmStartSelect),
    ('C', cmPaste),
    ('H', cmHideSelect),
    ('K', cmCopy),
    ('Y', cmCut),
)

keyMaps = (firstKeys, quickKeys, blockKeys)


def isWordChar(ch):
    return ch in string.ascii_letters or ch in string.digits or ch == ' '


def scanKeyMap(keyMap, keyCode):
    codeHi, codeLow = divmod(keyCode, 256)

    for _map, command in keyMap:
        mapHi, mapLow = divmod(_map, 256)

        if (mapLow == codeLow) and ((mapHi == 0) or (mapHi == codeHi)):
            return command
    return 0


class Editor(View):
    name = 'Editor'
    cpEditor = "\x06\x07"

    def __init__(self, bounds, hScrollBar, vScrollBar, indicator, bufSize):
        super().__init__(bounds)

        self.delta = Point(0, 0)
        self.limit = Point(0, 0)
        self.curPos = Point(0, 0)
        self.hScrollBar = hScrollBar
        self.vScrollBar = vScrollBar
        self.indicator = indicator

        self.bufSize = bufSize
        self.canUndo = True
        self.selecting = False
        self.overwrite = False
        self.autoIndent = False
        self.isValid = False
        self.modified = False

        self.bufLen = 0
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
        self.editorFlags = 0

        self.findStr = ''
        self.replaceStr = ''
        self.clipboard = None
        self.buffer = None

        self.growMode = gfGrowHiX | gfGrowHiY

        self.options |= ofSelectable
        self.eventMask = evMouseDown | evKeyDown | evCommand | evBroadcast

        self.showCursor()
        self.initBuffer()
        self.setBufLen(0)
        self.isValid = True
        self.clipboard = None

    @staticmethod
    def editorDialog(_flag, *_args):
        return cmOK

    def bufChar(self, pos):
        o = 0
        if pos >= self.curPtr:
            o = self.gapLen
        return chr(self.buffer[pos + o])

    def bufPtr(self, pos):
        if pos >= self.curPtr:
            return pos + self.gapLen
        return pos

    def shutdown(self):
        self.doneBuffer()
        super().shutdown()

    def changeBounds(self, bounds):
        self.setBounds(bounds)
        self.delta.x = max(0, min(self.delta.x, self.limit.x - self.size.x))
        self.delta.y = max(0, min(self.delta.y, self.limit.y - self.size.y))
        self.update(ufView)

    def charPos(self, p, target):
        pos = 0
        while p < target:
            if self.bufChar(p) == '\x09':
                pos |= TAB_MASK

            pos += 1
            p += 1
        return pos

    def charPtr(self, p, target):
        pos = 0

        while pos < target and p < self.bufLen and self.bufChar(p) != '\n':
            if self.bufChar(p) == '\x09':
                pos |= TAB_MASK

            pos += 1
            p += 1

        if pos > target:
            p -= 1
        return p

    def clipCopy(self):
        res = False
        if self.clipboard and self.clipboard is not self:
            res = self.clipboard.insertFrom(self)
            self.selecting = False
            self.update(ufUpdate)
        return res

    def clipCut(self):
        if self.clipCopy():
            self.deleteSelect()

    def clipPaste(self):
        if self.clipboard and self.clipboard is not self:
            self.insertFrom(self.clipboard)

    def convertEvent(self, event):
        if event.what == evKeyDown:
            if (event.keyDown.controlKeyState & kbShift and
                    0x47 <= event.keyDown.charScan.scanCode <= 0x51):
                event.keyDown.charScan.charCode = 0

            key = event.keyDown.keyCode
            if self.keyState:
                if 0x01 <= (key & 0xFF) <= 0x1a:
                    key += 0x40
                if 0x61 <= (key & 0xFF) <= 0x7a:
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

    def isCursorVisible(self):
        return (self.curPos.y >= self.delta.y) and (self.curPos.y < self.delta.y + self.size.y)

    def deleteRange(self, startPtr, endPtr, delSelect):
        if self.hasSelection() and delSelect:
            self.deleteSelect()
        else:
            self.setSelect(self.curPtr, endPtr, True)
            self.deleteSelect()
            self.setSelect(startPtr, self.curPtr, False)
            self.deleteSelect()

    def deleteSelect(self):
        self.insertText([], 0, False)

    def doneBuffer(self):
        del self.buffer

    def doSearchReplace(self):
        done = False
        while not done:
            i = cmCancel
            if not self.search(self.findStr, self.editorFlags):
                if ((self.editorFlags & (efReplaceAll | efDoReplace)) !=
                        (efReplaceAll | efDoReplace)):
                    self.editorDialog(edSearchFailed)
            else:
                if self.editorFlags & efDoReplace:
                    i = cmYes

                    if self.editorFlags & efPromptOnReplace:
                        c = self.makeGlobal(self.cursor)
                        i = self.editorDialog(edReplacePrompt, c)
                    if i == cmYes:
                        self.lock()
                        self.insertText(self.replaceStr, len(self.replaceStr), False)
                        self.trackCursor(False)
                        self.unlock()
            done = not (i != cmCancel and (self.editorFlags & efReplaceAll))

    def doUpdate(self):
        if self.updateFlags:
            self.setCursor(self.curPos.x - self.delta.x, self.curPos.y - self.delta.y)
            if self.updateFlags & ufView:
                self.drawView()
            elif self.updateFlags & ufLine:
                self.drawLines(self.curPos.y - self.delta.y, 1, self.lineStart(self.curPtr))

            if self.hScrollBar:
                self.hScrollBar.setParams(self.delta.x, 0,
                                          self.limit.x - self.size.x,
                                          self.size.x // 2, 1)

            if self.vScrollBar:
                self.vScrollBar.setParams(self.delta.y, 0,
                                          self.limit.y - self.size.y,
                                          self.size.y - 1, 1)

            if self.indicator:
                self.indicator.setValue(self.curPos, self.modified)

            if self.state & sfActive:
                self.updateCommands()
            self.updateFlags = 0

    def draw(self):
        if self.drawLine != self.delta.y:
            self.drawPtr = self.lineMove(self.drawPtr, self.delta.y - self.drawLine)
            self.drawLine = self.delta.y

        self.drawLines(0, self.size.y, self.drawPtr)

    def drawLines(self, y, count, linePtr):
        color = self.getColor(0x0201)

        for line in range(y, y + count):
            b = DrawBuffer()
            self.formatLine(b, linePtr, self.delta.x + self.size.x, color)
            self.writeBuf(0, line, self.size.x, 1, b[self.delta.x:])
            linePtr = self.nextLine(linePtr)

    def find(self):
        findRec = FindDialogRecord(self.findStr, self.editorFlags)

        if self.editorDialog(edFind, findRec) != cmCancel:
            self.findStr = findRec.find
            self.editorFlags = findRec.options & ~efDoReplace
            self.doSearchReplace()

    def getMousePtr(self, m):
        mouse = self.makeLocal(m)

        mouse.x = max(0, min(mouse.x, self.size.x - 1))
        mouse.y = max(0, min(mouse.y, self.size.y - 1))

        return self.charPtr(self.lineMove(self.drawPtr,
                                          mouse.y + self.delta.y - self.drawLine),
                            mouse.x + self.delta.x)

    def getPalette(self):
        palette = Palette(self.cpEditor)
        return palette

    def checkScrollBar(self, event, scrollBar, value):
        if event.message.infoPtr == scrollBar and scrollBar.value != value:
            value = scrollBar.value
            self.update(ufView)

        return value

    def handleEvent(self, event):
        super().handleEvent(event)

        centerCursor = not self.isCursorVisible()
        selectMode = 0

        if (self.selecting or
                (event.what & evMouse and (event.mouse.controlKeyState & kbShift)) or
                (event.what & evKeyboard and (event.keyDown.controlKeyState & kbShift))):
            selectMode = smExtend

        self.convertEvent(event)

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
            else:
                if c not in {
                    cmCut, cmCopy, cmPaste, cmUndo, cmClear, cmCharLeft, cmCharRight, cmWordLeft, cmWordRight,
                    cmLineStart, cmLineEnd, cmLineUp, cmLineDown, cmPageUp, cmPageDown, cmTextStart, cmTextEnd,
                    cmNewLine, cmBackSpace, cmDelChar, cmDelWord, cmDelStart, cmDelEnd, cmDelLine, cmInsMode,
                    cmStartSelect, cmHideSelect, cmIndentMode}:
                    return
                self._handleEditorCommand(c, centerCursor, selectMode)
        elif what == evBroadcast:
            c = event.message.command
            if c == cmScrollBarChanged:
                if ((event.message.infoPtr == self.hScrollBar) or
                        (event.message.infoPtr == self.vScrollBar)):
                    self.delta.x = self.checkScrollBar(event, self.hScrollBar, self.delta.x)
                    self.delta.y = self.checkScrollBar(event, self.vScrollBar, self.delta.y)
                else:
                    return
        else:
            return

        self.clearEvent(event)

    def _handleEditorCommand(self, c, centerCursor, selectMode):
        self.lock()
        if c == cmCut:
            self.clipCut()
        elif c == cmCopy:
            self.clipCopy()
        elif c == cmPaste:
            self.clipPaste()
        elif c == cmUndo:
            self.undo()
        elif c == cmClear:
            self.deleteSelect()
        elif c == cmCharLeft:
            self.setCurPtr(self.prevChar(self.curPtr), selectMode)
        elif c == cmCharRight:
            self.setCurPtr(self.nextChar(self.curPtr), selectMode)
        elif c == cmWordLeft:
            self.setCurPtr(self.prevWord(self.curPtr), selectMode)
        elif c == cmWordRight:
            self.setCurPtr(self.nextWord(self.curPtr), selectMode)
        elif c == cmLineStart:
            self.setCurPtr(self.lineStart(self.curPtr), selectMode)
        elif c == cmLineEnd:
            self.setCurPtr(self.lineEnd(self.curPtr), selectMode)
        elif c == cmLineUp:
            self.setCurPtr(self.lineMove(self.curPtr, -1), selectMode)
        elif c == cmLineDown:
            self.setCurPtr(self.lineMove(self.curPtr, 1), selectMode)
        elif c == cmPageUp:
            self.setCurPtr(self.lineMove(self.curPtr, -(self.size.y - 1)),
                           selectMode)
        elif c == cmPageDown:
            self.setCurPtr(self.lineMove(self.curPtr, self.size.y - 1),
                           selectMode)
        elif c == cmTextStart:
            self.setCurPtr(0, selectMode)
        elif c == cmTextEnd:
            self.setCurPtr(self.bufLen, selectMode)
        elif c == cmNewLine:
            self.newLine()
        elif c == cmBackSpace:
            self.deleteRange(self.prevChar(self.curPtr), self.curPtr, True)
        elif c == cmDelChar:
            self.deleteRange(self.curPtr, self.nextChar(self.curPtr), True)
        elif c == cmDelWord:
            self.deleteRange(self.curPtr, self.nextWord(self.curPtr), False)
        elif c == cmDelStart:
            self.deleteRange(self.lineStart(self.curPtr), self.curPtr, False)
        elif c == cmDelEnd:
            self.deleteRange(self.curPtr, self.lineEnd(self.curPtr), False)
        elif c == cmDelLine:
            self.deleteRange(self.lineStart(self.curPtr),
                             self.nextLine(self.curPtr), False)
        elif c == cmInsMode:
            self.toggleInsMode()
        elif c == cmStartSelect:
            self.startSelect()
        elif c == cmHideSelect:
            self.hideSelect()
        elif c == cmIndentMode:
            self.autoIndent = not self.autoIndent
        self.trackCursor(centerCursor)
        self.unlock()

    def _handleKeyDownEvent(self, centerCursor, event):
        self.lock()
        if self.overwrite and not self.hasSelection():
            if self.curPtr != self.lineEnd(self.curPtr):
                self.selEnd = self.nextChar(self.curPtr)
        self.insertText(event.keyDown.charScan.charCode, 1, False)
        self.trackCursor(centerCursor)
        self.unlock()

    def _handleMouseEvent(self, event, selectMode):
        if event.mouse.eventFlags & meDoubleClick:
            selectMode |= smDouble
        done = False
        while not done:
            self.lock()

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
            self.unlock()

            done = (not self.mouseEvent(event, evMouseMove + evMouseAuto))

    def hasSelection(self):
        return self.selStart != self.selEnd

    def hideSelect(self):
        self.selecting = False
        self.setSelect(self.curPtr, self.curPtr, False)

    def initBuffer(self):
        self.buffer = BufferArray()

    def countLines(self, start, count):
        lines = sum(1 for c in itertools.islice(self.buffer, start, start + count) if c == ord('\n'))
        return lines

    @staticmethod
    def scan(buffer, size, pattern):
        return ''.join(chr(c) for c in buffer[:size]).find(pattern)

    @staticmethod
    def iScan(buffer, size, pattern):
        return ''.join(chr(c) for c in buffer[:size]).lower().find(pattern.lower())

    def insertBuffer(self, p, offset, length, allowUndo, selectText):
        self.selecting = False
        selLen = self.selEnd - self.selStart

        if selLen == 0 and length == 0:
            return True

        delLen = 0
        if allowUndo:
            if self.curPtr == self.selStart:
                delLen = selLen
            else:
                if selLen > self.insCount:
                    delLen = selLen - self.insCount

        newSize = self.bufLen + self.delCount - selLen + delLen + length

        if newSize > self.bufLen + self.delCount and not self.setBufSize(newSize):
            self.editorDialog(edOutOfMemory)
            self.selEnd = self.selStart
            return False

        selLines = self.countLines(self.bufPtr(self.selStart), selLen)

        if self.curPtr == self.selEnd:
            if allowUndo:
                if delLen > 0:
                    o = self.curPtr + self.gapLen - self.delCount - delLen
                    self.buffer[o:o + delLen] = self.buffer[self.selStart:self.selStart + delLen]

                self.insCount -= selLen - delLen

            self.curPtr = self.selStart
            self.curPos.y -= selLines

        if self.delta.y > self.curPos.y:
            self.delta.y -= selLines
            if self.delta.y < self.curPos.y:
                self.delta.y = self.curPos.y

        if length > 0:
            self.buffer[self.curPtr:self.curPtr + length] = BufferArray(p[offset:offset + length])

        lines = self.countLines(self.curPtr, length)
        self.curPtr += length
        self.curPos.y += lines

        self.drawLine = self.curPos.y
        self.drawPtr = self.lineStart(self.curPtr)
        self.curPos.x = self.charPos(self.drawPtr, self.curPtr)

        if not selectText:
            self.selStart = self.curPtr

        self.selEnd = self.curPtr

        self.bufLen += length - selLen
        self.gapLen -= length - selLen

        if allowUndo:
            self.delCount += delLen
            self.insCount += length

        self.limit.y += lines - selLines
        self.delta.y = max(0, min(self.delta.y, self.limit.y - self.size.y))

        if not self.isClipboard():
            self.modified = True

        self.setBufSize(self.bufLen + self.delCount)

        if not selLines and not lines:
            self.update(ufLine)
        else:
            self.update(ufView)
        return True

    def insertFrom(self, editor):
        pt = editor.bufPtr(editor.selStart)

        return self.insertBuffer(editor.buffer,
                                 pt, editor.selEnd - editor.selStart,
                                 self.canUndo, self.isClipboard())

    def insertText(self, text, length, selectText):
        return self.insertBuffer([ord(c) for c in text], 0, length, self.canUndo, selectText)

    def isClipboard(self):
        return self.clipboard is self

    def lineMove(self, p, count):
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

        p = self.lineStart(self.curPtr)
        i = p

        while i < self.curPtr and chr(self.buffer[i]) in string.whitespace:
            i += 1

        self.insertText(nl, 1, False)

        if self.autoIndent:
            self.insertText(self.buffer[p:], i - p, False)

    def nextLine(self, pos):
        return self.nextChar(self.lineEnd(pos))

    def nextWord(self, pos):
        while pos < self.bufLen and isWordChar(self.bufChar(pos)):
            pos = self.nextChar(pos)
        while pos < self.bufLen and not isWordChar(self.bufChar(pos)):
            pos = self.nextChar(pos)

        return pos

    def prevLine(self, pos):
        return self.lineStart(self.prevChar(pos))

    def prevWord(self, pos):
        while pos > 0 and not isWordChar(self.bufChar(self.prevChar(pos))):
            pos = self.prevChar(pos)
        while pos > 0 and isWordChar(self.bufChar(self.prevChar(pos))):
            pos = self.prevChar(pos)
        return pos

    def replace(self):
        replaceRec = ReplaceDialogRecord(self.findStr, self.replaceStr, self.editorFlags)

        if self.editorDialog(edReplace, replaceRec) != cmCancel:
            self.findStr = replaceRec.find
            self.replaceStr = replaceRec.replace
            self.editorFlags = replaceRec.options | efDoReplace
            self.doSearchReplace()

    def scrollTo(self, x, y):
        x = max(0, min(x, self.limit.x - self.size.x))
        y = max(0, min(y, self.limit.y - self.size.y))
        if x != self.delta.x or y != self.delta.y:
            self.delta.x = x
            self.delta.y = y
            self.update(ufView)

    def search(self, findStr, opts):
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
                    self.setSelect(i, i + len(findStr), False)
                    self.trackCursor(not self.isCursorVisible())
                    self.unlock()
                    return True
                else:
                    pos = i + 1

            done = (i == sfSearchFailed)

        return False

    def setBufLen(self, length):
        self.bufLen = length
        self.gapLen = self.bufSize - length
        self.selStart = 0
        self.selEnd = 0
        self.curPtr = 0
        self.delta.x = 0
        self.delta.y = 0
        self.curPos.x = 0
        self.curPos.y = 0
        self.limit.x = maxLineLength
        self.limit.y = self.countLines(self.gapLen, self.bufLen) + 1
        self.drawLine = 0
        self.drawPtr = 0
        self.delCount = 0
        self.insCount = 0
        self.modified = False
        self.update(ufView)

    def setBufSize(self, newSize):
        return newSize <= self.bufSize

    def setCmdState(self, command, enable):
        s = CommandSet()

        s += command
        if enable and (self.state & sfActive):
            self.enableCommands(s)
        else:
            self.disableCommands(s)

    def setCurPtr(self, pos, selectMode):
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

    def setSelect(self, newStart, newEnd, curStart):
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
                self.buffer[self.curPtr:self.curPtr + length] = \
                    self.buffer[self.curPtr + self.gapLen:self.curPtr + self.gapLen + length]
                self.curPos.y += self.countLines(self.curPtr, length)
                self.curPtr = pos
            else:
                length = self.curPtr - pos
                self.curPtr = pos
                self.curPos.y -= self.countLines(self.curPtr, length)
                self.buffer[self.curPtr + self.gapLen:self.curPtr + self.gapLen + length] = \
                    self.buffer[self.curPtr:self.curPtr + length]

            self.drawLine = self.curPos.y
            self.drawPtr = self.lineStart(pos)
            self.curPos.x = self.charPos(self.drawPtr, pos)

            self.delCount = 0
            self.insCount = 0
            self.setBufSize(self.bufLen)
        self.selStart = newStart
        self.selEnd = newEnd
        self.update(flags)

    def setState(self, state, enable):
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

    def trackCursor(self, center):
        if center:
            self.scrollTo(self.curPos.x - self.size.x + 1,
                          self.curPos.y - self.size.y // 2)
        else:
            self.scrollTo(max(self.curPos.x - self.size.x + 1, min(self.delta.x, self.curPos.x)),
                          max(self.curPos.y - self.size.y + 1, min(self.delta.y, self.curPos.y)))

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

    def update(self, flags):
        self.updateFlags |= flags
        if self.lockCount == 0:
            self.doUpdate()

    def updateCommands(self):
        self.setCmdState(cmUndo, (self.delCount != 0 or self.insCount != 0))

        if not self.isClipboard():
            self.setCmdState(cmCut, self.hasSelection())
            self.setCmdState(cmCopy, self.hasSelection())
            self.setCmdState(cmPaste,
                             self.clipboard and (self.clipboard.hasSelection()))

        self.setCmdState(cmClear, self.hasSelection)
        self.setCmdState(cmFind, True)
        self.setCmdState(cmReplace, True)
        self.setCmdState(cmSearchAgain, True)

    def valid(self, *args):
        return self.isValid

    def lineStart(self, pos):
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

    def lineEnd(self, pos):
        if pos < self.curPtr:
            while pos < self.curPtr:
                if self.buffer[pos] == ord('\n'):
                    return pos
                pos += 1
            if self.curPtr == self.bufLen:
                return self.bufLen
        else:
            if pos == self.bufLen:
                return self.bufLen
        while pos + self.gapLen < self.bufSize:
            if self.buffer[pos + self.gapLen] == ord('\n'):
                return pos
            pos += 1
        return pos

    def formatLine(self, drawBuf, linePtr, width, color):
        i = 0  # Drawbuffer
        pos = linePtr  # Buffer

        while pos < self.curPtr and self.buffer[pos] != ord('\n') and i <= width:
            if self.selStart <= pos < self.selEnd:
                curColor = ((color & 0xFF00) >> 8) << DrawBuffer.CHAR_WIDTH
            else:
                curColor = (color & 0xFF) << DrawBuffer.CHAR_WIDTH
            if self.buffer[pos] == 0x9:
                _, r = divmod(i, 8)
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

        if pos >= self.curPtr:
            pos += self.gapLen
            while (pos < self.bufSize) and self.buffer[pos] != ord('\n') and i <= width:
                if self.selStart <= pos < self.selEnd:
                    curColor = ((color & 0xFF00) >> 8) << DrawBuffer.CHAR_WIDTH
                else:
                    curColor = (color & 0xFF) << DrawBuffer.CHAR_WIDTH
                if self.buffer[pos] == 0x9:
                    _, r = divmod(i, 8)
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

        for j in range(i, width):
            if self.selStart <= pos < self.selEnd:
                curColor = ((color & 0xFF00) >> 8) << DrawBuffer.CHAR_WIDTH
            else:
                curColor = (color & 0xFF) << DrawBuffer.CHAR_WIDTH
            drawBuf[j] = 0x20 | curColor

    def nextChar(self, pos):
        if pos == self.bufLen:
            return pos
        return pos + 1

    @staticmethod
    def prevChar(pos):
        if pos == 0:
            return pos
        return pos - 1
