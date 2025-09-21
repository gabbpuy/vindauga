# -*- coding: utf-8 -*-
from threading import Lock
from vindauga.utilities.platform.events.event_source import EventSource
from .display_adapter import DisplayAdapter


class ConsoleAdapter:
    def __init__(self, display: DisplayAdapter, sources: list[EventSource]):
        self.display = display
        self.sources = sources
        self.lock = Lock()

    def set_clipboard_text(self, text) -> bool:
        return False

    def request_clipboard_text(self, *args) -> str:
        return ''

    def resize(self, width: int, height: int):
        self.display.resize(width, height)

    def is_alive(self) -> bool:
        return True

