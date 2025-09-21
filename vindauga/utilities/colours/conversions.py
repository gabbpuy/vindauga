# -*- coding: utf-8 -*-
from dataclasses import dataclass

from .colour_bios import ColourBIOS
from .colour_rgb import ColourRGB
from .colour_xterm import ColourXTerm

HUE_PRECISION = 32
HUE_MAX = 6 * HUE_PRECISION


@dataclass
class HCL:
    h: int
    c: int
    lightness: int


def pack(r: int, g: int, b: int):
    return (r << 8 | g) << 8 | b


def XTerm16toBIOS(idx: int) -> ColourBIOS:
    """
    Convert XTerm16 index to BIOS color (they use the same format).
    """
    return ColourBIOS(idx)


def BIOS_to_XTerm16(bios_color) -> int:
    """
    Convert BIOS color to XTerm16 index with proper mapping.
    """
    bios_to_xterm = [0, 4, 2, 6, 1, 5, 3, 7, 8, 12, 10, 14, 9, 13, 11, 15]
    
    from .colour_bios import ColourBIOS
    if isinstance(bios_color, ColourBIOS):
        idx = int(bios_color) & 0x0F
    elif isinstance(bios_color, int):
        idx = bios_color & 0x0F
    else:
        idx = int(bios_color) & 0x0F
    
    return bios_to_xterm[idx]


def RGB_to_HCL(r: int, g: int, b: int) -> HCL:
    x_min = min(min(r, g), b)
    x_max = max(max(r, g), b)
    v = x_max
    L = (x_max + x_min) // 2
    C = x_max - x_min
    H = 0
    if C:
        if v == r:
            H = (HUE_PRECISION * (g - b)) // C
        elif v == g:
            H = (HUE_PRECISION * (b - r)) // C + 2 * HUE_PRECISION
        elif v == b:
            H = (HUE_PRECISION * (r - g)) // C + 4 * HUE_PRECISION

        if H < 0:
            H += HUE_MAX
        elif H >= HUE_MAX:
            H -= HUE_MAX

    return HCL(H & 0xFF, C & 0xFF, L & 0xFF)


def u8(d: float) -> int:
    return int(d * 255) & 0xFF


def RGB_toXTerm16(r: int, g: int, b: int) -> int:
    c = RGB_to_HCL(r, g, b)
    if c.c >= 12:  # Color if Chroma >= 12
        normal = [0x1, 0x3, 0x2, 0x6, 0x4, 0x5]
        bright = [0x9, 0xB, 0xA, 0xE, 0xC, 0xD]
        if c.h < HUE_MAX - HUE_PRECISION // 2:
            index = (c.h + HUE_PRECISION // 2) // HUE_PRECISION
        else:
            index = (c.h - (HUE_MAX - HUE_PRECISION // 2)) // HUE_PRECISION
        index = index % 6

        if c.lightness < u8(0.5):
            return normal[index]
        if c.lightness < u8(0.925):
            return bright[index]
        return 15
    else:
        if c.lightness < u8(0.25):
            return 0
        if c.lightness < u8(0.625):
            return 8
        if c.lightness < u8(0.875):
            return 7
        return 15


def RGB_toXTerm16Impl(c):
    return RGB_toXTerm16(c.r, c.g, c.b)


def RGB(c: ColourRGB) -> int:
    return RGB_toXTerm16Impl(c)


def RGB_toBIOS(rgb: ColourRGB) -> ColourBIOS:
    return XTerm16toBIOS(RGB_toXTerm16(rgb.r, rgb.g, rgb.b))


def XTerm256toRGB(idx: int) -> ColourRGB:
    return ColourRGB.from_int(XTerm256toRGB_LUT[idx])


def XTerm256toXTerm16(idx: int) -> ColourXTerm:
    return ColourXTerm(XTerm256toXTerm16LUT[idx])


def RGB_toXTerm256(rgb: ColourRGB) -> int:
    """
    Convert RGB color to closest XTerm 256 color index.

    :param rgb: RGB color
    """

    def scale_to_6cube(c: int) -> int:
        """
        Scale 0-255 RGB component to 0-5 for 6x6x6 cube.
        """
        if c < 75:
            return 0
        return min(5, (c - 35) // 40)

    def cnv_colour(r: int, g: int, b: int) -> int:
        """
        Convert RGB to 6x6x6 cube index.
        """
        r6 = scale_to_6cube(r)
        g6 = scale_to_6cube(g)
        b6 = scale_to_6cube(b)
        return 16 + r6 * 36 + g6 * 6 + b6

    def cnv_gray(level: int) -> int:
        """
        Convert grayscale level to grayscale ramp index.
        """
        if level < 8:
            return 16  # Use color cube black
        if level > 238:
            return 231  # Use color cube white
        return 232 + (level - 8) // 10

    # Try color cube first
    color_idx = cnv_colour(rgb.r, rgb.g, rgb.b)

    # Check if it's better represented as grayscale
    min_val = min(rgb.r, rgb.g, rgb.b)
    max_val = max(rgb.r, rgb.g, rgb.b)
    chroma = max_val - min_val

    if chroma < 12:  # Low chroma, try grayscale
        avg = (rgb.r + rgb.g + rgb.b) // 3
        gray_idx = cnv_gray(avg)

        # Compare distances to decide between color and gray
        color_rgb = XTerm256toRGB(color_idx)
        gray_rgb = XTerm256toRGB(gray_idx)

        color_dist = (rgb.r - color_rgb.r) ** 2 + (rgb.g - color_rgb.g) ** 2 + (rgb.b - color_rgb.b) ** 2
        gray_dist = (rgb.r - gray_rgb.r) ** 2 + (rgb.g - gray_rgb.g) ** 2 + (rgb.b - gray_rgb.b) ** 2

        return gray_idx if gray_dist < color_dist else color_idx

    return color_idx


def initXTerm256toXTerm16LUT():
    res = [0] * 256
    for i in range(16):
        res[i] = i

    for i in range(6):
        R = 55 + i * 40 if i else 0
        for j in range(6):
            G = 55 + j * 40 if j else 0
            for k in range(6):
                B = 55 + k * 40 if k else 0
                idx16 = RGB_toXTerm16(R, G, B)
                res[16 + (i * 6 + j) * 6 + k] = idx16

    for i in range(24):
        L = i * 10 + 8
        idx16 = RGB_toXTerm16(L, L, L)
        res[232 + i] = idx16
    return res


def initXTerm256toRGB_LUT():
    res = [0] * 256
    for i in range(6):
        R = 55 + i * 40 if i else 0
        for j in range(6):
            G = 55 + j * 40 if j else 0
            for k in range(6):
                B = 55 + k * 40 if k else 0
                res[16 + (i * 6 + j) * 6 + k] = pack(R, G, B)

    for i in range(24):
        L = i * 10 + 8
        res[232 + i] = pack(L, L, L)

    return res


XTerm256toXTerm16LUT = initXTerm256toXTerm16LUT()
XTerm256toRGB_LUT = initXTerm256toRGB_LUT()
