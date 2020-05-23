# -*- coding: utf-8 -*-
cmFileOpen = 1001  # Returned from FileDialog when Open pressed
cmFileReplace = 1002  # Returned from FileDialog when Replace pressed
cmFileClear = 1003  # Returned from FileDialog when Clear pressed
cmFileInit = 1004  # Used by FileDialog internally
cmChangeDir = 1005  #
cmRevert = 1006  # Used by TChDirDialog internally
cmDirSelection = 1007  # Used by TChDirDialog internally
cmFileFocused = 102  # A new file was focused in the FileList
cmFileDoubleClicked = 103  # A file was selected in the FileList

cdNormal = 0x0000  # Option to use dialog immediately
cdNoLoadDir = 0x0001  # Option to init the dialog to store on a stream
cdHelpButton = 0x0002  # Put a help button in the dialog
