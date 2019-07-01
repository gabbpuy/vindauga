# -*- coding: utf-8 -*-

## View DragMode masks

# Allow the view to move.
# @see View::dragMode
dmDragMove = 0x01

# Allow the view to __change size.
# @see View::dragMode
dmDragGrow = 0x02

# The view's left-hand side cannot move outside limits.
# @see View::dragMode
dmLimitLoX = 0x10

# The view's top side cannot move outside limits.
# @see View::dragMode
dmLimitLoY = 0x20

# The view's right-hand side cannot move outside limits.
# @see View::dragMode
dmLimitHiX = 0x40

# The view's bottom side cannot move outside limits.
# @see View::dragMode
dmLimitHiY = 0x80

# No part of the view can move outside limits.
# @see View::dragMode
dmLimitAll = dmLimitLoX | dmLimitLoY | dmLimitHiX | dmLimitHiY
