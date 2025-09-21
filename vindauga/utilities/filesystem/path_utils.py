# -*- coding: utf-8 -*-
import os
from typing import Tuple, Union


def fexpand(path: Union[str, bytes]) -> str:
    """Expand and normalize a file path."""
    return os.path.normpath(os.path.expanduser(path))


def splitPath(path) -> Tuple[str, str]:
    """Split path into directory and filename, ensuring directory ends with separator."""
    dirname, filename = os.path.split(path)
    if not dirname:
        dirname = '.'
    if not dirname.endswith(os.path.sep):
        dirname += os.path.sep
    return dirname, filename


def getCurDir() -> str:
    """Get current directory with trailing separator."""
    theDir = os.path.normpath(os.getcwd())
    if not theDir.endswith(os.path.sep):
        theDir += os.path.sep
    return theDir


def isWild(f: str) -> bool:
    """Check if filename contains wildcards."""
    return any(c in {'?', '*'} for c in reversed(f))


def isRelativePath(path) -> bool:
    """Check if path is relative (not absolute)."""
    return not os.path.isabs(path)


def isValidFileName(fileName: str) -> bool:
    """Check if filename is valid and accessible."""
    if os.path.exists(fileName):
        return os.access(fileName, os.R_OK)
    try:
        with open(fileName, 'w'):
            pass
        os.remove(fileName)
        return True
    except IOError:
        return False


def isDirectory(path) -> bool:
    """Check if path is a directory."""
    return os.path.isdir(os.path.dirname(path))