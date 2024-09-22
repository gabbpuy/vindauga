# -*- coding: utf-8 -*-
import logging
import time

from vindauga.constants.command_codes import cmMenu, cmQuit
from vindauga.constants.event_codes import evCommand
from vindauga.constants.keys import kbF10, kbAltX
from vindauga.constants.message_flags import mfInformation, mfOKButton
from vindauga.dialogs.message_box import messageBox
from vindauga.events.event import Event
from vindauga.types.rect import Rect
from vindauga.types.status_def import StatusDef
from vindauga.types.status_item import StatusItem
from vindauga.widgets.application import Application
from vindauga.widgets.info_window import postInfo
from vindauga.widgets.message_window import postMessage
from vindauga.widgets.status_line import StatusLine

cmAbout = 100
cmTest = 101


class MessageWindowApp(Application):

    def initStatusLine(self, bounds: Rect) -> StatusLine:
        bounds.topLeft.y = bounds.bottomRight.y - 1

        sl = StatusLine(bounds, StatusDef(0, 0xFFFF) +
                        StatusItem('', kbF10, cmMenu) +
                        StatusItem('~Alt-X~ Quit', kbAltX, cmQuit))
        return sl

    def handleEvent(self, event: Event):
        super().handleEvent(event)

        if event.what == evCommand:
            emc = event.message.command

            if emc == cmAbout:
                self.About()
            elif emc == cmTest:
                self.Test()

    @staticmethod
    def About():
        messageBox('\x03Dynamic Text Demo', mfInformation,  (mfOKButton,))

    def Test(self):
        logger.info('Sending "Chau"')
        postInfo(1, '   Chau')
        logger.info('Waiting 10 seconds.')
        s = time.time()
        while time.time() < s + 10:
            self.idle()
            time.sleep(0.1)
        logger.info('Sending "Pepe".')
        postInfo(2, '   Pepe')
        logger.info('Done.')


class PostHandler(logging.Handler):
    def __init__(self):
        super().__init__()

    def emit(self, record):
        try:
            with self.lock:
                postMessage(record.getMessage())
        except AttributeError as e:
            # Logging before the application context is created...
            pass


if __name__ == '__main__':
    logging.basicConfig(level=logging.DEBUG)
    logger = logging.getLogger('vindauga')
    logger.propagate = False
    handlers = logger.handlers
    for handler in handlers:
        # Remove everything else
        logger.removeHandler(handler)
    # Add the message window
    logger.addHandler(PostHandler())
    init = Event(evCommand)
    init.message.command = cmTest
    app = MessageWindowApp()
    app.putEvent(init)
    app.run()
