# -*- coding: utf-8 -*-
import logging


def setupLogging():
    vLogger = logging.getLogger('vindauga')
    vLogger.propagate = False
    lFormat = "%(name)-25s | %(message)s"
    vLogger.setLevel(logging.DEBUG)
    handler = logging.StreamHandler(open('vindauga.log', 'wt'))
    handler.setFormatter(logging.Formatter(lFormat))
    vLogger.addHandler(handler)


setupLogging()

logger = logging.getLogger('vindauga.demo.wallpaper')

try:
    from vindauga.widgets.application import Application
    from vindauga.widgets.desktop import Desktop
    from vindauga.widgets.wallpaper import Wallpaper
except:
    logger.exception('imports')
    raise


class WallpaperDesktop(Desktop):
    def initBackground(self, bounds):
        return Wallpaper(bounds, '116441263 (Small).jpg')


class Demo(Application):
    def initDesktop(self, bounds):
        bounds.topLeft.y += 1
        bounds.bottomRight.y -= 1
        return WallpaperDesktop(bounds)


if __name__ == '__main__':
    try:
        app = Demo()
        app.run()
    except:
        logger.exception('runtime')
