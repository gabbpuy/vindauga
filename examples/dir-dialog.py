# -*- coding: utf-8 -*-
import logging
import os
from vindauga.constants.command_codes import (cmCancel)
from vindauga.constants.message_flags import mfInformation, mfOKButton
from vindauga.dialogs.change_dir_dialog import ChangeDirDialog
from vindauga.dialogs.message_box import messageBox
from vindauga.types.records.data_record import DataRecord
from vindauga.widgets.application import Application

logger = logging.getLogger('vindauga.examples.dir-dialog')


class MyApp(Application):

    def doWork(self):
        messageBox(f'\003Directory Dialog\nCurrent Directory is {os.getcwd()}', mfInformation, (mfOKButton,))
        _data = self.newDialog()
        messageBox(f'\003Directory Dialog\nCurrent Directory is now {os.getcwd()}', mfInformation, (mfOKButton,))

    def newDialog(self):
        pd = ChangeDirDialog(0, 'dirs')
        control = self.desktop.execView(pd)
        demoDialogData = DataRecord(value='')
        if control != cmCancel:
            demoDialogData = pd.getData()
        del pd
        return demoDialogData.value

    def initMenuBar(self, bounds):
        return []


def setupLogging():
    vLogger = logging.getLogger('vindauga')
    vLogger.propagate = False
    lFormat = "%(name)-25s | %(message)s"
    vLogger.setLevel(logging.DEBUG)
    handler = logging.StreamHandler(open('vindauga.log', 'wt'))
    handler.setFormatter(logging.Formatter(lFormat))
    vLogger.addHandler(handler)


if __name__ == '__main__':
    setupLogging()
    app = MyApp()
    try:
        app.doWork()
    except:
        logger.exception('dir-dialog')

