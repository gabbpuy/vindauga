# -*- coding: utf-8 -*-
from vindauga.widgets.application import Application
from vindauga.widgets.desktop import Desktop


class Demo(Application):
    """
    How to __change the background _pattern
    """
    def __init__(self):
        Desktop.DEFAULT_BACKGROUND = '╬'
        super().__init__()


if __name__ == '__main__':
    app = Demo()
    app.run()
