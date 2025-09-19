# -*- coding: utf-8 -*-
import wcwidth


def utf8_bytes_left(first_byte: int) -> int:
    """
    Calculate how many more bytes are needed for UTF-8 character
    """
    if first_byte < 0:
        return 0

    byte = first_byte & 0xFF

    # Single byte ASCII (0xxxxxxx)
    if (byte & 0x80) == 0:
        return 0

    # Multi-byte sequences
    if (byte & 0xE0) == 0xC0:  # 110xxxxx - 2 byte sequence
        return 1
    elif (byte & 0xF0) == 0xE0:  # 1110xxxx - 3 byte sequence
        return 2
    elif (byte & 0xF8) == 0xF0:  # 11110xxx - 4 byte sequence
        return 3

    # Invalid UTF-8 start byte
    return 0


def read_utf8_char(get_char_func, first_byte: int) -> tuple[str, int]:
    """
    Read complete UTF-8 character starting with first_byte
    Returns (character_string, bytes_consumed)

    :param get_char_func: function to get character data
    :param first_byte: first byte to read

    :return: tuple of (character_string, bytes_consumed)
    """
    if first_byte < 0:
        return '', 0

    bytes_needed = utf8_bytes_left(first_byte)
    if bytes_needed == 0:
        # Single byte ASCII
        return chr(first_byte), 1

    # Collect UTF-8 bytes
    utf8_bytes = [first_byte]

    for i in range(bytes_needed):
        next_byte = get_char_func()
        if next_byte < 0:
            # Incomplete sequence - return what we have
            break
        utf8_bytes.append(next_byte)

    # Convert bytes to string
    try:
        char_bytes = bytes(utf8_bytes)
        return char_bytes.decode('utf-8'), len(utf8_bytes)
    except UnicodeDecodeError:
        # Invalid UTF-8 - return replacement character
        return '�', len(utf8_bytes)


def validate_utf8_sequence(byte_sequence: list[int]) -> bool:
    """
    Validate if byte sequence forms valid UTF-8

    :param byte_sequence: list of byte sequence
    """
    if not byte_sequence:
        return False

    try:
        bytes(byte_sequence).decode('utf-8')
        return True
    except UnicodeDecodeError:
        return False


def is_utf8_continuation(byte_val: int) -> bool:
    """
    Check if byte is a UTF-8 continuation byte (10xxxxxx)

    :param byte_val: byte value
    """
    return (byte_val & 0xC0) == 0x80


def get_utf8_char_width(char: str) -> int:
    """
    Get display width of UTF-8 character using wcwidth

    :param char: character string
    """
    if not char:
        return 0

    width = wcwidth.wcswidth(char)
    return width if width is not None else 1


class UTF8CharacterAssembler:
    """
    Assembles UTF-8 characters from byte stream
    """
    def __init__(self):
        self._partial_bytes: list[int] = []
        self._expected_length = 0

    def add_byte(self, byte_val: int) -> str | None:
        """
        Add byte to character assembly
        Returns completed character or None if still assembling

        :param byte_val: byte value
        """
        if byte_val < 0:
            return None

        # If we're not in the middle of a multi-byte sequence
        if not self._partial_bytes:
            bytes_needed = utf8_bytes_left(byte_val)

            if bytes_needed == 0:
                # Complete single-byte character
                return chr(byte_val) if 0 <= byte_val <= 127 else '�'

            # Start of multi-byte sequence
            self._partial_bytes = [byte_val]
            self._expected_length = bytes_needed + 1
            return None

        # Continuation of multi-byte sequence
        if not is_utf8_continuation(byte_val):
            # Invalid continuation - reset and try as new character
            self._partial_bytes = []
            self._expected_length = 0
            return self.add_byte(byte_val)  # Recursive call for new start

        self._partial_bytes.append(byte_val)

        # Check if sequence is complete
        if len(self._partial_bytes) >= self._expected_length:
            # Try to decode
            try:
                char = bytes(self._partial_bytes).decode('utf-8')
                self._partial_bytes = []
                self._expected_length = 0
                return char
            except UnicodeDecodeError:
                # Invalid sequence
                self._partial_bytes = []
                self._expected_length = 0
                return '�'

        # Still need more bytes
        return None

    def flush(self) -> str | None:
        """
        Flush any incomplete sequence
        Returns replacement character if there was an incomplete sequence
        """
        if self._partial_bytes:
            self._partial_bytes = []
            self._expected_length = 0
            return '�'
        return None

    def reset(self):
        """
        Reset assembler state
        """
        self._partial_bytes = []
        self._expected_length = 0
