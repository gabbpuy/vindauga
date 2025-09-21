# -*- coding: utf-8 -*-
from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from vindauga.utilities.platform.adapters.display_adapter import DisplayAdapter
from vindauga.utilities.colours.colour_attribute import ColourAttribute
from vindauga.utilities.screen.cell_char import CellChar
from vindauga.utilities.screen.screen_cell import ScreenCell
from vindauga.types.point import Point

if TYPE_CHECKING:
    from vindauga.utilities.platform.display_buffer import DisplayBuffer


logger = logging.getLogger(__name__)


class FlushScreenAlgorithm:
    def __init__(self, display: DisplayBuffer, adapter: DisplayAdapter):
        self.display = display
        self.adapter = adapter
        self.cell: ScreenCell = None
        self.damage: DisplayBuffer.Range = None
        self.x: int = 0
        self.y: int = 0
        self.row_offset: int = 0
        self.size = Point(0, 0)

    def is_trail(self, cell: ScreenCell) -> bool:
        return cell._ch.is_wide_char_trail()

    def is_wide(self, cell: ScreenCell) -> bool:
        return cell.is_wide()

    def cell_at(self, x: int) -> ScreenCell:
        return self.display._buffer[self.row_offset + x]

    def get_cell(self):
        index = self.row_offset + self.x
        self.cell = self.display[index]
        self.display._validate_cell(self.cell)

    def cell_dirty(self) -> bool:
        cell_index = self.row_offset + self.x
        return self.cell != self.display._flush_buffer[cell_index]

    def commit_dirty(self):
        cell_index = self.row_offset + self.x
        self.display._flush_buffer[cell_index] = self.cell

    def wide_can_overlap(self):
        return self.display._wide_overlapping

    def process_cell(self):
        if self.is_wide(self.cell):
            self.handle_wide_char_spill()
            return
        if self.is_trail(self.cell):
            self.handle_trail()
            return
        self.write_cell()

    def _write_cell(self, ch: CellChar, attr: ColourAttribute, wide: bool):
        self.adapter.write_cell(Point(self.x, self.y), ch.get_text(), attr, wide)

    def write_cell(self):
        self._write_cell(self.cell._ch, self.cell.attr, self.cell.is_wide())

    def write_space(self, *args):
        ch: CellChar = CellChar()
        ch.move_char(' ')
        self._write_cell(ch, self.cell.attr, False)

    def handle_wide_char_spill(self):
        width = int(self.cell.is_wide())
        attr = self.cell.attr

        if self.x + width < self.size.x:
            self.write_cell()
        else:
            self.write_space()
            while width and self.x + 1 < self.size.x:
                width -= 1
                self.x += 1
                self.get_cell()
                if not self.is_trail(self.cell):
                    self.x -= 1
                    return
                self.write_space()
            return
        w_begin = self.x
        while width and self.x + 1 < self.size.x:
            width -= 1
            self.x += 1
            self.get_cell()
            self.commit_dirty()
            if not self.is_trail(self.cell):
                if self.wide_can_overlap():
                    self.write_cell()
                else:
                    w_end = self.x
                    self.x = w_begin
                    while True:
                        self.get_cell()
                        self.write_space()
                        self.x += 1
                        if self.x >= w_end:
                            break
                    self.get_cell()
                    self.write_cell()
                return
        if self.x + 1 < self.size.x:
            self.x += 1
            self.get_cell()
            if attr != self.cell.attr:
                self.commit_dirty()
                self.process_cell()
            else:
                self.x -= 1

    def handle_trail(self):
        attr = self.cell.attr
        if self.x > 0:
            self.x -= 1
            self.get_cell()
            if self.cell.is_wide():
                self.handle_wide_char_spill()
                return
            self.x += 1
            self.get_cell()

        while True:
            self.commit_dirty()
            self.write_space()
            self.x += 1
            if self.x < self.size.x:
                self.get_cell()
            else:
                return
            if not self.is_trail(self.cell):
                break

        if self.x > self.damage.end and attr != self.cell.attr:
            self.process_cell()
        else:
            self.x -= 1

    def __call__(self):
        self.size = self.display.size
        self.row_offset = 0
        for self.y in range(self.size.y):
            self.damage = self.display._row_damage[self.y]
            if self.damage.begin <= self.damage.end:
                self.x = self.damage.begin
                wide_spill_before = (
                    not self.wide_can_overlap() and 0 < self.x and self.is_wide(self.cell_at(self.x - 1))
                )
                while self.x <= self.damage.end:
                    self.get_cell()
                    if self.cell_dirty() or self.is_trail(self.cell):
                        if wide_spill_before:
                            self.x -= 1
                            self.get_cell()
                            wide_spill_before = False
                        self.commit_dirty()
                        self.process_cell()
                    else:
                        wide_spill_before = not self.wide_can_overlap() and self.is_wide(self.cell)
                    self.x += 1
                if self.x < self.size.x:
                    self.get_cell()
                    if self.is_trail(self.cell):
                        self.handle_trail()

            # Reset damage range
            self.display._row_damage[self.y] = self.display.__class__.Range(65536, -65536)
            self.row_offset += self.size.x


def flush_screen_algorithm(display: DisplayBuffer, adapter: DisplayAdapter):
    FlushScreenAlgorithm(display, adapter)()
