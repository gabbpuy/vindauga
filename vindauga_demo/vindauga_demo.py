# -*- coding: utf-8 -*-
from __future__ import annotations

import logging
from pathlib import Path
import random
import os
import sys

from vindauga.constants.buttons import bfDefault, bfNormal
from vindauga.constants.command_codes import cmMenu, cmQuit, cmClose, hcNoContext, cmNext, cmZoom, cmHelp, cmResize, \
    cmCancel, cmOK, cmCascade, cmTile
from vindauga.constants.event_codes import evCommand
from vindauga.constants.keys import kbF10, kbAltX, kbF6, kbF3, kbNoKey, kbF11, kbF5, kbCtrlF5, kbCtrlW
from vindauga.constants.message_flags import mfError, mfOKButton
from vindauga.constants.option_flags import ofCentered
from vindauga.constants.option_flags import ofTileable
from vindauga.dialogs.calculator_dialog import CalculatorDialog
from vindauga.dialogs.calendar import CalendarWindow
from vindauga.dialogs.change_dir_dialog import ChangeDirDialog, cmChangeDir
from vindauga.dialogs.color_dialog import ColorDialog
from vindauga.dialogs.file_dialog import FileDialog, fdOpenButton
from vindauga.dialogs.message_box import messageBox
from vindauga.dialogs.mouse_dialog import MouseDialog
from vindauga.events.event import Event
from vindauga.events.event_queue import event_queue
from vindauga.gadgets.puzzle import PuzzleWindow
from vindauga.menus.menu_bar import MenuBar
from vindauga.menus.menu_item import MenuItem
from vindauga.menus.sub_menu import SubMenu
from vindauga.utilities.message import message
from vindauga.terminal.terminal_view import TerminalView
from vindauga.terminal.terminal_window import TerminalWindow
from vindauga.types.color_group import ColorGroup
from vindauga.types.color_item import ColorItem
from vindauga.types.rect import Rect
from vindauga.types.screen import Screen
from vindauga.types.status_def import StatusDef
from vindauga.types.status_item import StatusItem
from vindauga.types.view import View
from vindauga.utilities.filesystem.pushd import pushd
from vindauga.widgets.application import Application
from vindauga.widgets.background import Background
from vindauga.widgets.button import Button
from vindauga.widgets.check_boxes import CheckBoxes
from vindauga.widgets.clock import ClockView
from vindauga.widgets.desktop import Desktop
from vindauga.widgets.dialog import Dialog
from vindauga.widgets.file_window import FileWindow
from vindauga.widgets.input_line import InputLine
from vindauga.widgets.label import Label
from vindauga.widgets.radio_buttons import RadioButtons
from vindauga.widgets.static_text import StaticText
from vindauga.widgets.status_line import StatusLine

from demo.app_commands import AppCommands
from demo.ascii_table import AsciiChart
from demo.help_contexts import HelpContexts
from vindauga.widgets.wallpaper_background import WallpaperBackground

logger = logging.getLogger('vindauga.vindauga_demo')

checkBoxData = 0
radioButtonData = 0
inputLineData = ''

demoDialogData = list(reversed([checkBoxData, radioButtonData, inputLineData]))


def setupLogging(logger_name: str):
    logger = logging.getLogger(logger_name)
    logger.propagate = False
    format = '%(asctime)s.%(msecs)03d\t%(name)s\t%(levelname)s\t%(message)s'
    logger.setLevel(logging.DEBUG)
    handler = logging.StreamHandler(open(f'{logger_name}.log', 'wt'))
    handler.setFormatter(logging.Formatter(format, datefmt='%H:%M:%S'))
    logger.addHandler(handler)


class WallpaperDesktop(Desktop):
    """
    Desktop with wallpaper background.
    """

    def initBackground(self, bounds: Rect):
        """
        Initialize wallpaper background.
        """
        # Look for a sample image in the examples directory
        wallpapers = Path(__file__).parent / 'wallpapers'

        # Try to find any image file in examples directory
        image_extensions = ['.png', '.jpg', '.jpeg', '.gif']
        sample_image = None

        random.shuffle(image_extensions)

        for ext in image_extensions:
            try:
                sample_image = random.choice(list(wallpapers.glob('*' + ext)))
            except IndexError:
                continue
            if sample_image:
                break

        # If no image found, create a simple test pattern
        if not sample_image:
            logger.warning("No sample image found in examples directory")
            return Background(bounds, '▒')

        try:
            wallpaper_bg = WallpaperBackground(
                bounds,
                sample_image,
            )
            logger.info("Created wallpaper background with image: %s", sample_image)
            return wallpaper_bg
        except Exception as e:
            logger.exception("Failed to create wallpaper background: %s", e)
            # Fallback to regular background
            return Background(bounds, '▒')


class VindaugaDemo(Application):
    def __init__(self):
        super().__init__()
        self.wallpaper_desktop = None
        self.helpInUse = False

        r = self.getExtent()
        r.topLeft.x = r.bottomRight.x - 9
        r.topLeft.y = r.bottomRight.y - 1
        self.clock = ClockView(r)
        self.insert(self.clock)

        for fileSpec in sys.argv[1:]:
            if os.path.isdir(fileSpec):
                fileSpec = os.path.join(fileSpec, '*')

            if '*' in fileSpec or '?' in fileSpec:
                self.openFile(fileSpec)
            else:
                w = self.validView(FileWindow(fileSpec))
                if w:
                    self.desktop.insert(w)

    @staticmethod
    def isTileable(view: View, *_args) -> bool:
        return view.options & ofTileable != 0

    @staticmethod
    def closeView(view: View, params):
        message(view, evCommand, cmClose, params)

    def initDesktop(self, bounds: Rect) -> Desktop:
        bounds.topLeft.y += 1
        bounds.bottomRight.y -= 1
        self.wallpaper_desktop = WallpaperDesktop(bounds)
        return self.wallpaper_desktop

    def initStatusLine(self, bounds: Rect) -> StatusLine:
        bounds.topLeft.y = bounds.bottomRight.y - 1

        return StatusLine(bounds,
                          StatusDef(0, 50) +
                          StatusItem('~F11~ Help', kbF11, cmHelp) +
                          StatusItem('~Alt+X~ Exit', kbAltX, cmQuit) +
                          StatusItem("", kbCtrlW, cmClose) +
                          StatusItem("", kbF10, cmMenu) +
                          StatusItem("", kbF5, cmZoom) +
                          StatusItem("", kbCtrlF5, cmResize) +
                          StatusDef(50, 0xFFFF) +
                          StatusItem('Howdy', kbF11, cmHelp))

    def tile(self):
        self.desktop.tile(self.desktop.getExtent())

    def initMenuBar(self, bounds: Rect) -> MenuBar:
        bounds.bottomRight.y = bounds.topLeft.y + 1
        subMenu1 = (SubMenu('~≡~', 0, hcNoContext) +
                    MenuItem('~A~bout...', AppCommands.cmAboutCmd, kbNoKey, HelpContexts.hcSAbout) +
                    MenuItem.newLine() +
                    MenuItem('~P~uzzle', AppCommands.cmPuzzleCmd, kbNoKey, HelpContexts.hcSPuzzle) +
                    MenuItem('Ca~l~endar', AppCommands.cmCalendarCmd, kbNoKey, HelpContexts.hcSCalendar) +
                    MenuItem('Ascii ~T~able', AppCommands.cmAsciiCmd, kbNoKey, HelpContexts.hcSAsciiTable) +
                    MenuItem('~C~alculator', AppCommands.cmCalcCmd, kbNoKey, HelpContexts.hcCalculator))

        subMenu2 = (SubMenu('~F~ile', 0, HelpContexts.hcFile) +
                    MenuItem('~O~pen', AppCommands.cmOpenCmd, kbF3, HelpContexts.hcFOpen, 'F3') +
                    MenuItem('~C~hange Dir...', AppCommands.cmChDirCmd, kbNoKey, HelpContexts.hcFChangeDir) +
                    MenuItem.newLine() +
                    MenuItem('~D~ialog', AppCommands.cmDialogCmd, kbNoKey, hcNoContext) +
                    MenuItem('~S~hell', AppCommands.cmShellCmd, kbNoKey, HelpContexts.hcFDosShell) +
                    MenuItem.newLine() +
                    MenuItem('E~x~it', cmQuit, kbAltX, hcNoContext, 'Alt+X'))

        subMenu3 = (SubMenu('~W~indows', 0, HelpContexts.hcWindows) +
                    MenuItem('~R~esize/move', cmResize, kbCtrlF5, HelpContexts.hcWSizeMove, 'Ctrl+F5') +
                    MenuItem('~Z~oom', cmZoom, kbF5, HelpContexts.hcWZoom, 'F5') +
                    MenuItem('~N~ext', cmNext, kbF6, HelpContexts.hcWNext, 'F6') +
                    MenuItem('~C~lose', cmClose, kbCtrlW, HelpContexts.hcWClose, 'Ctrl+W') +
                    MenuItem('~T~ile', cmTile, kbNoKey, HelpContexts.hcWTile) +
                    MenuItem('C~a~scade', cmCascade, kbNoKey, HelpContexts.hcWCascade))

        subMenu4 = (SubMenu('~O~ptions', 0, HelpContexts.hcOptions) +
                    MenuItem('~M~ouse...', AppCommands.cmMouseCmd, kbNoKey, HelpContexts.hcOMouse) +
                    MenuItem('~C~olors...', AppCommands.cmColorCmd, kbNoKey, HelpContexts.hcOColors) +
                    MenuItem('~W~allpaper', AppCommands.cmLoadWallpaperCmd, kbNoKey, HelpContexts.hcWallpaper))

        subMenu5 = (SubMenu('~R~esolution', 0, hcNoContext) +
                    MenuItem('~1~ 80x25', AppCommands.cmTest80x25, kbNoKey, hcNoContext) +
                    MenuItem('~2~ 80x28', AppCommands.cmTest80x28, kbNoKey, hcNoContext) +
                    MenuItem('~3~ 80x50', AppCommands.cmTest80x50, kbNoKey, hcNoContext) +
                    MenuItem('~4~ 90x30', AppCommands.cmTest90x30, kbNoKey, hcNoContext) +
                    MenuItem('~5~ 94x34', AppCommands.cmTest94x34, kbNoKey, hcNoContext) +
                    MenuItem('~6~ 132x25', AppCommands.cmTest132x25, kbNoKey, hcNoContext) +
                    MenuItem('~7~ 132x50', AppCommands.cmTest132x50, kbNoKey, hcNoContext) +
                    MenuItem('~8~ 132x60', AppCommands.cmTest132x60, kbNoKey, hcNoContext) +
                    MenuItem('~9~ 160x60', AppCommands.cmTest160x60, kbNoKey, hcNoContext)
                    )

        return MenuBar(bounds, subMenu1 + subMenu2 + subMenu3 + subMenu4 + subMenu5)

    def handleEvent(self, event: Event):
        super().handleEvent(event)
        if event.what == evCommand:
            emc = event.message.command
            if emc == cmHelp and not self.helpInUse:
                self.helpInUse = True
            elif isinstance(emc, AppCommands):
                self.clearEvent(event)
                if emc == AppCommands.cmAboutCmd:
                    self.aboutDialogBox()
                elif emc == AppCommands.cmCalendarCmd:
                    self.calendar()
                elif emc == AppCommands.cmAsciiCmd:
                    self.asciiTable()
                elif emc == AppCommands.cmCalcCmd:
                    self.calculator()
                elif emc == AppCommands.cmPuzzleCmd:
                    self.newPuzzle()
                elif emc == AppCommands.cmOpenCmd:
                    self.openFile('*')
                elif emc == AppCommands.cmChDirCmd:
                    self.changeDir()
                elif emc == AppCommands.cmShellCmd:
                    self.doShellWindow()
                elif emc == AppCommands.cmMouseCmd:
                    self.mouse()
                elif emc == AppCommands.cmColorCmd:
                    self.colors()
                elif emc == AppCommands.cmDialogCmd:
                    self.newDialog()
                elif emc == AppCommands.cmLoadWallpaperCmd:
                    self.loadWallpaper()
                elif AppCommands.cmTest80x25 <= emc <= AppCommands.cmTest160x60:
                    self.testMode(emc)
            elif emc == cmTile:
                self.clearEvent(event)
                self.tile()
            elif emc == cmCascade:
                self.clearEvent(event)
                self.cascade()

    def loadWallpaper(self):
        fileSpec = "*"
        wallpapers = Path(__file__).parent / 'wallpapers'
        with pushd(wallpapers):
            d = FileDialog(fileSpec, 'Load Wallpaper Image', '~N~ame', fdOpenButton, 110)
            if d and self.desktop.execView(d) != cmCancel:
                filename = d.getFilename()
                # Validate that the selected file is an image
                if not self._is_image_file(filename):
                    messageBox("Please select an image file.\n\n"
                               "Supported formats:\n"
                               "PNG, JPG, JPEG, GIF",
                               mfError, (mfOKButton,))
                    self.destroy(d)
                    return

                # Find the wallpaper background and set the new image
                wallpaper_bg = self.desktop._background
                if isinstance(wallpaper_bg, WallpaperBackground):
                    try:
                        wallpaper_bg.set_image(filename)
                        logger.info("Successfully loaded new wallpaper: %s", filename)
                    except Exception as e:
                        logger.error("Failed to load wallpaper image %s: %s", filename, e)
                        messageBox(f"Failed to load image:\n{filename}\n\n"
                                   f"Error: {str(e)}",
                                   mfError, (mfOKButton,))
                else:
                    messageBox("Internal error: Could not find wallpaper background to update.",
                               mfError, (mfOKButton,))

                self.destroy(d)

    def _is_image_file(self, filename: str) -> bool:
        """Check if filename has a supported image extension."""
        if not filename:
            return False

        # Convert to lowercase for case-insensitive comparison
        lower_filename = filename.lower()
        image_extensions = ['.png', '.jpg', '.jpeg', '.gif']
        return any(lower_filename.endswith(ext) for ext in image_extensions)

    def testMode(self, mode):
        width, height = (int(i) for i in mode.name.replace('cmTest', '').split('x'))
        Screen.screen.setScreenSize(width, height)

    def idle(self):
        super().idle()
        self.clock.update()
        TerminalView.updateTerminals()
        if self.desktop.firstThat(self.isTileable, None):
            self.enableCommand(cmTile)
            self.enableCommand(cmCascade)
        else:
            self.disableCommand(cmTile)
            self.disableCommand(cmCascade)

    def doShellWindow(self):
        r = Rect(0, 0, 84, 29)
        r.grow(-1, -1)
        t = TerminalWindow(r, 'Terminal', 0)
        self.desktop.insert(t)

    def newPuzzle(self):
        p = PuzzleWindow()
        self.desktop.insert(p)

    def newDialog(self):
        pd = Dialog(Rect(20, 6, 60, 19), 'Demo Dialog')
        b = CheckBoxes(Rect(3, 3, 18, 6), ('~H~avarti', '~T~ilset', '~J~arlsberg'))
        pd.insert(b)
        pd.insert(Label(Rect(2, 2, 10, 3), 'Cheeses', b))
        b = RadioButtons(Rect(22, 3, 34, 6), ('~S~olid', '~R~unny', '~M~elted',))
        pd.insert(b)
        pd.insert(Label(Rect(21, 2, 33, 3), 'Consistency', b))

        b = InputLine(Rect(3, 8, 37, 9), 128)
        pd.insert(b)

        pd.insert(Label(Rect(2, 7, 24, 8), 'Delivery Instructions', b))
        pd.insert(Button(Rect(15, 10, 25, 12), '~O~K', cmOK, bfDefault))
        pd.insert(Button(Rect(28, 10, 38, 12), '~C~ancel', cmCancel, bfNormal))
        pd.setData(demoDialogData)

        control = self.desktop.execView(pd)
        data = []
        if control != cmCancel:
            data = pd.getData()
        del pd
        return data

    def aboutDialogBox(self):
        aboutBox = Dialog(Rect(0, 0, 39, 13), 'About')
        aboutBox.insert(
            StaticText(Rect(9, 2, 30, 9),
                       """\003Vindauga Demo\n\n\003Python Version\n\n\003Copyright (C) 1994\n\n\003Borland International""")
        )
        aboutBox.insert(
            Button(Rect(14, 10, 26, 12), ' OK', cmOK, bfDefault)
        )
        aboutBox.options |= ofCentered
        self.executeDialog(aboutBox, None)

    def asciiTable(self):
        chart = self.validView(AsciiChart())
        if chart:
            chart.helpCtx = HelpContexts.hcAsciiTable
            self.desktop.insert(chart)

    def calendar(self):
        cal = self.validView(CalendarWindow())
        if cal:
            cal.helpCtx = HelpContexts.hcCalendar
            self.desktop.insert(cal)

    def calculator(self):
        calc = self.validView(CalculatorDialog())
        if calc:
            calc.helpCtx = HelpContexts.hcCalculator
            self.desktop.insert(calc)

    def cascade(self):
        self.desktop.cascade(self.desktop.getExtent())

    def changeDir(self):
        d = self.validView(ChangeDirDialog(0, cmChangeDir))
        if d:
            d.helpCtx = HelpContexts.hcFCChDirDBox
            self.desktop.execView(d)
            self.destroy(d)

    def colors(self):
        group1 = (ColorGroup('Desktop')
                  + ColorItem('Color', 1)

                  + ColorGroup('Menus')
                  + ColorItem('Normal', 2)
                  + ColorItem('Disabled', 3)
                  + ColorItem('Shortcut', 4)
                  + ColorItem('Selected', 5)
                  + ColorItem('Selected disabled', 6)
                  + ColorItem('Shortcut selected', 7)
                  )

        group2 = (ColorGroup('Dialogs / Calculator')
                  + ColorItem('Frame/background', 33)
                  + ColorItem('Frame icons', 34)
                  + ColorItem('Scroll bar page', 35)
                  + ColorItem('Scroll bar icons', 36)
                  + ColorItem('Static text', 37)
                  + ColorItem('Label normal', 38)
                  + ColorItem('Label selected', 39)
                  + ColorItem('Label shortcut', 40)

                  + ColorItem('Button normal', 41)
                  + ColorItem('Button default', 42)
                  + ColorItem('Button selected', 43)
                  + ColorItem('Button disabled', 44)
                  + ColorItem('Button shortcut', 45)
                  + ColorItem('Button shadow', 46)
                  + ColorItem('Cluster normal', 47)
                  + ColorItem('Cluster selected', 48)
                  + ColorItem('Cluster shortcut', 49)

                  + ColorItem('Input normal', 50)
                  + ColorItem('Input selected', 51)
                  + ColorItem('Input arrow', 52)

                  + ColorItem('History button', 53)
                  + ColorItem('History sides', 54)
                  + ColorItem('History bar page', 55)
                  + ColorItem('History bar icons', 56)

                  + ColorItem('List normal', 57)
                  + ColorItem('List focused', 58)
                  + ColorItem('List selected', 59)
                  + ColorItem('List divider', 60)
                  + ColorItem('Information pane', 61))

        group3 = (ColorGroup('Viewer')
                  + ColorItem('Frame passive', 8)
                  + ColorItem('Frame active', 9)
                  + ColorItem('Frame icons', 10)
                  + ColorItem('Scroll bar page', 11)
                  + ColorItem('Scroll bar icons', 12)
                  + ColorItem('Text', 13)

                  + ColorGroup('Puzzle')
                  + ColorItem('Frame passive', 8)
                  + ColorItem('Frame active', 9)
                  + ColorItem('Frame icons', 10)
                  + ColorItem('Scroll bar page', 11)
                  + ColorItem('Scroll bar icons', 12)
                  + ColorItem('Normal text', 13)
                  + ColorItem('Highlighted text', 14))

        group4 = (ColorGroup('Calendar')
                  + ColorItem('Frame passive', 16)
                  + ColorItem('Frame active', 17)
                  + ColorItem('Frame icons', 18)
                  + ColorItem('Scroll bar page', 19)
                  + ColorItem('Scroll bar icons', 20)
                  + ColorItem('Normal text', 21)
                  + ColorItem('Current day', 22)

                  + ColorGroup('Ascii table')
                  + ColorItem('Frame passive', 24)
                  + ColorItem('Frame active', 25)
                  + ColorItem('Frame icons', 26)
                  + ColorItem('Scroll bar page', 27)
                  + ColorItem('Scroll bar icons', 28)
                  + ColorItem('Text', 29))

        group5 = group1 + group2 + group3 + group4

        c = ColorDialog(None, group5)

        if self.validView(c):
            c.helpCtx = HelpContexts.hcOCColorsDBox
            c.setData(self.getPalette())
            if self.desktop.execView(c) != cmCancel:
                pal = c.getData()
                self.setPalette(pal)
                self.setScreenMode(Screen.screen.screenMode)
        self.destroy(c)

    def mouse(self):
        mouseCage = self.validView(MouseDialog())
        if mouseCage:
            mouseCage.helpCtx = HelpContexts.hcOMMouseDBox
            mouseCage.setData([event_queue.mouseReverse])
            if self.desktop.execView(mouseCage) != cmCancel:
                data = mouseCage.getData()
                event_queue.mouseReverse = data[0].value
            self.destroy(mouseCage)

    def openFile(self, fileSpec):
        d = self.validView(FileDialog(fileSpec, 'Open a File', '~N~ame', fdOpenButton, 100))
        if d and self.desktop.execView(d) != cmCancel:
            filename = d.getFilename()
            d.helpCtx = HelpContexts.hcFOFileOpenDBox
            w = self.validView(FileWindow(filename))
            if w:
                self.desktop.insert(w)
            self.destroy(d)


def run():
    myApp = VindaugaDemo()
    myApp.run()


if __name__ == '__main__':
    setupLogging('vindauga')

    try:
        run()
    except:
        logger.exception('vindauga fail')
