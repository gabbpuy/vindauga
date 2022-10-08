#!/usr/bin/python
import time

from vindauga.constants.buttons import bfDefault
from vindauga.constants.command_codes import hcNoContext, cmOK, cmCancel, cmYes, cmQuit, cmMenu, cmClose
from vindauga.constants.message_flags import mfConfirmation, mfYesButton, mfNoButton
from vindauga.constants.window_flags import wfClose
from vindauga.constants.event_codes import evCommand, evNothing
from vindauga.constants.keys import kbAltA, kbAltL, kbF10, kbAltX, kbAltF3
from vindauga.constants.option_flags import ofCentered
from vindauga.dialogs.message_box import messageBox
from vindauga.events.event import Event
from vindauga.menus.menu import Menu
from vindauga.menus.menu_bar import MenuBar
from vindauga.menus.menu_item import MenuItem
from vindauga.menus.sub_menu import SubMenu
from vindauga.types.rect import Rect
from vindauga.types.status_def import StatusDef
from vindauga.types.status_item import StatusItem
from vindauga.widgets.application import Application
from vindauga.widgets.button import Button
from vindauga.widgets.clock import ClockView
from vindauga.widgets.dialog import Dialog
from vindauga.widgets.progress_bar import ProgressBar
from vindauga.widgets.static_text import StaticText
from vindauga.widgets.status_line import StatusLine


cmAboutCmd = 100
cmStatusCmd = 101


class ProgressBarApplication(Application):
    backChar = '▓'

    def __init__(self):
        super().__init__()

        r = self.getExtent()
        r.topLeft.x = r.bottomRight.x - 10
        r.topLeft.y = r.bottomRight.y - 1
        self.clock = ClockView(r)
        self.insert(self.clock)

    def initStatusLine(self, bounds):
        bounds.topLeft.y = bounds.bottomRight.y - 1
        return StatusLine(bounds,
                          (StatusDef(0, 0xFFFF) +
                              StatusItem("", kbF10, cmMenu) +
                              StatusItem("~Alt X~ Exit", kbAltX, cmQuit) +
                              StatusItem("~Alt F3~ Close", kbAltF3, cmClose)))

    def initMenuBar(self, bounds):
        bounds.bottomRight.y = bounds.topLeft.y + 1
        return MenuBar(bounds,
                       Menu(
                           SubMenu('Progress ~B~ar', 0, hcNoContext) +
                           MenuItem('~A~bout', cmAboutCmd, kbAltA, hcNoContext, None) +
                           MenuItem('~P~rogress Bar', cmStatusCmd, kbAltL, hcNoContext, None) +
                           SubMenu('Empty', 0, hcNoContext) +
                           MenuItem('Empty', 0, 0, hcNoContext, None)))

    def handleEvent(self, event):
        super().handleEvent(event)
        if event.what == evCommand:
            if event.message.command == cmAboutCmd:
                logging.error('About Box')
                self.aboutDialog()
                self.clearEvent(event)
            elif event.message.command == cmStatusCmd:
                logging.error('Make Status Go Now')
                self.statusDialog()
                self.clearEvent(event)

    def aboutDialog(self):
        pd = Dialog(Rect(0, 0, 35, 12), 'About')
        pd.options |= ofCentered
        pd.insert(StaticText(
            Rect(1, 2, 34, 7), '\x03Python Vision Example\n\x03\n\x03Using a Progress Bar\n\x03\n'
        ))
        pd.insert(Button(Rect(3, 9, 32, 11), '~O~k', cmOK, bfDefault))
        if self.validView(pd):
            self.desktop.execView(pd)

    def idle(self):
        super().idle()
        self.clock.update()
        # logger.error('Widget Tree:\n' + drawWidgetTree(self))

    @staticmethod
    def isCancel(pd):
        event = Event(evNothing)
        pd.getEvent(event)
        pd.handleEvent(event)
        if event.what == evCommand and event.message.command == cmCancel:
            return messageBox('Are you sure you want to cancel?', mfConfirmation, mfYesButton | mfNoButton) == cmYes
        return False

    def statusDialog(self):
        logging.error('Status Dialog -> IN')
        pd = Dialog(Rect(0, 0, 60, 15), 'Example Progress Bar')
        pd.flags &= wfClose
        pd.options |= ofCentered
        pBar = ProgressBar(Rect(2, 2, pd.size.x - 2, 3), 300, self.backChar)
        pd.insert(pBar)
        pd.insert(Button(Rect(10, pd.size.y - 3, pd.size.x - 10, pd.size.y - 1), '~C~ancel', cmCancel, bfDefault))
        pd = self.validView(pd)
        logging.error('Inserting: %s', pd)
        self.desktop.insert(pd)
        logging.error('Post Insert')
        keepOnGoing = True
        r = Rect(5, 5, pd.size.x - 5, pd.size.y - 5)
        theMessage = StaticText(r, 'This is a modeless dialog box. You can drag this box around the desktop')
        pd.insert(theMessage)
        self.draw()

        for i in range(100):
            pBar.update(i)
            self.idle()
            time.sleep(.2)
            keepOnGoing = not self.isCancel(pd)
            if not keepOnGoing:
                break

        self.destroy(theMessage)
        if keepOnGoing:
            theMessage = StaticText(r, 'Notice that only the attribute is changed to show progress')
            pd.insert(theMessage)
            for i in range(200):
                pBar.update(i)
                self.idle()
                time.sleep(.2)
                keepOnGoing = not self.isCancel(pd)
                if not keepOnGoing:
                    break

        if keepOnGoing:
            theMessage = StaticText(r, 'Syntax: ProgressBar(r:Rect, total:float, bar:_str)')
            pd.insert(theMessage)
            for i in range(300):
                pBar.update(i)
                self.idle()
                time.sleep(.2)
                keepOnGoing = not self.isCancel(pd)
                if not keepOnGoing:
                    break
        self.destroy(pd)


if __name__ == '__main__':
    import logging

    logger = logging.getLogger('vindauga')
    logger.propagate = False
    format = "%(name)-25s | %(message)s"
    logger.setLevel(logging.DEBUG)
    handler = logging.StreamHandler(open('vindauga.log', 'wt'))
    handler.setFormatter(logging.Formatter(format))
    logger.addHandler(handler)

    myApplication = ProgressBarApplication()
    myApplication.run()
