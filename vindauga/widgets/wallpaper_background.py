# -*- coding: utf-8 -*-
import logging
from pathlib import Path
from typing import Optional, List

from vindauga.constants.event_codes import evBroadcast
from vindauga.constants.command_codes import cmWallpaperToggleBlocks, cmWallpaperToggleColor
from vindauga.events.event import Event
from vindauga.types.draw_buffer import DrawBuffer
from vindauga.types.rect import Rect
from vindauga.widgets.background import Background
from vindauga.utilities.image_to_ansi import create_converter
from vindauga.screen_driver.colours.colour_attribute import ColourAttribute

logger = logging.getLogger(__name__)


class WallpaperBackground(Background):
    """
    A Background widget that displays an image converted to ANSI characters and colors.
    
    This widget extends the basic Background class to show an image as wallpaper
    by converting it to ANSI characters with appropriate colors.
    """

    name = 'WallpaperBackground'
    cpBackground = "\x01"

    def __init__(self, bounds: Rect, image_path: str, pattern: str = '▒',
                 use_blocks: bool = False, use_color: bool = True,
                 enhance_contrast: float = 1.2):
        """
        Initialize wallpaper background.
        
        :param bounds: Widget bounds
        :param image_path: Path to image file  
        :param pattern: Fallback pattern character
        :param use_blocks: Use block characters instead of ASCII art
        :param use_color: Enable color conversion
        :param enhance_contrast: Contrast enhancement factor
        """
        super().__init__(bounds, pattern)

        self._image_path = str(Path(image_path).resolve())
        self._use_blocks = use_blocks
        self._use_color = use_color
        self._enhance_contrast = enhance_contrast

        # Cached image data
        self._char_lines: Optional[List[str]] = None
        self._color_lines: Optional[List[List[ColourAttribute]]] = None
        self._image_width = 0
        self._image_height = 0
        self._last_size = None

        # Load image on initialization
        self._load_image()

    def _load_image(self):
        """
        Load and convert the image to ANSI representation.
        """
        try:
            # Check if size changed or first load
            current_size = (self.size.x, self.size.y)
            if self._last_size == current_size and self._char_lines is not None:
                return  # Use cached data

            logger.info("Loading wallpaper image: %s (size: %dx%d)",
                        self._image_path, self.size.x, self.size.y)

            # Create converter
            converter = create_converter(use_blocks=self._use_blocks, use_color=self._use_color)

            # Convert image
            self._char_lines, self._color_lines = converter.convert_image(
                self._image_path,
                self.size.x,
                self.size.y,
                enhance_contrast=self._enhance_contrast
            )

            self._image_width = len(self._char_lines[0]) if self._char_lines else 0
            self._image_height = len(self._char_lines)
            self._last_size = current_size
        except Exception as e:
            logger.error("Failed to load wallpaper image %s: %s", self._image_path, e)
            # Use fallback
            self._char_lines = None
            self._color_lines = None

    def draw(self):
        """
        Draw the wallpaper background.
        """
        # Reload image if size changed
        self._load_image()

        b = DrawBuffer()

        if self._char_lines and self._color_lines:
            # Calculate centering offsets
            offset_x = max(0, (self.size.x - self._image_width) // 2)
            offset_y = max(0, (self.size.y - self._image_height) // 2)

            # Draw line by line
            for y in range(self.size.y):
                # Clear the line first
                b.clear()

                image_y = y - offset_y

                if 0 <= image_y < self._image_height:
                    # Draw image line
                    char_line = self._char_lines[image_y]
                    color_line = self._color_lines[image_y]

                    for x in range(self.size.x):
                        image_x = x - offset_x

                        if 0 <= image_x < len(char_line):
                            # Use image character and color
                            char = char_line[image_x]
                            color = color_line[image_x]
                        else:
                            # Use pattern for areas outside image
                            char = self._pattern
                            color = self.getColor(0x01)

                        b.moveChar(x, char, color, 1)
                else:
                    # Fill with pattern
                    color = self.getColor(0x01)
                    b.moveChar(0, self._pattern, color, self.size.x)

                self.writeLine(0, y, self.size.x, 1, b)
        else:
            # Fallback to pattern background
            super().draw()

    def handleEvent(self, event: Event):
        """
        Handle broadcast events for wallpaper controls.
        """
        super().handleEvent(event)

        if event.what == evBroadcast:
            command = event.message.command

            if command == cmWallpaperToggleBlocks:
                current_blocks = self._use_blocks
                self.set_converter_options(use_blocks=not current_blocks)
                self.clearEvent(event)

            elif command == cmWallpaperToggleColor:
                current_color = self._use_color
                self.set_converter_options(use_color=not current_color)
                self.clearEvent(event)

    def reload_image(self):
        """
        Force reload of the image (useful if file changed).
        """
        self._last_size = None  # Force reload
        self._load_image()
        self.drawView()

    def set_image(self, image_path: str):
        """
        Change the wallpaper image.
        
        :param image_path: New image path
        """
        self._image_path = str(Path(image_path).resolve())
        self._last_size = None  # Force reload
        self._load_image()
        self.drawView()

    def set_converter_options(self, use_blocks: bool = None, use_color: bool = None,
                              enhance_contrast: float = None):
        """
        Update converter options and reload image.
        
        :param use_blocks: Use block characters
        :param use_color: Enable colors
        :param enhance_contrast: Contrast enhancement
        """
        changed = False

        if use_blocks is not None and use_blocks != self._use_blocks:
            self._use_blocks = use_blocks
            changed = True

        if use_color is not None and use_color != self._use_color:
            self._use_color = use_color
            changed = True

        if enhance_contrast is not None and enhance_contrast != self._enhance_contrast:
            self._enhance_contrast = enhance_contrast
            changed = True

        if changed:
            self._last_size = None  # Force reload
            self._load_image()
            self.drawView()


def create_wallpaper_background(bounds: Rect, image_path: str, **kwargs) -> WallpaperBackground:
    """
    Create a WallpaperBackground with common defaults.
    
    :param bounds: Widget bounds
    :param image_path: Path to image file
    :param kwargs: Additional options for WallpaperBackground
    :return: Configured wallpaper background
    """
    return WallpaperBackground(bounds, image_path, **kwargs)
