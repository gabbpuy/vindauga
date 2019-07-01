# -*- coding: utf-8 -*-
from vindauga.constants.buttons import bfDefault, bfNormal
from vindauga.constants.command_codes import (cmOK, cmCancel)
from vindauga.constants.message_flags import mfError, mfInformation, mfOKButton
from vindauga.dialogs.message_box import messageBox
from vindauga.types.draw_buffer import DrawBuffer
from vindauga.types.rect import Rect
from vindauga.widgets.application import Application
from vindauga.widgets.background import Background
from vindauga.widgets.button import Button
from vindauga.widgets.check_boxes import CheckBoxes
from vindauga.widgets.desktop import Desktop
from vindauga.widgets.dialog import Dialog
from vindauga.widgets.input_line import InputLine
from vindauga.widgets.label import Label
from vindauga.widgets.radio_buttons import RadioButtons


class MyBackground(Background):

    def draw(self):
        b = DrawBuffer()
        s = 'Background Example'
        x = 0
        while x < self.size.x:
            b.moveStr(x, s, 0x17)
            x += len(s)

        self.writeLine(0, 0, self.size.x, self.size.y, b)


class MyDesktop(Desktop):

    def initBackground(self, bounds):
        return MyBackground(bounds, Desktop.DEFAULT_BACKGROUND)


class MyApp(Application):

    def doWork(self):
        messageBox('\003Welcome to the cheese ordering system', mfInformation, (mfOKButton,))
        checkBoxData = 1
        radioButtonData = 2
        inputLineData = 'By box'
        demoDialogData = [checkBoxData, radioButtonData, inputLineData]
        data = self.newDialog(demoDialogData)
        if data:
            messageBox('Your order is accepted', mfInformation, (mfOKButton,))
        else:
            messageBox('You cancelled the order', mfError, (mfOKButton,))

    def newDialog(self, demoDialogData):
        pd = Dialog(Rect(20, 6, 60, 19), "Demo Dialog")
        b = CheckBoxes(Rect(3, 3, 18, 6), ("~H~avarti", "~T~ilset", "~J~arlsberg"))

        pd.insert(b)
        pd.insert(Label(Rect(2, 2, 10, 3), "Cheeses", b))

        b = RadioButtons(Rect(22, 3, 34, 6), ("~S~olid", "~R~unny", "~M~elted"))

        pd.insert(b)

        pd.insert(Label(Rect(21, 2, 33, 3), "Consistency", b))

        b = InputLine(Rect(3, 8, 37, 9), 128)
        pd.insert(b)

        pd.insert(Label(Rect(2, 7, 24, 8), "Delivery Instructions", b))
        pd.insert(Button(Rect(15, 10, 25, 12), "~O~K", cmOK, bfDefault))
        pd.insert(Button(Rect(28, 10, 38, 12), "~C~ancel", cmCancel, bfNormal))
        pd.setData(demoDialogData)

        control = self.desktop.execView(pd)
        data = None
        if control != cmCancel:
            data = pd.getData()
        del pd
        return data

    def initStatusLine(self, bounds):
        pass

    def initMenuBar(self, bounds):
        pass

    def initDesktop(self, bounds):
        return MyDesktop(bounds)


if __name__ == '__main__':
    app = MyApp()
    app.doWork()
