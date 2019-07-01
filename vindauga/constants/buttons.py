# Button is a normal, non-default button.
# @see Button::flag
bfNormal = 0x00

# Button is the default button: if this bit is set this button will be
# highlighted as the default button.
# @see Button::flag
bfDefault = 0x01

# Button label is left-justified; if this bit is clear the title will be
# centered.
# @see Button::flag
bfLeftJust = 0x02

# Sends a broadcast message when pressed.
# @see Button::flag
bfBroadcast = 0x04

# The button grabs the focus when pressed.
# @see Button::flag
bfGrabFocus = 0x08
