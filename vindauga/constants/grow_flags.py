# -*- coding: utf-8 -*-
# View GrowMode masks

# If set, the left-hand side of the view will maintain a constant
# distance from its owner's right-hand side. If not set, the movement
# indicated won't occur.
# @see View::growMode
gfGrowLoX = 0x01

# If set, the top of the view will maintain a constant distance from
# the bottom of its owner.
# @see View::growMode
gfGrowLoY = 0x02

# If set, the right-hand side of the view will maintain a constant
# distance from its owner's right side.
# @see View::growMode
gfGrowHiX = 0x04

# If set, the bottom of the view will maintain a constant distance
# from the bottom of its owner's.
# @see View::growMode
gfGrowHiY = 0x08

# If set, the view will move with the lower-right corner of its owner.
# @see View::growMode
gfGrowAll = 0x0f

# For use with @ref Window objects that are in the desktop. The view
# will __change size relative to the owner's size, maintaining that
# relative size with respect to the owner even when screen is resized.
# @see View::growMode
gfGrowRel = 0x10

# Undocumented.
# @see View::growMode
gfFixed = 0x20
