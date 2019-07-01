# -*- coding: utf-8 -*-

ufUpdate = 0x01
ufLine = 0x02
ufView = 0x04

smExtend = 0x01
smDouble = 0x02

sfSearchFailed = 0xFFFFFFFF

cmFind = 82
cmReplace = 83
cmSearchAgain = 84

cmCharLeft = 500
cmCharRight = 501
cmWordLeft = 502
cmWordRight = 503
cmLineStart = 504
cmLineEnd = 505
cmLineUp = 506
cmLineDown = 507
cmPageUp = 508
cmPageDown = 509
cmTextStart = 510
cmTextEnd = 511
cmNewLine = 512
cmBackSpace = 513
cmDelChar = 514
cmDelWord = 515
cmDelStart = 516
cmDelEnd = 517
cmDelLine = 518
cmInsMode = 519
cmStartSelect = 520
cmHideSelect = 521
cmIndentMode = 522
cmUpdateTitle = 523

# @see Editor::doSearchReplace
edOutOfMemory = 0

# @see Editor::doSearchReplace
edReadError = 1

# @see Editor::doSearchReplace
edWriteError = 2

# @see Editor::doSearchReplace
edCreateError = 3

# @see Editor::doSearchReplace
edSaveModify = 4

# @see Editor::doSearchReplace
edSaveUntitled = 5

# @see Editor::doSearchReplace
edSaveAs = 6

# @see Editor::doSearchReplace
edFind = 7

# @see Editor::doSearchReplace
edSearchFailed = 8

# @see Editor::doSearchReplace
edReplace = 9

# @see Editor::doSearchReplace
edReplacePrompt = 10

# Default to case-sensitive search.
# @see Editor::editorFlags
efCaseSensitive = 0x0001

# Default to whole words only search.
# @see Editor::editorFlags
efWholeWordsOnly = 0x0002

# Prompt on replace.
# @see Editor::editorFlags
efPromptOnReplace = 0x0004

# Replace all occurrences.
# @see Editor::editorFlags
efReplaceAll = 0x0008

# Do replace.
# @see Editor::editorFlags
efDoReplace = 0x0010

# Create backup files with a trailing ~ on saves.
# @see Editor::editorFlags
efBackupFiles = 0x0100

# Maximum allowed line length for _text in a Editor view.
maxLineLength = 1024
