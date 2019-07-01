# -*- coding: utf-8 -*-
mfWarning = 0x0000  # Display a Warning box
mfError = 0x0001  # Display a Error box
mfInformation = 0x0002  # Display an Information Box
mfConfirmation = 0x0003  # Display a Confirmation Box
mfYesButton = 0x0100  # Put a Yes button into the dialog
mfNoButton = 0x0200  # Put a No button into the dialog
mfOKButton = 0x0400  # Put an OK button into the dialog
mfCancelButton = 0x0800  # Put a Cancel button into the dialog

# Message box button flags
# Standard Yes, No, Cancel dialog
mfYesNoCancel = (mfYesButton, mfNoButton, mfCancelButton)

# Standard OK, Cancel dialog
mfOKCancel = (mfOKButton, mfCancelButton)
