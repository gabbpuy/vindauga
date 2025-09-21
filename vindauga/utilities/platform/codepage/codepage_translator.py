# -*- coding: utf-8 -*-
from dataclasses import field, dataclass
import logging
import os
from typing import Sequence, Dict

from vindauga.utilities.platform.events.utf8_handler import utf8_bytes_left

logger = logging.getLogger(__name__)

cp437_to_utf8 = (
    "\0", "☺", "☻", "♥", "♦", "♣", "♠", "•", "◘", "○", "◙", "♂", "♀", "♪", "♫", "☼",
    "►", "◄", "↕", "‼", "¶", "§", "▬", "↨", "↑", "↓", "→", "←", "∟", "↔", "▲", "▼",
    " ", "!", "\"", "#", "$", "%", "&", "'", "(", ")", "*", "+", ",", "-", ".", "/",
    "0", "1", "2", "3", "4", "5", "6", "7", "8", "9", ":", ";", "<", "=", ">", "?",
    "@", "A", "B", "C", "D", "E", "F", "G", "H", "I", "J", "K", "L", "M", "N", "O",
    "P", "Q", "R", "S", "T", "U", "V", "W", "X", "Y", "Z", "[", "\\", "]", "^", "_",
    "`", "a", "b", "c", "d", "e", "f", "g", "h", "i", "j", "k", "l", "m", "n", "o",
    "p", "q", "r", "s", "t", "u", "v", "w", "x", "y", "z", "{", "|", "}", "~", "⌂",
    "Ç", "ü", "é", "â", "ä", "à", "å", "ç", "ê", "ë", "è", "ï", "î", "ì", "Ä", "Å",
    "É", "æ", "Æ", "ô", "ö", "ò", "û", "ù", "ÿ", "Ö", "Ü", "¢", "£", "¥", "₧", "ƒ",
    "á", "í", "ó", "ú", "ñ", "Ñ", "ª", "º", "¿", "⌐", "¬", "½", "¼", "¡", "«", "»",
    "░", "▒", "▓", "│", "┤", "╡", "╢", "╖", "╕", "╣", "║", "╗", "╝", "╜", "╛", "┐",
    "└", "┴", "┬", "├", "─", "┼", "╞", "╟", "╚", "╔", "╩", "╦", "╠", "═", "╬", "╧",
    "╨", "╤", "╥", "╙", "╘", "╒", "╓", "╫", "╪", "┘", "┌", "█", "▄", "▌", "▐", "▀",
    "α", "ß", "Γ", "π", "Σ", "σ", "µ", "τ", "Φ", "Θ", "Ω", "δ", "∞", "φ", "ε", "∩",
    "≡", "±", "≥", "≤", "⌠", "⌡", "÷", "≈", "°", "∙", "·", "√", "ⁿ", "²", "■", " "
)

cp850_to_utf8 = (
    "\0", "☺", "☻", "♥", "♦", "♣", "♠", "•", "◘", "○", "◙", "♂", "♀", "♪", "♫", "☼",
    "►", "◄", "↕", "‼", "¶", "§", "▬", "↨", "↑", "↓", "→", "←", "∟", "↔", "▲", "▼",
    " ", "!", "\"", "#", "$", "%", "&", "'", "(", ")", "*", "+", ",", "-", ".", "/",
    "0", "1", "2", "3", "4", "5", "6", "7", "8", "9", ":", ";", "<", "=", ">", "?",
    "@", "A", "B", "C", "D", "E", "F", "G", "H", "I", "J", "K", "L", "M", "N", "O",
    "P", "Q", "R", "S", "T", "U", "V", "W", "X", "Y", "Z", "[", "\\", "]", "^", "_",
    "`", "a", "b", "c", "d", "e", "f", "g", "h", "i", "j", "k", "l", "m", "n", "o",
    "p", "q", "r", "s", "t", "u", "v", "w", "x", "y", "z", "{", "|", "}", "~", "⌂",
    "Ç", "ü", "é", "â", "ä", "à", "å", "ç", "ê", "ë", "è", "ï", "î", "ì", "Ä", "Å",
    "É", "æ", "Æ", "ô", "ö", "ò", "û", "ù", "ÿ", "Ö", "Ü", "ø", "£", "Ø", "×", "ƒ",
    "á", "í", "ó", "ú", "ñ", "Ñ", "ª", "º", "¿", "®", "¬", "½", "¼", "¡", "«", "»",
    "░", "▒", "▓", "│", "┤", "Á", "Â", "À", "©", "╣", "║", "╗", "╝", "¢", "¥", "┐",
    "└", "┴", "┬", "├", "─", "┼", "ã", "Ã", "╚", "╔", "╩", "╦", "╠", "═", "╬", "¤",
    "ð", "Ð", "Ê", "Ë", "È", "ı", "Í", "Î", "Ï", "┘", "┌", "█", "▄", "¦", "Ì", "▀",
    "Ó", "ß", "Ô", "Ò", "õ", "Õ", "µ", "þ", "Þ", "Ú", "Û", "Ù", "ý", "Ý", "¯", "´",
    "-", "±", "‗", "¾", "¶", "§", "÷", "¸", "°", "¨", "·", "¹", "³", "²", "■", " "
)


def string_as_int(s: str) -> int:
    res = 0
    for i, char in enumerate(s):
        res |= (ord(char) << (8 * i))
    return res


def init_map(to_utf_8: Sequence[str]) -> Dict[int, str]:
    char_map = {}
    for i in range(256):
        ch = to_utf_8[i]
        length = 1 + utf8_bytes_left(ord(ch))
        char_map[string_as_int(ch)] = chr(i)
    return char_map


@dataclass
class CodepageTable:
    cp: str
    to_utf_8: Sequence[str] = field(default_factory=list)
    from_utf_8: Dict[int, str] = field(default_factory=dict)

    def __init__(self, cp: str, to_utf_8: Sequence[str]):
        self.cp = cp
        self.to_utf_8 = to_utf_8
        self.from_utf_8 = init_map(to_utf_8)


class CodepageTranslator:
    def __init__(self):
        self.current_from_utf8 = {}
        self.current_to_utf8 = cp850_to_utf8

    def init(self):
        cp = os.environ.get('VINDAUGA_CODE_PAGE', '437')
        tables = [
            CodepageTable('437', cp437_to_utf8),
            CodepageTable('850', cp850_to_utf8),
        ]
        for table in tables:
            if table.cp == cp:
                self.current_from_utf8 = table.from_utf_8
                self.current_to_utf8 = table.to_utf_8
                return

    def to_packed_utf8(self, c: str) -> int:
        return self.current_to_utf8[c]

    def from_utf8(self, s: str) -> str:
        self.init()

        return self.current_from_utf8.get(string_as_int(s), '\x00')

    def printable_from_utf8(self, s: str) -> str:
        c = self.from_utf8(s)
        if c < ' ':
            return '\0'
        return c
