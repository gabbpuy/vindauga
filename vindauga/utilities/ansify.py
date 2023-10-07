# -*- coding: utf-8 -*-
from dataclasses import dataclass, field
import itertools
import logging

from PIL import Image

from vindauga.types.display import Display
from vindauga.types.draw_buffer import DrawBuffer
from vindauga.types.rect import Rect
from vindauga.types.screen import Screen
from vindauga.utilities.colours.colours import colourFindRGB, colour_256to16
from vindauga.widgets.desktop import Desktop

logger = logging.getLogger(__name__)


@dataclass
class BitMap:
    pattern: int
    charOrd: int
    char: str


BLOCK = BitMap(0x0000ffff, 0x2584, '▄')  # lower 1/2
# BLOCK = BitMap(0x5a5a5a5a, 0x2592, '▒')


@dataclass
class Colour:
    r: int = 0
    g: int = 0
    b: int = 0

    def __floordiv__(self, other) -> 'Colour':
        r = self.r // other
        g = self.g // other
        b = self.b // other
        return Colour(r, g, b)

    def __ifloordiv__(self, other) -> 'Colour':
        self.r //= other
        self.g //= other
        self.b //= other
        return self

    def __add__(self, other) -> 'Colour':
        r = self.r + other[0]
        g = self.g + other[1]
        b = self.b + other[2]
        return Colour(r, g, b)

    def __iadd__(self, other) -> 'Colour':
        self.r += other[0]
        self.g += other[1]
        self.b += other[2]
        return self

    def __iter__(self):
        yield from (self.r, self.g, self.b)


@dataclass
class CharData:
    fgColour: Colour = field(default_factory=Colour)
    bgColour: Colour = field(default_factory=Colour)
    char: str = BLOCK.char


@dataclass
class Size:
    width: int
    height: int

    def scaled(self, scale):
        return Size(int(self.width * scale), int(self.height * scale))

    def fittedWithin(self, container):
        scale = min(container.width / self.width, container.height / self.height)
        return self.scaled(scale)


def openFile(filename):
    im = Image.open(filename)
    im.draft("RGB", im.size)
    return im


def getBitmapCharData(bitmap: BitMap, input_image: Image, x0: int, y0: int) -> CharData:
    result = CharData()
    result.char = bitmap.char

    fgCount = 0
    bgCount = 0
    mask = 0x80000000

    for y, x in itertools.product(range(y0, y0 + 8), range(x0, x0 + 4)):
        if bitmap.pattern & mask:
            avg = result.fgColour
            fgCount += 1
        else:
            avg = result.bgColour
            bgCount += 1

        avg += input_image[x, y]
        mask >>= 1

    if bgCount:
        result.bgColour //= bgCount

    if fgCount:
        result.fgColour //= fgCount
    return result


def emitImage256(image):
    w, h = image.size
    pixels = image.load()
    lines = []
    for y in range(0, h - 8, 8):
        buffer = DrawBuffer()
        buffer.moveChar(0, Desktop.DEFAULT_BACKGROUND, 0, w // 4 + 1)
        for i, x in enumerate(range(0, w - 4, 4)):
            charData = getBitmapCharData(BLOCK, pixels, x, y)
            bg = colourFindRGB(*charData.bgColour)
            fg = colourFindRGB(*charData.fgColour)
            pair = (fg << 8 | bg)
            buffer[i] = pair << 16 | ord(charData.char)
        lines.append(buffer)
    return lines


def emitImage16(image):
    w, h = image.size
    pixels = image.load()
    lines = []
    for y in range(0, h - 8, 8):
        buffer = DrawBuffer()
        buffer.moveChar(0, Desktop.DEFAULT_BACKGROUND, 0, w // 4 + 1)
        for i, x in enumerate(range(0, w - 4, 4)):
            charData = getBitmapCharData(BLOCK, pixels, x, y)
            bg = colour_256to16(colourFindRGB(*charData.bgColour))
            fg = colour_256to16(colourFindRGB(*charData.fgColour))
            pair = fg << 4 | bg
            buffer[i] = pair << 16 | ord(charData.char)
        lines.append(buffer)
    return lines


def wallpaper(filename, bounds: Rect):
    maxWidth = bounds.width * 4
    maxHeight = bounds.height * 8

    img = openFile(filename).convert('RGB')
    iw, ih = img.size
    size = Size(iw, ih)
    if iw > maxWidth or ih > maxHeight:
        size = size.fittedWithin(Size(maxWidth, maxHeight))
        img = img.resize((size.width, size.height))
    if Screen.screen.screenMode != Display.smCO256:
        return size.width // 4, size.height // 8, emitImage16(img)
    return size.width // 4, size.height // 8, emitImage256(img)
