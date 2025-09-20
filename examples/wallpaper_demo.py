# -*- coding: utf-8 -*-
import logging
from pathlib import Path
import random

from PIL import Image, ImageDraw

from vindauga.constants.buttons import bfDefault
from vindauga.constants.command_codes import hcNoContext, cmOK, cmCancel, cmQuit
from vindauga.constants.message_flags import mfError, mfOKButton
from vindauga.constants.event_codes import evCommand
from vindauga.constants.keys import kbAltA, kbAltL, kbAltX
from vindauga.constants.option_flags import ofCentered
from vindauga.events.event import Event

from vindauga.menus.menu_bar import MenuBar
from vindauga.menus.menu_item import MenuItem
from vindauga.menus.sub_menu import SubMenu

from vindauga.types.rect import Rect
from vindauga.utilities.pushd import pushd

from vindauga.widgets.application import Application
from vindauga.widgets.background import Background
from vindauga.widgets.button import Button
from vindauga.widgets.desktop import Desktop
from vindauga.widgets.dialog import Dialog
from vindauga.widgets.static_text import StaticText
from vindauga.widgets.wallpaper_background import WallpaperBackground
from vindauga.dialogs.file_dialog import FileDialog, fdOpenButton
from vindauga.dialogs.message_box import messageBox

logger = logging.getLogger('vindauga.wallpaper_demo')

# Command codes
cmAbout = 100
cmLoadImage = 101


class WallpaperDemo(Application):
    """
    Demo application showing wallpaper background functionality.
    """

    def __init__(self):
        super().__init__()
        self.wallpaper_desktop = None

    def initMenuBar(self, bounds: Rect) -> MenuBar:
        bounds.bottomRight.y = bounds.topLeft.y + 1
        fileMenu = (SubMenu('~F~ile', 0, hcNoContext) +
                    MenuItem('~L~oad Image...', cmLoadImage, kbAltL, hcNoContext) +
                    MenuItem.newLine() +
                    MenuItem('E~x~it', cmQuit, kbAltX, hcNoContext))

        aboutMenu = SubMenu('~A~bout', 0, hcNoContext) + MenuItem('~A~bout Demo', cmAbout, kbAltA, hcNoContext)
        return MenuBar(bounds, fileMenu + aboutMenu)

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
            elif command == cmLoadImage:
                self._load_image_dialog()
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

    def _load_image_dialog(self):
        """
        Show file dialog to load a new wallpaper image.
        """
        # Use single wildcard since FileList.readDirectory doesn't support multiple wildcards
        fileSpec = "*"
        wallpapers = Path(__file__).parent.parent / 'vindauga_demo' / 'wallpapers'
        with pushd(wallpapers):
            d = FileDialog(fileSpec, 'Load Wallpaper Image', '~N~ame', fdOpenButton, 100)
            if d and self.desktop.execView(d) != cmCancel:
                filename = d.getFilename()
                logger.info("Selected file: %s", filename)

                # Validate that the selected file is an image
                if not self._is_image_file(filename):
                    messageBox("Please select an image file.\n\n"
                               "Supported formats:\n"
                               "PNG, JPG, JPEG, GIF, BMP, TIFF",
                               mfError, (mfOKButton,))
                    self.destroy(d)
                    return

                # Find the wallpaper background and set the new image
                # wallpaper_bg = self._find_wallpaper_background()
                wallpaper_bg = self.desktop._background
                if isinstance(wallpaper_bg, WallpaperBackground):
                    try:
                        wallpaper_bg.set_image(filename)
                        logger.info("Successfully loaded new wallpaper: %s", filename)
                    except Exception as e:
                        logger.error("Failed to load wallpaper image %s: %s", filename, e)
                        messageBox(f"Failed to load image:\n{filename}\n\n"
                                   f"Error: {str(e)}",
                                   mfError, (mfOKButton,))
                else:
                    logger.error("Could not find WallpaperBackground to update")
                    messageBox("Internal error: Could not find wallpaper background to update.",
                               mfError, (mfOKButton,))

                self.destroy(d)

    def _is_image_file(self, filename: str) -> bool:
        """Check if filename has a supported image extension."""
        if not filename:
            return False

        # Convert to lowercase for case-insensitive comparison
        lower_filename = filename.lower()
        image_extensions = ['.png', '.jpg', '.jpeg', '.gif', '.bmp', '.tiff']

        return any(lower_filename.endswith(ext) for ext in image_extensions)


class WallpaperDesktop(Desktop):
    """
    Desktop with wallpaper background.
    """

    def initBackground(self, bounds: Rect):
        """Initialize wallpaper background."""
        # Look for a sample image in the examples directory
        examples_dir = Path(__file__).parent.parent / 'vindauga_demo' / 'wallpapers'

        # Try to find any image file in examples directory
        image_extensions = ['.png', '.jpg', '.jpeg', '.gif', '.bmp', '.tiff']
        sample_image = None

        random.shuffle(image_extensions)

        for ext in image_extensions:
            try:
                sample_image = random.choice(list(examples_dir.glob('*' + ext)))
            except IndexError:
                continue
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
            )
            logger.info("Created wallpaper background with image: %s", sample_image)
            return wallpaper_bg
        except Exception as e:
            logger.exception("Failed to create wallpaper background: %s", e)
            # Fallback to regular background
            return Background(bounds, '▒')

    def _create_test_image(self, output_path: Path) -> str:
        """
        Create a simple test image if no sample image is available.
        """
        try:

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
        logger.exception("Demo failed: %s", e)
        raise
