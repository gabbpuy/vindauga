# -*- coding: utf-8 -*-
import logging
from typing import Tuple, List, Optional
from PIL import Image, ImageEnhance

from vindauga.screen_driver.colours.colour_attribute import ColourAttribute
from vindauga.screen_driver.colours.colour_rgb import ColourRGB
from vindauga.screen_driver.colours.palettes import find_closest_bios_color

logger = logging.getLogger(__name__)

# ANSI character gradients from darkest to brightest
ASCII_CHARS = " .'-:;!=*#$@"
BLOCK_CHARS = " ░▒▓█"


class ImageToANSIConverter:
    """
    Converts images to ANSI character representation with colors.
    """

    def __init__(self, char_set: str = ASCII_CHARS, use_color: bool = True):
        """
        Initialize converter.
        
        :param char_set: Character set to use for conversion
        :param use_color: Whether to use colors
        """
        self.char_set = char_set
        self.use_color = use_color
        self._color_cache = {}

    def convert_image(self, image_path: str, width: int, height: int,
                      enhance_contrast: float = 1.0) -> Tuple[List[str], List[List[ColourAttribute]]]:
        """
        Convert image to ANSI characters and colors.
        
        :param image_path: Path to image file
        :param width: Target width in characters  
        :param height: Target height in characters
        :param enhance_contrast: Contrast enhancement factor (1.0 = no change)
        :return: Tuple of (character_lines, color_attributes)
        """
        try:
            # Load and process image
            with Image.open(image_path) as img:
                # Convert to RGB if not already
                if img.mode != 'RGB':
                    img = img.convert('RGB')

                # Resize image to target dimensions
                img = img.resize((width, height * 2), Image.Resampling.LANCZOS)  # *2 for aspect ratio

                # Enhance contrast if requested
                if enhance_contrast != 1.0:
                    enhancer = ImageEnhance.Contrast(img)
                    img = enhancer.enhance(enhance_contrast)

                # Convert to character representation
                char_lines = []
                color_lines = []

                for y in range(0, img.height, 2):  # Process 2 vertical pixels per character
                    char_line = []
                    color_line = []

                    for x in range(img.width):
                        # Get pixel colors (average 2 vertical pixels if available)
                        pixel1 = img.getpixel((x, y))
                        if y + 1 < img.height:
                            pixel2 = img.getpixel((x, y + 1))
                            # Average the two pixels
                            avg_pixel = tuple((pixel1[i] + pixel2[i]) // 2 for i in range(3))
                        else:
                            avg_pixel = pixel1

                        # Convert to character based on brightness
                        brightness = sum(avg_pixel) // 3
                        char_index = int((brightness / 255) * (len(self.char_set) - 1))
                        char = self.char_set[char_index]

                        # Convert to color attribute
                        if self.use_color:
                            color_attr = self._rgb_to_color_attribute(avg_pixel)
                        else:
                            color_attr = ColourAttribute.from_bios(0x07)  # Default white on black

                        char_line.append(char)
                        color_line.append(color_attr)

                    char_lines.append(''.join(char_line))
                    color_lines.append(color_line)

                return char_lines, color_lines

        except Exception as e:
            logger.error("Failed to convert image %s: %s", image_path, e)
            # Return fallback pattern
            fallback_char = '▒'
            fallback_color = ColourAttribute.from_bios(0x08)  # Gray
            char_lines = [fallback_char * width for _ in range(height)]
            color_lines = [[fallback_color for _ in range(width)] for _ in range(height)]
            return char_lines, color_lines

    def _rgb_to_color_attribute(self, rgb: Tuple[int, int, int]) -> ColourAttribute:
        """
        Convert RGB color to nearest BIOS color attribute using the sophisticated color system.
        
        :param rgb: RGB color tuple
        :return: ColourAttribute
        """
        # Check cache first
        if rgb in self._color_cache:
            return self._color_cache[rgb]

        # Create ColourRGB object
        colour_rgb = ColourRGB(rgb[0], rgb[1], rgb[2])

        # Find closest BIOS color using the sophisticated system
        nearest_color_index = find_closest_bios_color(colour_rgb)

        # Create color attribute with nearest color as foreground, black background
        color_attr = ColourAttribute.from_bios((nearest_color_index & 0x0F) | (0 << 4))

        # Cache result
        self._color_cache[rgb] = color_attr

        return color_attr

    def convert_from_pil_image(self, img: Image.Image, width: int, height: int,
                               enhance_contrast: float = 1.0) -> Tuple[List[str], List[List[ColourAttribute]]]:
        """
        Convert PIL Image directly to ANSI representation.
        
        :param img: PIL Image object
        :param width: Target width in characters
        :param height: Target height in characters  
        :param enhance_contrast: Contrast enhancement factor
        :return: Tuple of (character_lines, color_attributes)
        """
        # Convert to RGB if not already
        if img.mode != 'RGB':
            img = img.convert('RGB')

        # Resize image to target dimensions
        img = img.resize((width, height * 2), Image.Resampling.LANCZOS)  # *2 for aspect ratio

        # Enhance contrast if requested
        if enhance_contrast != 1.0:
            enhancer = ImageEnhance.Contrast(img)
            img = enhancer.enhance(enhance_contrast)

        # Convert to character representation
        char_lines = []
        color_lines = []

        for y in range(0, img.height, 2):  # Process 2 vertical pixels per character
            char_line = []
            color_line = []

            for x in range(img.width):
                # Get pixel colors (average 2 vertical pixels if available)
                pixel1 = img.getpixel((x, y))
                if y + 1 < img.height:
                    pixel2 = img.getpixel((x, y + 1))
                    # Average the two pixels
                    avg_pixel = tuple((pixel1[i] + pixel2[i]) // 2 for i in range(3))
                else:
                    avg_pixel = pixel1

                # Convert to character based on brightness
                brightness = sum(avg_pixel) // 3
                char_index = int((brightness / 255) * (len(self.char_set) - 1))
                char = self.char_set[char_index]

                # Convert to color attribute
                if self.use_color:
                    color_attr = self._rgb_to_color_attribute(avg_pixel)
                else:
                    color_attr = ColourAttribute.from_bios(0x07)  # Default white on black

                char_line.append(char)
                color_line.append(color_attr)

            char_lines.append(''.join(char_line))
            color_lines.append(color_line)

        return char_lines, color_lines


def create_converter(use_blocks: bool = False, use_color: bool = True) -> ImageToANSIConverter:
    """
    Create an ImageToANSIConverter with appropriate settings.
    
    :param use_blocks: Use block characters instead of ASCII art
    :param use_color: Enable color conversion
    :return: Configured converter
    """
    char_set = BLOCK_CHARS if use_blocks else ASCII_CHARS
    return ImageToANSIConverter(char_set=char_set, use_color=use_color)
