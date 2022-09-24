# -*- coding: utf-8 -*-
"""
#----------------------------------------------------------------------#
#                                                                      #
#     Palette layout                                                   #
#       1 = Frame passive                                              #
#       2 = Frame active                                               #
#       3 = Frame icon                                                 #
#       4 = ScrollBar page area                                        #
#       5 = ScrollBar controls                                         #
#       6 = StaticText                                                 #
#       7 = Label normal                                               #
#       8 = Label selected                                             #
#       9 = Label shortcut                                             #
#      10 = Button normal                                              #
#      11 = Button default                                             #
#      12 = Button selected                                            #
#      13 = Button disabled                                            #
#      14 = Button shortcut                                            #
#      15 = Button shadow                                              #
#      16 = Cluster normal                                             #
#      17 = Cluster selected                                           #
#      18 = Cluster shortcut                                           #
#      19 = InputLine normal _text                                     #
#      20 = InputLine selected _text                                   #
#      21 = InputLine arrows                                           #
#      22 = History_support arrow                                      #
#      23 = History_support sides                                      #
#      24 = HistoryWindow scrollbar page area                          #
#      25 = HistoryWindow scrollbar controls                           #
#      26 = ListViewer normal                                          #
#      27 = ListViewer focused                                         #
#      28 = ListViewer selected                                        #
#      29 = ListViewer divider                                         #
#      30 = InfoPane                                                   #
#      31 = Cluster Disabled                                           #
#      32 = Reserved                                                   #
#----------------------------------------------------------------------#
"""
import array
from typing import Union


class Palette:
    """
    Palette object

    The first byte of a palette string holds its length (not counting the first
    byte itself). Each basic view has a default palette that determines the
    usual colors assigned to the various parts of a view, such as scroll bars,
    frames, buttons, text, and so on.
    """

    def __init__(self, palette: Union['Palette', str] = ''):
        if isinstance(palette, (Palette,)):
            self.palette = array.array('B', palette.palette)
        else:
            self.palette = array.array('B', (ord(p) for p in palette))

    def __len__(self):
        return len(self.palette)

    def __getitem__(self, index):
        return self.palette[index - 1]
