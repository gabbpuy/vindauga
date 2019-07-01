# -*- coding: utf-8 -*-

from ctypes import *

"""
ATTR_T int
COLOR_T short
SIZE_T short
CH_T chtype
chtype ulong
"""


class pdat(Structure):
    _fields_ = [("_pad_y", c_short),
                ("_pad_x", c_short),
                ("_pad_top", c_short),
                ("_pad_left", c_short),
                ("_pad_bottom", c_short),
                ("_pad_right", c_short)]


class ldat(Structure):
    _fields_ = [("_text", c_char_p),
                ("firstchar", c_short),
                ("lastchar", c_short),
                ("oldindex", c_short)]


lpldat = POINTER("ldat")
SetPointerType(lpldat, ldat)


class MEVENT(Structure):
    _fields_ = [("id", c_short),
                ("x", c_int),
                ("y", c_int),
                ("z", c_int),
                ("bstate", c_ulong)]


lpMEvent = POINTER("MEVENT")
SetPointerType(lpMEvent, MEVENT)


def newMouseEventPointer():
    me = MEVENT()
    return pointer(me)


lpwindow = POINTER("WINDOW")


class WINDOW(Structure):
    _fields_ = [("_cury", c_short),
                ("_curx", c_short),
                ("_maxy", c_short),
                ("_maxx", c_short),
                ("_begy", c_short),
                ("_begx", c_short),
                ("_flags", c_short),
                ("_attrs", c_int),
                ("_bkgd", c_ulong),
                ("_notimeout", c_ubyte),
                ("_clear", c_ubyte),
                ("_leaveok", c_ubyte),
                ("_scroll", c_ubyte),
                ("_idlok", c_ubyte),
                ("_idcok", c_ubyte),
                ("_immed", c_ubyte),
                ("_sync", c_ubyte),
                ("_use_keypad", c_ubyte),
                ("_delay", c_int),
                ("ldat", lpldat),
                ("_regtop", c_short),
                ("_regbottom", c_short),
                ("_parx", c_int),
                ("_pary", c_int),
                ("_parent", lpwindow),
                ("_pad", pdat),
                ("_yoffset", c_short),
                ]


SetPointerType(lpwindow, WINDOW)

global_acs_keys = ['ACS_ULCORNER', 'ACS_LLCORNER',
                   'ACS_URCORNER', 'ACS_LRCORNER', 'ACS_LTEE',
                   'ACS_RTEE', 'ACS_BTEE', 'ACS_TTEE', 'ACS_HLINE',
                   'ACS_VLINE', 'ACS_PLUS', 'ACS_S', 'ACS_S',
                   'ACS_DIAMOND', 'ACS_CKBOARD', 'ACS_DEGREE',
                   'ACS_PLMINUS', 'ACS_BULLET', 'ACS_LARROW',
                   'ACS_RARROW', 'ACS_DARROW', 'ACS_UARROW',
                   'ACS_BOARD', 'ACS_LANTERN', 'ACS_BLOCK',
                   'ACS_S', 'ACS_S', 'ACS_LEQUAL', 'ACS_GEQUAL',
                   'ACS_PI', 'ACS_NEQUAL', 'ACS_STERLING',
                   ]
global_acs_vals = ('l', 'm', 'k', 'j', 't', 'u', 'v', 'w', 'q',
                   'x', 'n', 'o', 's', '`', 'a', 'f', 'g', '~',
                   ',', '+', '.', '-', 'h', 'i', '0', 'p', 'r',
                   'y', 'z', '{', '|', '}',)

ACSMAP = c_ulong * 128


class CursesWrapper:
    COLOR_BLACK = 0
    COLOR_RED = 1
    COLOR_GREEN = 2
    COLOR_YELLOW = 3
    COLOR_BLUE = 4
    COLOR_MAGENTA = 5
    COLOR_CYAN = 6
    COLOR_WHITE = 7

    NCURSES_BITS = lambda mask, shift: (mask << (shift + 8))

    BUTTON_RELEASE = lambda e, x: (e & (0o01 << (6 * (x - 1))))
    BUTTON_PRESS = lambda e, x: (e & (0o02 << (6 * (x - 1))))
    BUTTON_CLICK = lambda e, x: (e & (0o04 << (6 * (x - 1))))
    BUTTON_DOUBLE_CLICK = lambda e, x: (e & (0o10 << (6 * (x - 1))))
    BUTTON_TRIPLE_CLICK = lambda e, x: (e & (0o20 << (6 * (x - 1))))
    BUTTON_RESERVED_EVENT = lambda e, x: (e & (0o40 << (6 * (x - 1))))

    A_NORMAL = 0
    A_ATTRIBUTES = NCURSES_BITS(0, 0)
    A_CHARTEXT = (NCURSES_BITS(1, 0) - 1)
    A_COLOR = NCURSES_BITS((1 << 8) - 1, 0)
    A_STANDOUT = NCURSES_BITS(1, 8)
    A_UNDERLINE = NCURSES_BITS(1, 9)
    A_REVERSE = NCURSES_BITS(1, 10)
    A_BLINK = NCURSES_BITS(1, 11)
    A_DIM = NCURSES_BITS(1, 12)
    A_BOLD = NCURSES_BITS(1, 13)
    A_ALTCHARSET = NCURSES_BITS(1, 14)
    A_INVIS = NCURSES_BITS(1, 15)
    A_PROTECT = NCURSES_BITS(1, 16)
    A_HORIZONTAL = NCURSES_BITS(1, 17)
    A_LEFT = NCURSES_BITS(1, 18)
    A_LOW = NCURSES_BITS(1, 19)
    A_RIGHT = NCURSES_BITS(1, 20)
    A_TOP = NCURSES_BITS(1, 21)
    A_VERTICAL = NCURSES_BITS(1, 22)

    WA_ATTRIBUTES = A_ATTRIBUTES
    WA_NORMAL = A_NORMAL
    WA_STANDOUT = A_STANDOUT
    WA_UNDERLINE = A_UNDERLINE
    WA_REVERSE = A_REVERSE
    WA_BLINK = A_BLINK
    WA_DIM = A_DIM
    WA_BOLD = A_BOLD
    WA_ALTCHARSET = A_ALTCHARSET
    WA_INVIS = A_INVIS
    WA_PROTECT = A_PROTECT
    WA_HORIZONTAL = A_HORIZONTAL
    WA_LEFT = A_LEFT
    WA_LOW = A_LOW
    WA_RIGHT = A_RIGHT
    WA_TOP = A_TOP
    WA_VERTICAL = A_VERTICAL

    ERR = -1

    KEY_CODE_YES = 0o400
    KEY_MIN = 0o401
    KEY_BREAK = 0o401
    KEY_SRESET = 0o530
    KEY_RESET = 0o531
    KEY_DOWN = 0o402
    KEY_UP = 0o403
    KEY_LEFT = 0o404
    KEY_RIGHT = 0o405
    KEY_HOME = 0o406
    KEY_BACKSPACE = 0o407
    KEY_F0 = 0o410

    KEY_F = lambda self, n: self.KEY_F0 + n

    KEY_DL = 0o510
    KEY_IL = 0o511
    KEY_DC = 0o512
    KEY_IC = 0o513
    KEY_EIC = 0o514
    KEY_CLEAR = 0o515
    KEY_EOS = 0o516
    KEY_EOL = 0o517
    KEY_SF = 0o520
    KEY_SR = 0o521
    KEY_NPAGE = 0o522
    KEY_PPAGE = 0o523
    KEY_STAB = 0o524
    KEY_CTAB = 0o525
    KEY_CATAB = 0o526
    KEY_ENTER = 0o527
    KEY_PRINT = 0o532
    KEY_LL = 0o533
    KEY_A1 = 0o534
    KEY_A3 = 0o535
    KEY_B2 = 0o536
    KEY_C1 = 0o537
    KEY_C3 = 0o540
    KEY_BTAB = 0o541
    KEY_BEG = 0o542
    KEY_CANCEL = 0o543
    KEY_CLOSE = 0o544
    KEY_COMMAND = 0o545
    KEY_COPY = 0o546
    KEY_CREATE = 0o547
    KEY_END = 0o550
    KEY_EXIT = 0o551
    KEY_FIND = 0o552
    KEY_HELP = 0o553
    KEY_MARK = 0o554
    KEY_MESSAGE = 0o555
    KEY_MOVE = 0o556
    KEY_NEXT = 0o557
    KEY_OPEN = 0o560
    KEY_OPTIONS = 0o561
    KEY_PREVIOUS = 0o562
    KEY_REDO = 0o563
    KEY_REFERENCE = 0o564
    KEY_REFRESH = 0o565
    KEY_REPLACE = 0o566
    KEY_RESTART = 0o567
    KEY_RESUME = 0o570
    KEY_SAVE = 0o571
    KEY_SBEG = 0o572
    KEY_SCANCEL = 0o573
    KEY_SCOMMAND = 0o574
    KEY_SCOPY = 0o575
    KEY_SCREATE = 0o576
    KEY_SDC = 0o577
    KEY_SDL = 0o600
    KEY_SELECT = 0o601
    KEY_SEND = 0o602
    KEY_SEOL = 0o603
    KEY_SEXIT = 0o604
    KEY_SFIND = 0o605
    KEY_SHELP = 0o606
    KEY_SHOME = 0o607
    KEY_SIC = 0o610
    KEY_SLEFT = 0o611
    KEY_SMESSAGE = 0o612
    KEY_SMOVE = 0o613
    KEY_SNEXT = 0o614
    KEY_SOPTIONS = 0o615
    KEY_SPREVIOUS = 0o616
    KEY_SPRINT = 0o617
    KEY_SREDO = 0o620
    KEY_SREPLACE = 0o621
    KEY_SRIGHT = 0o622
    KEY_SRSUME = 0o623
    KEY_SSAVE = 0o624
    KEY_SSUSPEND = 0o625
    KEY_SUNDO = 0o626
    KEY_SUSPEND = 0o627
    KEY_UNDO = 0o630
    KEY_MOUSE = 0o631
    KEY_RESIZE = 0o632
    KEY_MAX = 0o777

    BUTTON1_RELEASED = 0o00000000001
    BUTTON1_PRESSED = 0o00000000002
    BUTTON1_CLICKED = 0o00000000004
    BUTTON1_DOUBLE_CLICKED = 0o00000000010
    BUTTON1_TRIPLE_CLICKED = 0o00000000020
    BUTTON1_RESERVED_EVENT = 0o00000000040
    BUTTON2_RELEASED = 0o00000000100
    BUTTON2_PRESSED = 0o00000000200
    BUTTON2_CLICKED = 0o00000000400
    BUTTON2_DOUBLE_CLICKED = 0o00000001000
    BUTTON2_TRIPLE_CLICKED = 0o00000002000
    BUTTON2_RESERVED_EVENT = 0o00000004000
    BUTTON3_RELEASED = 0o00000010000
    BUTTON3_PRESSED = 0o00000020000
    BUTTON3_CLICKED = 0o00000040000
    BUTTON3_DOUBLE_CLICKED = 0o00000100000
    BUTTON3_TRIPLE_CLICKED = 0o00000200000
    BUTTON3_RESERVED_EVENT = 0o00000400000
    BUTTON4_RELEASED = 0o00001000000
    BUTTON4_PRESSED = 0o00002000000
    BUTTON4_CLICKED = 0o00004000000
    BUTTON4_DOUBLE_CLICKED = 0o00010000000
    BUTTON4_TRIPLE_CLICKED = 0o00020000000
    BUTTON4_RESERVED_EVENT = 0o00040000000
    BUTTON_CTRL = 0o00100000000
    BUTTON_SHIFT = 0o00200000000
    BUTTON_ALT = 0o00400000000
    ALL_MOUSE_EVENTS = 0o00777777777
    REPORT_MOUSE_POSITION = 0o01000000000

    global_int_values = ('COLORS', 'COLOR_PAIRS',
                         'LINES', 'COLS', 'TABSIZE', 'ESCDELAY',
                         )

    def __init__(self, curseslib='libncurses.so'):
        self.ncurses = cdll.LoadLibrary(curseslib)
        self.acsmap = None
        self._stdscr = None
        self._curscr = None
        self._newscr = None
        self.setFProtos()
        self.setACSVals()
        self.initialised = True

    def setACSVals(self):
        self.acsmap = ACSMAP.in_dll(self.ncurses, 'acs_map')

        for i, k in enumerate(global_acs_keys):
            setattr(self, k, self.acsmap[ord(global_acs_vals[i])])

    def __getattr__(self, attr):
        if attr in self.__dict__:
            return self.__dict__[attr]

        if ('_' + attr) in self.__dict__:
            return self.__dict__['_' + attr].value

        return getattr(self.__dict__['ncurses'], attr)

    def _int_param(self, param):
        return c_int.in_dll(self.ncurses, param)

    def _ulong_param(self, param):
        return c_ulong.in_dll(self.ncurses, param)

    def initscr(self):
        w = self.ncurses.initscr()
        self.setupGlobals()
        self.setACSVals()
        return w

    def setupGlobals(self):
        for g in self.global_int_values:
            setattr(self, '_' + g, self._int_param(g))

        self._stdscr = lpwindow.in_dll(self.ncurses, 'stdscr')
        self._curscr = lpwindow.in_dll(self.ncurses, 'curscr')
        self._newscr = lpwindow.in_dll(self.ncurses, 'newscr')

    def setFProtos(self):
        nc = self.ncurses

        nc.wresize.argtypes = [lpwindow, c_int, c_int]
        nc.addch.argtypes = [c_int]
        nc.addchnstr.argtypes = [c_ulong, c_int]
        nc.addnstr.argtypes = [c_char_p, c_int]
        nc.attr_get.argtypes = [c_void_p, c_void_p, c_void_p]
        nc.attr_off.argtypes = [c_short, c_void_p]
        nc.attr_on.argtypes = [c_short, c_void_p]
        nc.attr_set.argtypes = [c_short, c_short, c_void_p]
        nc.box.argtypes = [lpwindow, c_int, c_int]
        nc.chgat.argtypes = [c_int, c_short, c_short, c_void_p]
        nc.clearok.argtypes = [lpwindow, c_byte]
        nc.color_content.argtypes = [c_short, c_void_p, c_void_p, c_void_p]
        nc.color_set.argtypes = [c_short, c_void_p]
        nc.copywin.argtypes = [lpwindow, lpwindow, c_int, c_int, c_int, c_int, c_int, c_int, c_int]
        nc.delscreen.argtypes = [c_void_p]  ### Really SCREEN *
        nc.delwin.argtypes = [lpwindow]

        nc.derwin.argtypes = [lpwindow, c_int, c_int, c_int, c_int]
        nc.derwin.restype = lpwindow

        nc.dupwin.argtypes = [lpwindow]
        nc.dupwin.restype = lpwindow
        nc.getbkgd.argtypes = [lpwindow]
        nc.getnstr.argtypes = [c_char_p, c_int]
        nc.getstr.argtypes = [c_char_p]
        nc.getwin.argtypes = [c_void_p]
        nc.getwin.restype = lpwindow
        nc.idcok.argtypes = [lpwindow, c_byte]
        nc.idlok.argtypes = [lpwindow, c_byte]
        nc.immedok.argtypes = [lpwindow, c_byte]
        nc.inchnstr.argtypes = [c_void_p, c_int]
        nc.inchstr.argtypes = [c_void_p]
        nc.initscr.restype = lpwindow
        nc.innstr.argtypes = [c_char_p, c_int]
        nc.insnstr.argtypes = [c_char_p, c_int]
        nc.insstr.argtypes = [c_char_p]
        nc.instr.argtypes = [c_char_p]
        nc.intrflush.argtypes = [lpwindow, c_byte]
        nc.is_linetouched.argtypes = [lpwindow, c_int]
        nc.is_wintouched.argtypes = [lpwindow]
        nc.keyname.restype = c_char_p
        nc.keypad.argtypes = [lpwindow, c_byte]
        nc.leaveok.argtypes = [lpwindow, c_byte]
        nc.longname.restype = c_char_p
        nc.meta.argtypes = [lpwindow, c_byte]
        nc.mvaddchnstr.argtypes = [c_int, c_int, c_void_p, c_int]
        nc.mvaddchstr.argtypes = [c_int, c_int, c_void_p]
        nc.mvaddnstr.argtypes = [c_int, c_int, c_void_p, c_int]
        nc.mvaddstr.argtypes = [c_int, c_int, c_void_p]
        # Generated
        # nc.mvchgat.argtypes = [c_int, c_int, c_int, c_int, c_short, c_void_p]
        nc.mvderwin.argtypes = [lpwindow, c_int, c_int]
        nc.mvgetnstr.argtypes = [c_int, c_int, c_char_p, c_int]
        nc.mvgetstr.argtypes = [c_int, c_int, c_char_p]
        nc.mvinchnstr.argtypes = [c_int, c_int, c_void_p, c_int]
        nc.mvinchstr.argtypes = [c_int, c_int, c_void_p]
        nc.mvinnstr.argtypes = [c_int, c_int, c_void_p, c_int]
        nc.mvinsnstr.argtypes = [c_int, c_int, c_void_p, c_int]
        nc.mvinsstr.argtypes = [c_int, c_int, c_char_p]
        nc.mvinstr.argtypes = [c_int, c_int, c_char_p]

        nc.mvwaddch.argtypes = [lpwindow, c_int, c_int, c_ulong]
        nc.mvwaddchnstr.argtypes = [lpwindow, c_int, c_int, c_void_p, c_int]
        nc.mvwaddchstr.argtypes = [lpwindow, c_int, c_int, c_void_p]
        nc.mvwaddnstr.argtypes = [lpwindow, c_int, c_int, c_char_p, c_int]
        nc.mvwaddstr.argtypes = [lpwindow, c_int, c_int, c_char_p]
        nc.mvwchgat.argtypes = [lpwindow, c_int, c_int, c_int, c_void_p, c_short, c_void_p]

        nc.mvwdelch.argtypes = [lpwindow, c_int, c_int]
        nc.mvwgetch.argtypes = [lpwindow, c_int, c_int]
        nc.mvwgetnstr.argtypes = [lpwindow, c_int, c_int, c_char_p, c_int]
        nc.mvwgetstr.argtypes = [lpwindow, c_int, c_int, c_char_p]
        nc.mvwhline.argtypes = [lpwindow, c_int, c_int, c_ulong, c_int]
        nc.mvwin.argtypes = [lpwindow, c_int, c_int]
        nc.mvwinch.argtypes = [lpwindow, c_int, c_int]
        nc.mvwinch.restype = c_ulong
        nc.mvwinchnstr.argtypes = [lpwindow, c_int, c_int, c_void_p, c_int]
        nc.mvwinchstr.argtypes = [lpwindow, c_int, c_int, c_void_p]
        nc.mvwinnstr.argtypes = [lpwindow, c_int, c_int, c_void_p, c_int]
        nc.mvwinsch.argtypes = [lpwindow, c_int, c_int, c_ulong]

        nc.mvwinsnstr.argtypes = [lpwindow, c_int, c_int, c_char_p, c_int]
        nc.mvwinsstr.argtypes = [lpwindow, c_int, c_int, c_char_p]
        nc.mvwinstr.argtypes = [lpwindow, c_int, c_int, c_char_p]
        nc.mvwvline.argtypes = [lpwindow, c_int, c_int, c_long, c_int]

        nc.newpad.restype = lpwindow

        nc.newterm.argtypes = [c_char_p, c_void_p, c_void_p]
        nc.newterm.restype = c_void_p  ### SCREEN *

        nc.newwin.restype = lpwindow
        nc.nodelay.argtypes = [lpwindow, c_byte]
        nc.notimeout.argtypes = [lpwindow, c_byte]
        nc.overlay.argtypes = [lpwindow, lpwindow]
        nc.overwrite.argtypes = [lpwindow, lpwindow]
        nc.pair_content.argtypes = [c_short, c_void_p, c_void_p]
        nc.pechochar.argtypes = [lpwindow, c_long]
        nc.pnoutrefresh.argtypes = [lpwindow, c_int, c_int, c_int, c_int, c_int, c_int]
        nc.prefresh.argtypes = [lpwindow, c_int, c_int, c_int, c_int, c_int, c_int]
        nc.putwin.argtypes = [lpwindow, c_void_p]
        nc.redrawwin.argtypes = [lpwindow]
        nc.scroll.argtypes = [lpwindow]
        nc.scrollok.argtypes = [lpwindow, c_byte]

        nc.subpad.argtypes = [lpwindow, c_int, c_int, c_int, c_int]
        nc.subpad.restype = lpwindow
        nc.subwin.argtypes = [lpwindow, c_int, c_int, c_int, c_int]
        nc.subwin.restype = lpwindow
        nc.syncok.argtypes = [lpwindow, c_byte]
        nc.termattrs.restype = c_long
        nc.termname.restype = c_char_p
        nc.touchline.argtypes = [lpwindow, c_int, c_int]
        nc.touchwin.argtypes = [lpwindow]
        nc.untouchwin.argtypes = [lpwindow]

        nc.waddch.argtypes = [lpwindow, c_long]
        nc.waddchnstr.argtypes = [lpwindow, c_void_p, c_int]
        nc.waddchstr.argtypes = [lpwindow, c_void_p]
        nc.waddnstr.argtypes = [lpwindow, c_char_p, c_int]
        nc.waddstr.argtypes = [lpwindow, c_char_p]
        nc.wattron.argtypes = [lpwindow, c_int]
        nc.wattroff.argtypes = [lpwindow, c_int]
        nc.wattrset.argtypes = [lpwindow, c_int]

        nc.wattr_get.argtypes = [lpwindow, c_void_p, c_void_p, c_void_p]
        nc.wattr_on.argtypes = [lpwindow, c_int, c_void_p]
        nc.wattr_off.argtypes = [lpwindow, c_int, c_void_p]
        nc.wattr_set.argtypes = [lpwindow, c_int, c_short, c_void_p]
        nc.wbkgd.argtypes = [lpwindow, c_long]
        nc.wbkgdset.argtypes = [lpwindow, c_long]
        nc.wborder.argtypes = [lpwindow, c_long, c_long, c_long, c_long, c_long, c_long, c_long, c_long]

        nc.wchgat.argtypes = [lpwindow, c_int, c_long, c_short, c_void_p]
        nc.wclear.argtypes = [lpwindow]
        nc.wclrtobot.argtypes = [lpwindow]
        nc.wclrtoeol.argtypes = [lpwindow]
        nc.wcolor_set.argtypes = [lpwindow, c_short, c_void_p]
        nc.wcursyncup.argtypes = [lpwindow]
        nc.delch.argtypes = [lpwindow]
        nc.deleteln.argtypes = [lpwindow]
        nc.wechochar.argtypes = [lpwindow, c_long]
        nc.werase.argtypes = [lpwindow]
        nc.wgetch.argtypes = [lpwindow]
        nc.wgetnstr.argtypes = [lpwindow, c_char_p, c_int]
        nc.wgetstr.argtypes = [lpwindow, c_char_p]
        nc.whline.argtypes = [lpwindow, c_long, c_int]
        nc.winch.argtypes = [lpwindow]
        nc.winchnstr.argtypes = [lpwindow, c_void_p, c_int]
        nc.winchstr.argtypes = [lpwindow, c_void_p]
        nc.winnstr.argtypes = [lpwindow, c_char_p, c_int]
        nc.winsch.argtypes = [lpwindow, c_long]
        nc.winsdelln.argtypes = [lpwindow, c_int]
        nc.winsertln.argtypes = [lpwindow]
        nc.winsnstr.argtypes = [lpwindow, c_char_p, c_int]
        nc.winsstr.argtypes = [lpwindow, c_char_p]
        nc.winstr.argtypes = [lpwindow, c_char_p]
        nc.wmove.argtypes = [lpwindow, c_int, c_int]
        nc.wnoutrefresh.argtypes = [lpwindow]
        nc.wrefresh.argtypes = [lpwindow]
        nc.wscrl.argtypes = [lpwindow, c_int]
        nc.wsetscrreg.argtypes = [lpwindow, c_int, c_int]
        nc.wstandout.argtypes = [lpwindow]
        nc.wstandend.argtypes = [lpwindow]
        nc.wsyncdown.argtypes = [lpwindow]
        nc.wsyncup.argtypes = [lpwindow]
        nc.wtimeout.argtypes = [lpwindow, c_int]
        nc.wtouchln.argtypes = [lpwindow, c_int, c_int, c_int]
        nc.wvline.argtypes = [lpwindow, c_long, c_int]

        nc.getmouse.argtypes = [lpMEvent, ]
        nc.ungetmouse.argtypes = [lpMEvent, ]
        nc.mousemask.restype = c_long
        nc.mousemask.argtypes = [c_long, c_void_p]

        nc.wenclose.restype = c_long
        nc.wenclose.argtypes = [lpwindow, c_int, c_int]

        nc.wmouse_trafo.argtypes = [lpwindow, c_void_p, c_void_p, c_int]
        nc.mouse_trafo.argtypes = [c_void_p, c_void_p, c_int]

    def mouse_trafo(self, y, x, to_screen):
        return self.wmouse_trafo(self.stdscr, y, x, to_screen)


ncurses = CursesWrapper()
