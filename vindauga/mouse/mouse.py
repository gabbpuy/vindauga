# -*- coding: utf-8 -*-
from vindauga.events.mouse_event import MouseEvent
from vindauga.screen_driver.hardware_info import hardware_info


class HW_Mouse:
    _buttonCount: int = 0
    __handlerInstalled = False
    __noMouse = False

    def __init__(self):
        self._resume()

    @staticmethod
    def _show():
        hardware_info.cursorOn()

    @staticmethod
    def _hide():
        hardware_info.cursorOff()

    @staticmethod
    def _setRange(low: int, high: int):
        pass

    @staticmethod
    def _getEvent(event: MouseEvent):
        """Get mouse event"""
        event.buttons = 0
        event.wheel = 0
        event.where.x = 0
        event.where.y = 0
        event.eventFlags = 0

    @staticmethod
    def _present() -> bool:
        return HW_Mouse._buttonCount != 0

    @staticmethod
    def _suspend():
        HW_Mouse._hide()
        HW_Mouse._buttonCount = 0

    @staticmethod
    def _resume():
        HW_Mouse._buttonCount = hardware_info.getButtonCount()
        HW_Mouse._show()

    @staticmethod
    def _inhibit():
        HW_Mouse.__noMouse = True

    @staticmethod
    def registerHandler():
        if not HW_Mouse._present():
            return
        HW_Mouse.__handlerInstalled = True

    def __del__(self):
        HW_Mouse._suspend()


class Mouse(HW_Mouse):

    @staticmethod
    def show():
        HW_Mouse._show()

    @staticmethod
    def hide():
        HW_Mouse._hide()

    @staticmethod
    def setRange(low: int, high: int):
        HW_Mouse._setRange(low, high)

    @staticmethod
    def getEvent(event: MouseEvent):
        HW_Mouse._getEvent(event)

    @staticmethod
    def present() -> bool:
        return HW_Mouse._present()

    @staticmethod
    def suspend():
        HW_Mouse._suspend()

    @staticmethod
    def resume():
        HW_Mouse._resume()
