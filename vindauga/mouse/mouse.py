# -*- coding: utf-8 -*-
from vindauga.events.mouse_event import MouseEvent
from vindauga.screen_driver.hardware_info import hardware_info


class HardwareMouse:
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
        """
        Get mouse event
        """
        event.buttons = 0
        event.wheel = 0
        event.where.x = 0
        event.where.y = 0
        event.eventFlags = 0

    @staticmethod
    def _present() -> bool:
        return HardwareMouse._buttonCount != 0

    @staticmethod
    def _suspend():
        HardwareMouse._hide()
        HardwareMouse._buttonCount = 0

    @staticmethod
    def _resume():
        HardwareMouse._buttonCount = hardware_info.getButtonCount()
        HardwareMouse._show()

    @staticmethod
    def _inhibit():
        HardwareMouse.__noMouse = True

    @staticmethod
    def registerHandler():
        if not HardwareMouse._present():
            return
        HardwareMouse.__handlerInstalled = True

    def __del__(self):
        HardwareMouse._suspend()


class Mouse(HardwareMouse):

    @staticmethod
    def show():
        HardwareMouse._show()

    @staticmethod
    def hide():
        HardwareMouse._hide()

    @staticmethod
    def setRange(low: int, high: int):
        HardwareMouse._setRange(low, high)

    @staticmethod
    def getEvent(event: MouseEvent):
        HardwareMouse._getEvent(event)

    @staticmethod
    def present() -> bool:
        return HardwareMouse._present()

    @staticmethod
    def suspend():
        HardwareMouse._suspend()

    @staticmethod
    def resume():
        HardwareMouse._resume()
