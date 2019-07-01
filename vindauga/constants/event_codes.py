# -*- coding: utf-8 -*-
# Event codes

# Mouse button pressed.
# @see Event::what
evMouseDown = 0x0001

# Mouse button released.
# @see Event::what
evMouseUp = 0x0002

# Mouse changed location.
# @see Event::what
evMouseMove = 0x0004

# Periodic event while mouse button held down.
# @see Event::what
evMouseAuto = 0x0008

# Key pressed.
# @see Event::what
evKeyDown = 0x0010

# Command event.
# @see Event::what
evCommand = 0x0100

# Broadcast event.
# @see Event::what
evBroadcast = 0x0200

# Event masks */

# Event already handled.
# @see Event::what
evNothing = 0x0000

# Mouse event.
# @see Event::what
evMouse = 0x000f

# Keyboard event.
# @see Event::what
evKeyboard = 0x0010

# Message (command, broadcast, or user-defined) event.
# @see Event::what
evMessage = 0xFF00

# Mouse button state masks
mbLeftButton = 0x01
mbRightButton = 0x02

# Mouse event flags
meMouseMoved = 0x01
meDoubleClick = 0x02

#  Event masks
# Defines the event classes that are positional events.
# The focusedEvents and positionalEvents masks are used by
# @ref Group::handleEvent() to determine how to dispatch an event to the
# group's subviews. If an event class isn't contained in
# @ref focusedEvents or positionalEvents, it is treated as a broadcast
# event.
positionalEvents = evMouse

# Defines the event classes that are focused events.
# The focusedEvents and positionalEvents values are used by
# @ref Group::handleEvent() to determine how to dispatch an event to the
# group's subviews. If an event class isn't contained in
# focusedEvents or @ref positionalEvents, it is treated as a broadcast
# event.
focusedEvents = evKeyboard | evCommand
