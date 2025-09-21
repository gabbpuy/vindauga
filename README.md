# Vindauga

## Introduction
This is a pure python3 implementation of the BSD licensed C++ Turbo Vision library.

[Vindauga](https://en.wiktionary.org/wiki/vindauga) is the old Norse precursor to the middle english word 'Window'. These are really old windows...

I needed a cross-platform TUI for python for a project, and the projects available worked on Windows or UNIX but not
both. I had previously built a version of this by transliteration which was quite frankly awful, so a dust-off began.

The benefits of this version;

* No dependencies other than curses (See Windows below to have it work in a cmd/powershell window)
* A lot of refactoring to make the code-base somewhat consistent.
* It uses unicode by default, (so no CP437)
  * See [UTF-Demo](UTF-8-demo.txt) and [Cyrillic Test](examples/cyrillic-test.py)
  * The file viewer works with UTF-8 encoded files, see [UTF-Demo](UTF-8-demo.txt).
  * `gettext` is enabled so you can use the `_()` built-in, there's no extraction now though.
* Curses mouse works in DOS windows and Cygwin, putty etc.
* Some stuff is Pythonic. 
  * Some is still a little clunky to use, working on that.
* You can dynamically change the "resolution" of the console window to be the size you need.
  * See [`vindauga_demo`](vindauga_demo/vindauga_demo.py) for how.
  * This only works in virtual terminals (including windows CMD).
* Tested on Mac, Windows, Cygwin, Putty, X-Terms
  * A lot of alt-keys are trapped on mac you have to use ESC-xxx instead.
* You can open (interactive) shell windows.

I've implemented other widgets like combo-boxes so there's some extra widgets available OOTB.
I've pulled together the examples and converted them as well, so there's sample code.
I've tried to keep the original class and method documentation where appropriate.

You're currently limited to 1024 width windows, you can adjust this in `vindauga.types.draw_buffer` or subclass 
`DrawBuffer` if it's really a problem. If you're doing linear processing of the draw buffer, then it will grow 
whatever size you want, but if you want them pre-allocated it's 1K.

![demo](docs/screen-show.gif)

### Windows
You'll also need to install the `pywin32` libraries. 

Running it in Cygwin doesn't require anything, just use the cygwin python in a mintty window.

### Mac

You'll want to install `pasteboard` for some clipboard support.

## Using it
Look in the [examples](examples) directory for small samples of how to use widgets. 
The [vindauga_demo](vindauga_demo/vindauga_demo.py) shows how to put it all together into a larger app.

For the most part, you will want to subclass `Application` and add your own `Menu` objects.

This [example](examples/background.py) is pretty much as simple as it gets, although it does nothing
except render a background with the default `StatusLine` that lets you `Alt+X` to quit.

```python
# -*- coding: utf-8 -*-
from vindauga.widgets.application import Application
from vindauga.widgets.desktop import Desktop


class Demo(Application):
    """
    How to __change the background _pattern
    """
    def __init__(self):
        Desktop.DEFAULT_BACKGROUND = '╬'
        super().__init__()


if __name__ == '__main__':
    app = Demo()
    app.run()

```

## Issues
* Events sometimes disappear, particularly mouse clicks from inside PowerShell windows. Click then tab and then the click 
arrives.
* The `Screen` class does too much and needs to be broken up to move IO into it's own hierarchy
* Lots more testing needs to be added.
* No console mouse support as yet
* I haven't collected all the module imports into `__init__.py` I'm not convinced either way yet.
  * That does mean a lot of import lines, but it means you're only importing what you need, and
    what you're using is explicit.

## Contributing

### Python Version
I'm targetting python 3.10+

### Class and Variable Names
* It doesn't use PEP-8 naming, for various reasons.
  * Naming is camel case
  * Classes are uppercase first; e.g. `ClassName`
  * Variables are lowercase first; e.g. `variableName`
  * Acronyms should be upper class and separated by an underscore to prevent run-on; e.g. `MyHTTP_Service`  

### Filenames
* Filenames should be all lowercase to prevent issues on case-insensitive file systems.
* It should indicate the main class defined within, with words seperated by underscores e.g. `class_name.py`
  * Runnable filenames (like in examples), should use dash instead of underscore e.g. `my-test.py`
    1. This prevents accidental importing from them
    2. Allows you to name an example after widget without conflicting names.

### Hierarchy
Generally; 
* Simple views should be under `widgets` 
* Data requests things under `dialogs` 
* Complex things under `gadgets` e.g things that have their own window.

Move things into submodules if they need to span multiple files

If you make a widget, add a sample use-case into `examples` 

### Debugging
Obviously using `print()` isn't going to work, so use the `logging` module and prefix your logger with `vindauga.`
You can use `postMessage` from `widgets.message_window` to log into a Vindauga window. 
See [`info-box.py`](examples/info-box.py)
