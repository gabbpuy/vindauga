# -*- coding: utf-8 -*-
from dataclasses import dataclass
import logging
import time
from platform import platform

from vindauga.types.point import Point

from .adapters.display_adapter import DisplayAdapter
from .flush_screen_algorithm import flush_screen_algorithm
from vindauga.utilities.colours.colour_attribute import ColourAttribute
from vindauga.utilities.screen.screen_cell import ScreenCell

logger = logging.getLogger(__name__)


def negate_attribute(attr: ColourAttribute) -> ColourAttribute:
    negated = ColourAttribute.from_colour_attribute(attr)
    negated._fg, negated._bg = attr._bg, attr._fg
    return negated


class DisplayBuffer:
    @dataclass
    class Range:
        begin: int = 0
        end: int = 0

    def __init__(self, adapter: DisplayAdapter = None):
        self.adapter = adapter
        self._wide_overlapping = platform().lower() != 'windows'
        self.__screen_touched = True
        self.__caret_or_cursor_changed = False

        self._buffer: list[ScreenCell] = []
        self._flush_buffer: list[ScreenCell] = []
        self._row_damage: list[DisplayBuffer.Range] = []

        self.__caret_position = Point(-1, -1)
        self.__new_caret_size = 0
        self.__cursor_position = Point(-1, -1)
        self.__cursor_visible = False

        self.__attr_under_cursor = ColourAttribute()

        self.__limit_fps = True
        self.__flush_delay = 0
        self.__last_flush = 0
        self.__pending_flush = 0
        self.__default_fps = 60

        self.size = Point(0, 0)
        self.caret_size = -1
        self.__caret_size = -1
        self._flushLocked = False

        if self.__limit_fps:
            self.__flush_delay = (1 / 60)

    def free_buffer(self):
        self._buffer.clear()
        self._flush_buffer.clear()
        self._row_damage.clear()
        self.size = Point(0, 0)
        self.__caret_position = Point(-1, -1)
        self.__new_caret_size = 0
        self.__cursor_position = Point(-1, -1)
        self.__cursor_visible = False
        self.__attr_under_cursor = ColourAttribute()
        self.__flush_delay = 0
        self.__last_flush = 0
        self.__pending_flush = 0
        self.caret_size = -1
        self.__caret_size = -1

    def __in_bounds(self, x: int, y: int) -> bool:
        return 0 <= x < self.size.x and 0 <= y < self.size.y

    def __resize_buffer(self):
        buffer_size = self.size.x * self.size.y
        self._buffer.clear()
        self._buffer.extend(ScreenCell() for _ in range(buffer_size))
        self._flush_buffer.clear()
        self._flush_buffer.extend([None] * buffer_size)
        self._row_damage.clear()
        self._row_damage.extend(self.Range(65536, -65536) for _ in range(self.size.y))

    def __set_dirty(self, x: int, y: int, count: int):
        dam = self._row_damage[y]
        if x < dam.begin:
            dam.begin = x
        if x + count - 1 > dam.end:
            dam.end = x + count - 1

    def _validate_cell(self, cell: ScreenCell):
        ch = cell._ch
        # Add bounds checking - only validate if we have at least 2 characters
        if len(ch._text) >= 2 and ch[1] == '\x00':
            c = ch[0]
            if c == '\x00':
                ch[0] = ' '
            elif c < ' ' or 0x7F <= ord(c):
                ch.move_multi_byte_char(c)  # cp_translator.to_packed_utf8(c))

    def __draw_cursor(self):
        if self.__cursor_visible:
            x, y = self.__cursor_position
            if self.__in_bounds(x, y):
                buffer_idx = y * self.size.x + x
                if buffer_idx >= len(self._buffer):
                    logger.error("__draw_cursor: buffer index out of bounds!")
                    return
                    
                cell = self._buffer[buffer_idx]
                if cell._ch.is_wide_char_trail() and x > 0:
                    prev_idx = buffer_idx - 1
                    if prev_idx >= 0 and self._buffer[prev_idx].is_wide():
                        cell = self._buffer[prev_idx]
                        x -= 1
                        
                self.__attr_under_cursor = cell.attr
                cell.attr = negate_attribute(cell.attr)
                self.__set_dirty(x, y, 1)

    def __undraw_cursor(self):
        if self.__cursor_visible:
            x, y = self.__cursor_position
            if self.__in_bounds(x, y):
                buffer_idx = y * self.size.x + x
                           
                cell = self._buffer[buffer_idx]
                if cell._ch.is_wide_char_trail() and x > 0:
                    prev_idx = buffer_idx - 1
                    if prev_idx >= 0 and self._buffer[prev_idx].is_wide():
                        cell = self._buffer[prev_idx]
                        x -= 1
                        
                cell.attr = self.__attr_under_cursor
                self.__set_dirty(x, y, 1)

    def __needs_flush(self) -> bool:
        return any((self.__screen_touched, self.__caret_or_cursor_changed, self.__caret_size != self.__new_caret_size))

    def __time_to_flush(self) -> bool:
        if self.__limit_fps:
            now = time.monotonic()
            flush_time = self.__last_flush + self.__flush_delay
            if flush_time <= now:
                self.__last_flush = now
                self.__pending_flush = 0
            else:
                self.__pending_flush = flush_time
                return False
        return True

    def set_caret_size(self, caret_size: int):
        self.__new_caret_size = caret_size

    def set_caret_position(self, x: int, y: int):
        self.__caret_position.x = x
        self.__caret_position.y = y
        self.__caret_or_cursor_changed = True

    def screen_write(self, x: int, y: int, buf: list[ScreenCell], count: int):
        if self.__in_bounds(x, y):
            _len = min(count, self.size.x - x)
            dst = y * self.size.x + x

            if self._buffer is buf:
                pass
            else:
                for i in range(max(_len, len(buf))):
                    self._buffer[dst + i] = buf[i]

            self.__set_dirty(x, y, _len)
            self.__screen_touched = True

    def clear_screen(self, display: DisplayAdapter):
        display.clear_screen()
        display.flush()
        self.__resize_buffer()

    def redraw_screen(self, display: DisplayAdapter):
        self.__screen_touched = True
        self.__last_flush = 0
        self._flush_buffer.clear()
        self._flush_buffer.extend([None] * len(self._buffer))
        for r in self._row_damage:
            r.begin = 0
            r.end = self.size.x - 1
        self.flush_screen(display)

    def flush_screen(self, display: DisplayAdapter):
        needs_flush = self.__needs_flush()
        time_to_flush = self.__time_to_flush()

        if needs_flush and time_to_flush:
            self.__draw_cursor()
            flush_screen_algorithm(self, display)
            if self.__caret_position.x != -1:
                display.set_caret_position(self.__caret_position)
            self.__undraw_cursor()
            if self.__caret_size != self.__new_caret_size:
                display.set_caret_size(self.__new_caret_size)
            display.flush()
            self.__screen_touched = False
            self.__caret_or_cursor_changed = False
            self.__caret_size = self.__new_caret_size

    def reload_screen_info(self, display: DisplayAdapter) -> list[ScreenCell]:
        self.size = display.reload_screen_info()
        self.__caret_size = -1
        self.__resize_buffer()
        return self._buffer

    def set_cursor_position(self, x: int, y: int):
        pos = Point(x, y)
        if self.__cursor_visible and self.__cursor_position != pos:
            self.__caret_or_cursor_changed = True
        self.__cursor_position = pos

    def set_cursor_visibility(self, visible: bool):
        if self.__cursor_visible != visible:
            self.__caret_or_cursor_changed = True
        self.__cursor_visible = visible

    def time_until_pending_flush_ms(self) -> int:
        if self.__pending_flush == 0:
            return -1

        now = int(time.monotonic() * 1000)
        if self.__pending_flush < now:
            return 0
        return self.__pending_flush - now

    def __len__(self):
        return len(self._buffer)

    def __getitem__(self, item):
        return self._buffer[item]
