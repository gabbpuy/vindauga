# -*- coding: utf-8 -*-
import logging

from vindauga.constants.buttons import bfDefault, bfNormal
from vindauga.constants.command_codes import cmSave, cmSaveAs, cmCut, cmCopy, cmPaste, cmClear, cmUndo, wnNoNumber, \
    cmCancel
from vindauga.constants.command_codes import cmOpen, cmNew, cmTile, cmCascade, cmOK, hcNoContext, cmQuit, cmResize, \
    cmZoom, cmNext, cmPrev, cmClose, cmMenu
from vindauga.constants.message_flags import mfError, mfInformation, mfYesButton, mfNoButton, mfOKButton, mfCancelButton
from vindauga.constants.edit_command_codes import *
from vindauga.constants.event_codes import evCommand
from vindauga.constants.keys import *
from vindauga.constants.std_dialog_commands import cdNormal
from vindauga.constants.option_flags import ofCentered, ofTileable
from vindauga.constants.state_flags import sfVisible
from vindauga.dialogs.change_dir_dialog import ChangeDirDialog
from vindauga.dialogs.file_dialog import FileDialog, fdOpenButton, fdOKButton
from vindauga.dialogs.message_box import messageBox, messageBoxRect
from vindauga.menus.menu_bar import MenuBar
from vindauga.menus.menu_item import MenuItem
from vindauga.menus.sub_menu import SubMenu
from vindauga.types.records.data_record import DataRecord
from vindauga.types.command_set import CommandSet
from vindauga.types.rect import Rect
from vindauga.types.status_def import StatusDef
from vindauga.types.status_item import StatusItem
from vindauga.widgets.application import Application
from vindauga.widgets.button import Button
from vindauga.widgets.check_boxes import CheckBoxes
from vindauga.widgets.edit_window import EditWindow
from vindauga.widgets.dialog import Dialog
from vindauga.widgets.history import History
from vindauga.widgets.input_line import InputLine
from vindauga.widgets.label import Label
from vindauga.widgets.program import Program
from vindauga.widgets.status_line import StatusLine

cmChangeDrct = 102
cmDosShell = 103
cmCalculator = 104
cmShowClip = 105
cmMacros = 106


def execDialog(d, data):
    if data:
        d.setData([data])

    p = Program.application.validView(d)
    if not p:
        return cmCancel
    result = Program.desktop.execView(p)
    if result != cmCancel and data:
        d = p.getData()
        result = d.value
    return result


def createFindDialog():
    d = Dialog(Rect(0, 0, 38, 12), 'Find')
    d.options |= ofCentered
    control = InputLine(Rect(3, 3, 32, 4), 80)
    d.insert(control)
    d.insert(Label(Rect(2, 2, 32, 3), '~T~ext to find', control))
    d.insert(History(Rect(32, 3, 35, 4), control, 10))

    d.insert(CheckBoxes(Rect(3, 5, 35, 7), ('~C~ase sensitive', '~W~hole words only', None)))
    d.insert(Button(Rect(14, 9, 24, 11), 'O~K~', cmOK, bfDefault))
    d.insert(Button(Rect(26, 9, 36, 11), 'Cancel', cmCancel, bfNormal))
    d.selectNext(False)
    return d


def createReplaceDialog():
    d = Dialog(Rect(0, 0, 40, 16), 'Replace')
    d.options |= ofCentered

    control = InputLine(Rect(3, 3, 34, 4), 80)
    d.insert(control)
    d.insert(Label(Rect(2, 2, 34, 3), '~T~ext to find', control))
    d.insert(History(Rect(34, 3, 37, 4), control, 10))

    control = InputLine(Rect(3, 6, 34, 7), 80)
    d.insert(control)
    d.insert(Label(Rect(2, 5, 34, 6), '~N~ew _text', control))
    d.insert(History(Rect(34, 6, 37, 7), control, 11))

    d.insert(CheckBoxes(Rect(3, 8, 37, 12), ('~C~ase sensitive', '~W~hole words only','~P~rompt on replace',
                                             '~R~eplace all')))

    d.insert(
        Button(Rect(17, 13, 27, 15), 'O~K~', cmOK, bfDefault))
    d.insert(Button(Rect(28, 13, 38, 15), 'Cancel', cmCancel, bfNormal))
    d.selectNext(False)
    return d


def isTileable(p, *args):
    return p.options & ofTileable and p.state * sfVisible


class EditorApp(Application):
    def __init__(self):
        super().__init__()
        ts = CommandSet()
        ts.enableCmd(cmSave)
        ts.enableCmd(cmSaveAs)
        ts.enableCmd(cmCut)
        ts.enableCmd(cmCopy)
        ts.enableCmd(cmPaste)
        ts.enableCmd(cmClear)
        ts.enableCmd(cmUndo)
        ts.enableCmd(cmFind)
        ts.enableCmd(cmReplace)
        ts.enableCmd(cmSearchAgain)
        self.disableCommands(ts)

        self.editorDialog = self.doEditorDialog
        self.clipWindow = self.openEditor(None, False)

    def initMenuBar(self, bounds):
        bounds.bottomRight.y = bounds.topLeft.y + 1

        sub1 = (SubMenu('~F~ile', kbAltF) +
                MenuItem("~O~pen", cmOpen, kbF3, hcNoContext, "F3") +
                MenuItem("~N~ew", cmNew, kbNoKey) +
                MenuItem("~S~ave", cmSave, kbF2, hcNoContext, "F2") +
                MenuItem("S~a~ve as...", cmSaveAs, kbNoKey) +
                MenuItem.newLine() +
                MenuItem("~C~hange dir...", cmChangeDrct, kbNoKey) +
                MenuItem("E~x~it", cmQuit, kbAltX, hcNoContext, "Alt+X"))

        sub2 = (SubMenu("~E~dit", kbAltE) +
                MenuItem("~U~ndo", cmUndo, kbNoKey) +
                MenuItem.newLine() +
                MenuItem("Cu~t~", cmCut, kbShiftDel, hcNoContext, "Shift+Del") +
                MenuItem("~C~opy", cmCopy, kbCtrlIns, hcNoContext, "Ctrl+Ins") +
                MenuItem("~P~aste", cmPaste, kbShiftIns, hcNoContext, "Shift+Ins") +
                MenuItem("~S~how clipboard", cmShowClip, kbNoKey) +
                MenuItem.newLine() +
                MenuItem("~C~lear", cmClear, kbCtrlDel, hcNoContext, "Ctrl+Del"))

        sub3 = (SubMenu("~S~earch", kbAltS) +
                MenuItem("~F~ind...", cmFind, kbNoKey) +
                MenuItem("~R~eplace...", cmReplace, kbNoKey) +
                MenuItem("~S~earch again", cmSearchAgain, kbNoKey))

        sub4 = (SubMenu("~W~indows", kbAltW) +
                MenuItem("~S~ize/move", cmResize, kbCtrlF5, hcNoContext, "Ctrl+F5") +
                MenuItem("~Z~oom", cmZoom, kbF5, hcNoContext, "F5") +
                MenuItem("~T~ile", cmTile, kbNoKey) +
                MenuItem("C~a~scade", cmCascade, kbNoKey) +
                MenuItem("~N~ext", cmNext, kbF6, hcNoContext, "F6") +
                MenuItem("~P~revious", cmPrev, kbShiftF6, hcNoContext, "Shift+F6") +
                MenuItem("~C~lose", cmClose, kbCtrlW, hcNoContext, "Ctrl+W"))
        return MenuBar(bounds, sub1 + sub2 + sub3 + sub4)

    def initStatusLine(self, bounds):
        bounds.topLeft.y = bounds.bottomRight.y - 1
        return StatusLine(bounds, StatusDef(0, 0xFFFF) +
                          StatusItem("~F10~ Menu", kbF10, cmMenu) +
                          StatusItem("~F2~ Save", kbF2, cmSave) +
                          StatusItem("~F3~ Open", kbF3, cmOpen) +
                          StatusItem("~Ctrl+W~ Close", kbCtrlW, cmClose) +
                          StatusItem("~F5~ Zoom", kbF5, cmZoom) +
                          StatusItem("~F6~ Next", kbF6, cmNext) +
                          StatusItem(0, kbCtrlF5, cmResize)
                          )

    def doEditorDialog(self, dialog, *args):
        if dialog == edOutOfMemory:
            return messageBox('Not enough memory for this operation', mfError, (mfOKButton,))
        if dialog == edReadError:
            return messageBox('Error reading file {}'.format(args[0]), mfError, (mfOKButton,))
        if dialog == edWriteError:
            return messageBox('Error writing file {}'.format(args[0]), mfError, (mfOKButton,))
        if dialog == edCreateError:
            return messageBox('Error creating file {}'.format(args[0]), mfError, (mfOKButton,))
        if dialog == edSaveModify:
            return messageBox('%s has been modified. Save?'.format(args[0]), mfInformation,
                              (mfYesButton, mfNoButton, mfCancelButton))
        if dialog == edSaveUntitled:
            return messageBox('Save untitled file?', mfInformation,
                              (mfYesButton, mfNoButton, mfCancelButton))
        if dialog == edSaveUntitled:
            return execDialog(
                FileDialog('*.*', 'Save file as', '~N~ame', fdOKButton, 101), args[0]
            )

        if dialog == edSearchFailed:
            return messageBox('Search string not found', mfError, (mfOKButton,))

        if dialog == edReplace:
            return execDialog(createReplaceDialog(), args[0])

        if dialog == edReplacePrompt:
            return self.doReplacePrompt(args[0])

    def doReplacePrompt(self, cursor):
        r = Rect(0, 2, 40, 9)
        r.move((self.desktop.size.x - r.bottomRight.x) // 2, 0)
        lower = self.desktop.makeGlobal(r.bottomRight)
        if cursor.y <= lower.y:
            r.move(0, (self.desktop.size.y - r.bottomRight.y) // 2)

        return messageBoxRect(r, 'Replace this occurrence?', mfInformation, (mfYesButton, mfNoButton, mfCancelButton))

    def openEditor(self, filename, visible):
        r = self.desktop.getExtent()
        p = self.validView(EditWindow(r, filename, wnNoNumber))
        if not visible:
            p.hide()
        self.desktop.insert(p)
        return p

    def fileOpen(self):
        filename = '*'
        c = execDialog(FileDialog('*', 'Open file', '~N~ame', fdOpenButton, 100), filename)
        if c != cmCancel:
            self.openEditor(c, True)

    def fileNew(self):
        self.openEditor(None, True)

    def changeDir(self):
        execDialog(ChangeDirDialog(cdNormal, 0), None)

    def doShell(self):
        pass

    def showClip(self):
        self.clipWindow.select()
        self.clipWindow.show()

    def tile(self):
        self.desktop.tile(self.desktop.getExtent())

    def cascade(self):
        self.desktop.cascade(self.desktop.getExtent())

    def handleEvent(self, event):
        super().handleEvent(event)
        if event.what != evCommand:
            return

        emc = event.message.command
        if emc == cmOpen:
            if event.message.infoPtr:
                self.openEditor(event.message.infoPtr, True)
            else:
                self.fileOpen()
        elif emc == cmNew:
            self.fileNew()
        elif emc == cmChangeDrct:
            self.changeDir()
        elif emc == cmShowClip:
            self.showClip()
        elif emc == cmTile:
            self.tile()
        elif emc == cmCascade:
            self.cascade()
        else:
            return

        self.clearEvent(event)

    def idle(self):
        super().idle()
        if self.desktop.firstThat(isTileable, 0):
            self.enableCommand(cmTile)
            self.enableCommand(cmCascade)
        else:
            for command in (cmSave, cmSaveAs, cmUndo, cmCut, cmCopy, cmPaste, cmClear,
                            cmFind, cmReplace, cmSearchAgain, cmTile, cmCascade):
                self.disableCommand(command)


def setupLogging():
    logger = logging.getLogger('vindauga')
    logger.propagate = False
    format = "%(name)s\t %(message)s"
    logger.setLevel(logging.DEBUG)
    handler = logging.StreamHandler(open('vindauga.log', 'wt'))
    handler.setFormatter(logging.Formatter(format))
    logger.addHandler(handler)


if __name__ == '__main__':
    setupLogging()
    app = EditorApp()
    app.run()
