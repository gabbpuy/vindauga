# -*- coding: utf-8 -*-
from vindauga.types.point import Point


class DisplayAdapter:
    def reload_screen_info(self):
        return Point(0, 0)

    def get_colour_count(self):
        return 0

    def get_font_size(self):
        return Point(0, 0)

    def write_cell(self, pos, text, attr, double_width=False):
        pass

    def set_caret_position(self, pos):
        pass

    def set_caret_size(self, size: int):
        pass

    def clear_screen(self):
        pass

    def flush(self):
        pass

    def resize(self, width: int, height: int):
        pass
