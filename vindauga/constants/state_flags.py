#  View State masks

# Set if the view is visible on its owner. Views are by default
# sfVisible. Use @ref View::show() and @ref View::hide() to modify
# sfVisible. An sfVisible view is not necessarily visible on the screen
# since its owner might not be visible. To test for visibility on the
# screen, examine the @ref sfExposed bit or call @ref View::exposed().
# @see View::state
sfVisible = 0x001

# Set if a view's cursor is visible. Clear is the default. You can
# use @ref View::showCursor() and @ref View::hideCursor() to modify
# sfCursorVis.
# @see View::state
sfCursorVis = 0x002

# Set if the view's cursor is a solid block; clear if the view's cursor
# is an underline (the default). Use @ref View::blockCursor() and
# @ref View::normalCursor() to modify this bit.
# @see View::state
sfCursorIns = 0x004

# Set if the view has a shadow.
# @see View::state
sfShadow = 0x008

# Set if the view is the active window or a subview in the active window.
# @see View::state
sfActive = 0x010

# Set if the view is the currently selected subview within its owner.
# Each @ref Group object has a @ref Group::current data member that
# points to the currently selected subview (or is 0 if no subview is
# selected). There can be only one currently selected subview in a
# @ref Group.
# @see View::state
sfSelected = 0x020

# Set if the view is focused. A view is focused if it is selected and
# all owners above it are also selected. The last view on the focused
# chain is the final target of all focused events.
# @see View::state
sfFocused = 0x040

# Set if the view is being dragged.
# @see View::state
sfDragging = 0x080

# Set if the view is disabled. A disabled view will ignore all events
# sent to it.
# @see View::state
sfDisabled = 0x100

# Set if the view is modal. There is always exactly one modal view in
# a running TVision application, usually a @ref Application or
# @ref Dialog object. When a view starts executing (through an
# @ref Group::execView() call), that view becomes modal. The modal
# view represents the apex (root) of the active event tree, getting
# and handling events until its @ref View::endModal() method is called.
# During this "local" event loop, events are passed down to lower
# subviews in the view tree. events from these lower views pass back
# up the tree, but go no further than the modal view. See also
# @ref View::setState(), @ref View::handleEvent() and
# @ref Group::execView().
# @see View::state
sfModal = 0x200

# This is a spare flag, available to specify some user-defined default
# state.
# @see View::state
sfDefault = 0x400

# Set if the view is owned directly or indirectly by the application
# object, and therefore possibly visible on the. @ref View::exposed()
# uses this flag in combination with further clipping calculations to
# determine whether any part of the view is actually visible on the
# screen.
# @see View::state
sfExposed = 0x800
