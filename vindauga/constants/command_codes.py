# -*- coding: utf-8 -*-
# Standard command codes
cmValid = 0
cmQuit = 1
cmError = 2
cmMenu = 3
cmClose = 4
cmZoom = 5
cmResize = 6
cmNext = 7
cmPrev = 8
cmHelp = 9

#  Dialog standard commands
cmOK = 10
cmCancel = 11
cmYes = 12
cmNo = 13
cmDefault = 14

#  Application command codes
cmCut = 20
cmCopy = 21
cmPaste = 22
cmUndo = 23
cmClear = 24
cmTile = 25
cmCascade = 26

# Standard application commands
cmNew = 30
cmOpen = 31
cmSave = 32
cmSaveAs = 33
cmSaveAll = 34
cmChDir = 35
cmDosShell = 36
cmCloseAll = 37
cmSysRepaint = 38
cmSysResize = 39
cmSysWakeup = 40
cmRecordHistory = 60
cmLoseFocus = 61

# Standard messages
cmReceivedFocus = 50
cmReleasedFocus = 51
cmCommandSetChanged = 52

# ScrollBar messages
cmScrollBarChanged = 53
cmScrollBarClicked = 54

# Window select messages
cmSelectWindowNum = 55

#  ListViewer messages
cmListItemSelected = 56

## View Help context codes

# No context specified.
# @see View::helpCtx
hcNoContext = 0

# Object is being dragged.
# @see View::helpCtx
hcDragging = 1

#  View inhibit flags
noMenuBar = 0x0001
noDeskTop = 0x0002
noStatusLine = 0x0004
noBackground = 0x0008
noFrame = 0x0010
noViewer = 0x0020
noHistory = 0x0040

# Window number constants

# Use the constant wnNoNumber to indicate that the window is not to be
# numbered and cannot be selected via the Alt+number key.
# @see Window::Window
wnNoNumber = 0

# Window palette entries

# Window _text is yellow on blue.
# @see Window::palette
wpBlueWindow = 0

# Window _text is blue on cyan.
# @see Window::palette
wpCyanWindow = 1

# Window _text is black on gray.
# @see Window::palette
wpGrayWindow = 2

