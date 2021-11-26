# -*- coding: utf-8 -*-
import logging
import textwrap

from vindauga.constants.grow_flags import gfFixed

from vindauga.types.draw_buffer import DrawBuffer
from vindauga.types.palette import Palette
from vindauga.types.view import View

logger = logging.getLogger(__name__)


class StaticText(View):

    name = 'StaticText'
    cpStaticText = "\x06"

    def __init__(self, bounds, text):
        super().__init__(bounds)
        self._text = text
        self.growMode |= gfFixed

    def drawEmptyLine(self, y, color):
        b = DrawBuffer()
        b.moveChar(0, ' ', color, self.size.x)
        self.writeLine(0, y, self.size.x, 1, b)

    def draw(self):
        color = self.getColor(1)
        s = self.getText()
        b = DrawBuffer()
        lines = s.splitlines()
        y = 0

        # For each line, wrap at width, until we get to our height
        for line in lines:
            if y > self.size.y:
                return

            center = False
            # line = line.strip()
            if not line:
                # Empty
                self.drawEmptyLine(y, color)
                y += 1
                continue

            # Centered
            if line[0] == '\x03':
                center = True
                line = line[1:]

            # Wrap the lines
            for subLine in textwrap.wrap(line, self.size.x):
                if center:
                    subLine = subLine.center(self.size.x, ' ')
                else:
                    subLine = subLine.ljust(self.size.x)
                b.moveStr(0, subLine, color)
                self.writeLine(0, y, self.size.x, 1, b)
                y += 1
                if y > self.size.y:
                    return

        # Draw the rest of the empty lines
        b.moveChar(0, ' ', color, self.size.x)
        for yy in range(y, self.size.y + 1):
            self.writeLine(0, yy, self.size.x, 1, b)

    def getPalette(self):
        palette = Palette(self.cpStaticText)
        return palette

    def getText(self):
        return self._text or ''
