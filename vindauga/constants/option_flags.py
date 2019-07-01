# View Option masks

# Set if the view should select itself automatically (see
# @ref sfSelected); for example, by a mouse click in the view, or a Tab
# in a dialog box.
# @see View::options
ofSelectable = 0x001

# Set if the view should move in front of all other peer views when
# selected. When the ofTopSelect bit is set, a call to
# @ref View::select() corresponds to a call to @ref View::makeFirst().
# @ref Window and descendants by default have the ofTopSelect bit set
# which causes them to move in front of all other windows on the desktop
# when selected.
# @see View::options
ofTopSelect = 0x002

# If clear, a mouse click that selects a view will have no further
# effect. If set, such a mouse click is processed as a normal mouse
# click after selecting the view. Has no effect unless @ref ofSelectable
# is also set. See also @ref View::handleEvent(), @ref sfSelected and
# @ref ofSelectable.
# @see View::options
ofFirstClick = 0x004

# Set if the view should have a frame drawn around it. A @ref Window
# and any class derived from @ref Window, has a @ref Frame as its last
# subview. When drawing itself, the @ref Frame will also draw a frame
# around any other subviews that have the ofFramed bit set.
# @see View::options
ofFramed = 0x008

# Set if the view should receive focused events before they are sent to
# the focused view. Otherwise clear. See also @ref sfFocused
# @ref ofPostProcess, and @ref Group::phase.
# @see View::options
ofPreProcess = 0x010

# Set if the view should receive focused events whenever the focused
# view fails to handle them. Otherwise clear. See also @ref sfFocused
# @ref ofPreProcess and @ref Group::phase.
# @see View::options
ofPostProcess = 0x020

# Used for @ref Group objects and classes derived from @ref Group
# only. Set if a cache buffer should be allocated if sufficient memory
# is available. The group buffer holds a screen image of the whole
# group so that group redraws can be sped up. In the absence of a
# buffer, @ref Group::draw() calls on each subview's
# @ref View::drawView() method. If subsequent memory allocation calls
# fail, group buffers will be deallocated to make memory available.
# @see View::options
ofBuffered = 0x040

# Set if the desktop can tile (or cascade) this view. Usually used
# only with @ref Window objects.
# @see View::options
ofTileable = 0x080

# Set if the view should be centered on the x-axis of its owner when
# inserted in a group using @ref Group::insert().
# @see View::options
ofCenterX = 0x100

# Set if the view should be centered on the y-axis of its owner when
# inserted in a group using @ref Group::insert().
# @see View::options
ofCenterY = 0x200

# Set if the view should be centered on both axes of its owner when
# inserted in a group using @ref Group::insert().
# @see View::options
ofCentered = 0x300

# Undocumented.
# @see View::options
ofValidate = 0x400
