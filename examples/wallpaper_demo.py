# -*- coding: utf-8 -*-
import logging
from pathlib import Path

from vindauga.constants.buttons import bfDefault
from vindauga.constants.command_codes import hcNoContext, cmOK, cmWallpaperToggleBlocks, cmWallpaperToggleColor
from vindauga.constants.event_codes import evCommand, evBroadcast
from vindauga.constants.keys import kbAltA, kbAltW, kbAltB, kbAltC
from vindauga.constants.option_flags import ofCentered
from vindauga.events.event import Event
from vindauga.misc.message import message

from vindauga.menus.menu_bar import MenuBar
from vindauga.menus.menu_item import MenuItem
from vindauga.menus.sub_menu import SubMenu

from vindauga.types.rect import Rect

from vindauga.widgets.application import Application
from vindauga.widgets.button import Button
from vindauga.widgets.desktop import Desktop
from vindauga.widgets.dialog import Dialog
from vindauga.widgets.static_text import StaticText
from vindauga.widgets.wallpaper_background import WallpaperBackground

logger = logging.getLogger('vindauga.wallpaper_demo')

# Command codes
cmAbout = 100


class WallpaperDemo(Application):
    """
    Demo application showing wallpaper background functionality.
    """

    def __init__(self):
        super().__init__()
        self.wallpaper_desktop = None

    def initMenuBar(self, bounds: Rect) -> MenuBar:
        bounds.bottomRight.y = bounds.topLeft.y + 1

        aboutMenu = SubMenu('~A~bout', 0, hcNoContext) + MenuItem('~A~bout Demo', cmAbout, kbAltA, hcNoContext)

        wallpaperMenu = (SubMenu('~W~allpaper', kbAltW, hcNoContext) +
                         MenuItem('Toggle ~B~locks', cmWallpaperToggleBlocks, kbAltB, hcNoContext) +
                         MenuItem('Toggle ~C~olor', cmWallpaperToggleColor, kbAltC, hcNoContext))

        return MenuBar(bounds, aboutMenu + wallpaperMenu)

    def initDesktop(self, bounds: Rect) -> Desktop:
        bounds.topLeft.y += 1
        bounds.bottomRight.y -= 1
        self.wallpaper_desktop = WallpaperDesktop(bounds)
        return self.wallpaper_desktop

    def handleEvent(self, event: Event):
        super().handleEvent(event)
        if event.what == evCommand:
            command = event.message.command

            if command == cmAbout:
                self._show_about_dialog()
                self.clearEvent(event)
            elif command == cmWallpaperToggleBlocks:
                self._toggle_blocks()
                self.clearEvent(event)
            elif command == cmWallpaperToggleColor:
                self._toggle_color()
                self.clearEvent(event)

    def _show_about_dialog(self):
        """Show about dialog."""
        d = Dialog(Rect(0, 0, 45, 14), 'About Wallpaper Demo')
        d.options |= ofCentered
        d.insert(StaticText(Rect(2, 2, 43, 10),
                            "\x03Vindauga Wallpaper Demo\n\n"
                            "\x03This demo shows how to use images\n"
                            "\x03as wallpapers by converting them to\n"
                            "\x03ANSI characters and colors.\n\n"
                            "\x03Features:\n"
                            "\x03• ASCII and block character modes\n"
                            "\x03• Color and monochrome rendering\n"
                            "\x03• Automatic image resizing"))
        d.insert(Button(Rect(15, 11, 30, 13), "~O~k", cmOK, bfDefault))
        self.desktop.execView(d)
        self.destroy(d)

    def _find_wallpaper_background(self):
        """Find WallpaperBackground in desktop children."""
        if not self.desktop:
            return None

        # Walk through desktop children looking for WallpaperBackground
        current = self.desktop.first
        while current:
            logger.info("Checking child: %s", type(current).__name__)
            if isinstance(current, WallpaperBackground):
                logger.info("Found WallpaperBackground: %s", current)
                return current
            current = current.next

        logger.warning("No WallpaperBackground found in desktop children")
        return None

    def _toggle_blocks(self):
        """Toggle between ASCII and block characters."""
        logger.info("Broadcasting toggle blocks command")
        wallpaper_bg = self._find_wallpaper_background()
        if wallpaper_bg:
            logger.info("Sending toggle blocks message to WallpaperBackground")
            message(wallpaper_bg, evBroadcast, cmWallpaperToggleBlocks, None)
        else:
            logger.warning("No WallpaperBackground found to send message to")

    def _toggle_color(self):
        """Toggle color rendering."""
        logger.info("Broadcasting toggle color command")
        wallpaper_bg = self._find_wallpaper_background()
        if wallpaper_bg:
            logger.info("Sending toggle color message to WallpaperBackground")
            message(wallpaper_bg, evBroadcast, cmWallpaperToggleColor, None)
        else:
            logger.warning("No WallpaperBackground found to send message to")


class WallpaperDesktop(Desktop):
    """
    Desktop with wallpaper background.
    """

    def initBackground(self, bounds: Rect):
        """Initialize wallpaper background."""
        # Look for a sample image in the examples directory
        examples_dir = Path(__file__).parent

        # Try to find any image file in examples directory
        image_extensions = ['.png', '.jpg', '.jpeg', '.gif', '.bmp', '.tiff']
        sample_image = None

        for ext in image_extensions:
            for img_file in examples_dir.glob(f'*{ext}'):
                sample_image = str(img_file)
                break
            if sample_image:
                break

        # If no image found, create a simple test pattern
        if not sample_image:
            logger.warning("No sample image found in examples directory")
            sample_image = self._create_test_image(examples_dir / "test_pattern.png")

        try:
            wallpaper_bg = WallpaperBackground(
                bounds,
                sample_image,
                pattern='▒',
                use_blocks=False,  # Start with ASCII art
                use_color=True,  # Start with color
                enhance_contrast=1.2
            )
            logger.info("Created wallpaper background with image: %s", sample_image)
            return wallpaper_bg
        except Exception as e:
            logger.error("Failed to create wallpaper background: %s", e)
            # Fallback to regular background
            from vindauga.widgets.background import Background
            return Background(bounds, '▒')

    def _create_test_image(self, output_path: Path) -> str:
        """
        Create a simple test image if no sample image is available.
        """
        try:
            from PIL import Image, ImageDraw, ImageFont

            # Create a colorful test pattern
            width, height = 200, 150
            img = Image.new('RGB', (width, height), color='black')
            draw = ImageDraw.Draw(img)

            # Draw gradient background
            for y in range(height):
                for x in range(width):
                    r = int(255 * (x / width))
                    g = int(255 * (y / height))
                    b = int(255 * ((x + y) / (width + height)))
                    img.putpixel((x, y), (r, g, b))

            # Draw some shapes
            draw.rectangle([20, 20, 80, 80], fill='red', outline='white')
            draw.ellipse([120, 20, 180, 80], fill='blue', outline='yellow')
            draw.polygon([(100, 100), (150, 120), (120, 140)], fill='green', outline='white')

            # Add text
            try:
                draw.text((10, height - 30), "Vindauga", fill='white')
                draw.text((10, height - 15), "Wallpaper Demo", fill='cyan')
            except:
                pass  # Font might not be available

            img.save(output_path)
            logger.info("Created test image: %s", output_path)
            return str(output_path)

        except Exception as e:
            logger.error("Failed to create test image: %s", e)
            # Return path to non-existent file, will trigger fallback
            return str(output_path)


def setup_logging():
    """Setup logging for the demo."""
    v_logger = logging.getLogger('vindauga')
    v_logger.propagate = False
    l_format = "%(name)-25s | %(message)s"
    v_logger.setLevel(logging.DEBUG)
    handler = logging.StreamHandler(open('vindauga.log', 'wt', encoding='utf-8'))
    handler.setFormatter(logging.Formatter(l_format))
    v_logger.addHandler(handler)


if __name__ == '__main__':
    setup_logging()

    try:
        app = WallpaperDemo()
        app.run()
        logger.info("Demo completed")
    except Exception as e:
        logger.error("Demo failed: %s", e)
        raise
