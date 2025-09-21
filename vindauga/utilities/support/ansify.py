# -*- coding: utf-8 -*-
from __future__ import annotations
from dataclasses import dataclass
import logging

from PIL import Image

from vindauga.utilities.colours.colour_attribute import ColourAttribute
from vindauga.utilities.colours.desired_colour import DesiredColour
from vindauga.types.draw_buffer import DrawBuffer
from vindauga.types.rect import Rect
from vindauga.types.view import View
from vindauga.widgets.desktop import Desktop

logger = logging.getLogger(__name__)


@dataclass
class BitMap:
    pattern: int
    charOrd: int
    char: str


BLOCK = BitMap(0x0000ffff, 0x2584, '▄')  # lower 1/2

# Color steps
COLOR_STEPS = [0, 0x5f, 0x87, 0xaf, 0xd7, 0xff]

# Grayscale steps
GRAYSCALE_STEPS = [
    0x08, 0x12, 0x1c, 0x26, 0x30, 0x3a, 0x44, 0x4e, 0x58, 0x62, 0x6c, 0x76,
    0x80, 0x8a, 0x94, 0x9e, 0xa8, 0xb2, 0xbc, 0xc6, 0xd0, 0xda, 0xe4, 0xee
]


def find_256_color_index(r, g, b):
    """
    Find the nearest 256 color index for an RGB color
    """
    if r == g and g == b:  # Grayscale
        if r < 8:
            return 16
        if r > 248:
            return 231

        # Find closest grayscale color
        for i, gray in enumerate(GRAYSCALE_STEPS):
            if r <= gray:
                return 232 + i
        return 231

    # Find closest RGB color
    ri = 0
    gi = 0
    bi = 0

    for i in range(len(COLOR_STEPS)):
        if r >= COLOR_STEPS[i]:
            ri = i
        if g >= COLOR_STEPS[i]:
            gi = i
        if b >= COLOR_STEPS[i]:
            bi = i

    return 16 + 36 * ri + 6 * gi + bi


def openFile(filename):
    im = Image.open(filename)
    im.draft("RGB", im.size)
    return im


def wallpaper(filename, bounds: Rect, view: View):
    img = openFile(filename)
    iw, ih = img.size
    width, height = bounds.width, bounds.height
    height *= 2
    img_ratio = iw / ih
    term_ratio = width / height
    if img_ratio > term_ratio:
        new_width = width
        new_height = int(width / img_ratio)
    else:
        new_height = height
        new_width = int(height * img_ratio)

    offset = (width - new_width) // 2

    img = img.resize((new_width, new_height))
    if img.mode != 'RGBA':
        img = img.convert('RGBA')
    pixels = img.load()
    logger.info('Creating wallpaper of (%sx%s)', new_width, new_height)
    lines = []
    v_align = (height - new_height) // 4
    colour = view.getColor(0x01) & 0xFF

    for y in range(v_align):
        buffer = DrawBuffer()
        buffer.moveChar(0, Desktop.DEFAULT_BACKGROUND, colour, width)
        lines.append(buffer)

    for y in range(0, new_height, 2):
        buffer = DrawBuffer()
        buffer.moveChar(0, Desktop.DEFAULT_BACKGROUND, colour, width)
        for x in range(new_width):
            upper_pixel = pixels[x, y]
            if y + 1 >= new_height:
                lower_pixel = (0, 0, 0)
            else:
                lower_pixel = pixels[x, y + 1]
            # Skip fully transparent pixels...
            if upper_pixel == lower_pixel and len(upper_pixel) == 4 and not upper_pixel[-1]:
                continue
            lower_pixel = lower_pixel[:-1]
            upper_pixel = upper_pixel[:-1]
            bg = find_256_color_index(*upper_pixel)
            fg = find_256_color_index(*lower_pixel)
            fg = DesiredColour.from_xterm(fg)
            bg = DesiredColour.from_xterm(bg)
            buffer.data[x + offset].char = BLOCK.char
            buffer.data[x + offset].attr = ColourAttribute.from_desired_colors(fg, bg)
        lines.append(buffer)

    for y in range(v_align + 1):
        buffer = DrawBuffer()
        buffer.moveChar(0, Desktop.DEFAULT_BACKGROUND, colour, width)
        lines.append(buffer)

    return new_width, new_height, lines
