# -*- coding: utf-8 -*-
from typing import Optional
import wcwidth


def hotKey(s: str) -> Optional[str]:
    """
    Return the hotkey from a '~T~ilde' formatted string

    :param s: String
    :return: The escaped character or None
    """
    head, _, tail = s.partition('~')
    if tail:
        return tail[0].upper()
    return None


def nameLength(name: str) -> int:
    """
    Remove the '~' from strings and count the letters.
    :param name: String to count
    :return: length of name without '~'
    """
    return wcwidth.wcswidth(name) - name.count('~')