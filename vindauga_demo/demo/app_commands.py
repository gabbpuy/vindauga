from enum import IntEnum, auto


class AppCommands(IntEnum):
    cmAboutCmd = 100
    cmPuzzleCmd = 101
    cmCalendarCmd = 102
    cmAsciiCmd = 103
    cmCalcCmd = 104
    cmOpenCmd = 105
    cmChDirCmd = 106
    cmShellCmd = 107
    cmMouseCmd = 108
    cmColorCmd = 109
    cmSaveCmd = 110
    cmRestoreCmd = 111
    cmDialogCmd = 112
    cmLoadWallpaperCmd = 113

    cmTest80x25 = auto()
    cmTest80x28 = auto()
    cmTest80x50 = auto()
    cmTest90x30 = auto()
    cmTest94x34 = auto()
    cmTest132x25 = auto()
    cmTest132x50 = auto()
    cmTest132x60 = auto()
    cmTest160x60 = auto()
