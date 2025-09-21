# -*- coding: utf-8 -*-
import itertools
import logging
from pathlib import Path
from typing import Optional, List

from vindauga.types.rect import Rect
from vindauga.widgets.background import Background
from vindauga.utilities.support.ansify import wallpaper
from vindauga.widgets.desktop import Desktop

logger = logging.getLogger(__name__)


class WallpaperBackground(Background):
    """
    A Background widget that displays an image converted to ANSI characters and colors.
    
    This widget extends the basic Background class to show an image as wallpaper
    by converting it to ANSI characters with appropriate colors.
    """

    name = 'WallpaperBackground'

    def __init__(self, bounds: Rect, image_path: str):
        """
        Initialize wallpaper background.
        
        :param bounds: Widget bounds
        :param image_path: Path to image file  
        """
        super().__init__(bounds, Desktop.DEFAULT_BACKGROUND)
        self._image_path = str(Path(image_path).resolve())
        # Cached image data
        self._char_lines: Optional[List[str]] = None
        self._drawLock = False
        # Load image on initialization
        self._load_image()

    def _load_image(self):
        logger.info("Loading wallpaper image: %s (size: %dx%d)",
                    self._image_path, self.size.x, self.size.y)
        _w, _h, self._char_lines = wallpaper(self._image_path, self.getBounds(), self)

    def draw(self):
        if self._drawLock:
            return
        for y, line in enumerate(itertools.islice(self._char_lines, 0, max(len(self._char_lines), self.size.y))):
            self.writeLine(0, y, self.size.x, 1, line)

    def reload_image(self):
        """
        Force reload of the image (useful if file changed).
        """
        self._load_image()
        self.drawView()

    def changeBounds(self, bounds: Rect):
        self._drawLock = True
        try:
            super().changeBounds(bounds)
        finally:
            self._drawLock = False
        self.reload_image()

    def set_image(self, image_path: str):
        """
        Change the wallpaper image.
        
        :param image_path: New image path
        """
        self._image_path = str(Path(image_path).resolve())
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
