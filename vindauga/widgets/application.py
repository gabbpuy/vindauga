# -*- coding: utf-8 -*-
import logging

from vindauga.history_support.history_utils import initHistory, doneHistory
from vindauga.types.screen import Screen
import vindauga.types.screen

from .program import Program

logger = logging.getLogger(__name__)


class Application(Program):
    """
    The mother of all applications.
       
    `Application` is a shell around `Program` and differs from it mainly in
    constructor and destructor. `Application` provides the application with a
    standard menu bar, a standard desktop and a standard status line.
       
    In any real application, you usually need to inherit `Application` and
    override some of its methods. For example to add custom menus you must
    override `Program.initMenuBar()`. To add a custom status line, you
    need to override `Program.initStatusLine()`. In the same way, to add
    a custom desktop you need to override `Program.initDeskTop()`.
       
    Should you require a different sequence of subsystem initialization and
    shut down, however, you can derive your application from `Program`, and
    manually initialize and shut down the vindauga subsystems along with your
    own.
    """

    name = 'Application'

    def __init__(self):
        Screen.init()
        vindauga.types.screen.Screen = Screen.screen
        super().__init__()
        Program.application = self
        initHistory()

    def __del__(self):
        doneHistory()

    @staticmethod
    def suspend():
        Screen.screen.suspend()

    @staticmethod
    def resume():
        Screen.screen.resume()
