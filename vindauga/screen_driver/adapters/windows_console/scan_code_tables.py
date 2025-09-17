# -*- coding: utf-8 -*-
import vindauga.constants.keys as keys

NORMAL_CVT = {
    # Function keys
    59: keys.kbF1,  # F1
    60: keys.kbF2,  # F2
    61: keys.kbF3,  # F3
    62: keys.kbF4,  # F4
    63: keys.kbF5,  # F5
    64: keys.kbF6,  # F6
    65: keys.kbF7,  # F7
    66: keys.kbF8,  # F8
    67: keys.kbF9,  # F9
    68: keys.kbF10,  # F10

    # Arrow keys and navigation
    72: keys.kbUp,  # Up arrow
    80: keys.kbDown,  # Down arrow
    75: keys.kbLeft,  # Left arrow
    77: keys.kbRight,  # Right arrow
    71: keys.kbHome,  # Home
    79: keys.kbEnd,  # End
    73: keys.kbPgUp,  # Page Up
    81: keys.kbPgDn,  # Page Down
    82: keys.kbIns,  # Insert
    83: keys.kbDel,  # Delete

    # Special keys
    1: keys.kbEsc,  # Escape
    15: keys.kbTab,  # Tab
    28: keys.kbEnter,  # Enter
    14: keys.kbBackSpace,  # Backspace
}

# Shift key conversion table  
# Maps scan code -> Vindauga key code for Shift+key combinations
SHIFT_CVT = {
    59: keys.kbShiftF1,  # Shift+F1
    60: keys.kbShiftF2,  # Shift+F2
    61: keys.kbShiftF3,  # Shift+F3
    62: keys.kbShiftF4,  # Shift+F4
    63: keys.kbShiftF5,  # Shift+F5
    64: keys.kbShiftF6,  # Shift+F6
    65: keys.kbShiftF7,  # Shift+F7
    66: keys.kbShiftF8,  # Shift+F8
    67: keys.kbShiftF9,  # Shift+F9
    68: keys.kbShiftF10,  # Shift+F10
    15: keys.kbShiftTab,  # Shift+Tab
}

# Ctrl key conversion table
# Maps scan code -> Vindauga key code for Ctrl+key combinations  
CTRL_CVT = {
    59: keys.kbCtrlF1,  # Ctrl+F1
    60: keys.kbCtrlF2,  # Ctrl+F2
    61: keys.kbCtrlF3,  # Ctrl+F3
    62: keys.kbCtrlF4,  # Ctrl+F4
    63: keys.kbCtrlF5,  # Ctrl+F5
    64: keys.kbCtrlF6,  # Ctrl+F6
    65: keys.kbCtrlF7,  # Ctrl+F7
    66: keys.kbCtrlF8,  # Ctrl+F8
    67: keys.kbCtrlF9,  # Ctrl+F9
    68: keys.kbCtrlF10,  # Ctrl+F10

    # Navigation with Ctrl
    71: keys.kbCtrlHome,  # Ctrl+Home
    79: keys.kbCtrlEnd,  # Ctrl+End
    73: keys.kbCtrlPgUp,  # Ctrl+Page Up
    81: keys.kbCtrlPgDn,  # Ctrl+Page Down
    75: keys.kbCtrlLeft,  # Ctrl+Left
    77: keys.kbCtrlRight,  # Ctrl+Right
    72: keys.kbCtrlUp,  # Ctrl+Up
    80: keys.kbCtrlDown,  # Ctrl+Down

    15: keys.kbCtrlTab,  # Ctrl+Tab
    28: keys.kbCtrlEnter,  # Ctrl+Enter
    14: keys.kbCtrlBackSpace,  # Ctrl+Backspace
}

# Alt key conversion table
# Maps scan code -> Vindauga key code for Alt+key combinations
ALT_CVT = {
    59: keys.kbAltF1,  # Alt+F1
    60: keys.kbAltF2,  # Alt+F2
    61: keys.kbAltF3,  # Alt+F3
    62: keys.kbAltF4,  # Alt+F4
    63: keys.kbAltF5,  # Alt+F5
    64: keys.kbAltF6,  # Alt+F6
    65: keys.kbAltF7,  # Alt+F7
    66: keys.kbAltF8,  # Alt+F8
    67: keys.kbAltF9,  # Alt+F9
    68: keys.kbAltF10,  # Alt+F10

    # Alt+letters (generated dynamically from scan codes)
    30: keys.kbAltA,  # Alt+A
    48: keys.kbAltB,  # Alt+B
    46: keys.kbAltC,  # Alt+C
    32: keys.kbAltD,  # Alt+D
    18: keys.kbAltE,  # Alt+E
    33: keys.kbAltF,  # Alt+F
    34: keys.kbAltG,  # Alt+G
    35: keys.kbAltH,  # Alt+H
    23: keys.kbAltI,  # Alt+I
    36: keys.kbAltJ,  # Alt+J
    37: keys.kbAltK,  # Alt+K
    38: keys.kbAltL,  # Alt+L
    50: keys.kbAltM,  # Alt+M
    49: keys.kbAltN,  # Alt+N
    24: keys.kbAltO,  # Alt+O
    25: keys.kbAltP,  # Alt+P
    16: keys.kbAltQ,  # Alt+Q
    19: keys.kbAltR,  # Alt+R
    31: keys.kbAltS,  # Alt+S
    20: keys.kbAltT,  # Alt+T
    22: keys.kbAltU,  # Alt+U
    47: keys.kbAltV,  # Alt+V
    17: keys.kbAltW,  # Alt+W
    45: keys.kbAltX,  # Alt+X
    21: keys.kbAltY,  # Alt+Y
    44: keys.kbAltZ,  # Alt+Z

    # Alt+numbers
    2: keys.kbAlt1,  # Alt+1
    3: keys.kbAlt2,  # Alt+2
    4: keys.kbAlt3,  # Alt+3
    5: keys.kbAlt4,  # Alt+4
    6: keys.kbAlt5,  # Alt+5
    7: keys.kbAlt6,  # Alt+6
    8: keys.kbAlt7,  # Alt+7
    9: keys.kbAlt8,  # Alt+8
    10: keys.kbAlt9,  # Alt+9
    11: keys.kbAlt0,  # Alt+0

    14: keys.kbAltBackSpace,  # Alt+Backspace
}
