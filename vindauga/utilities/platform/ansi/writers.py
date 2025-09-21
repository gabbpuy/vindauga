# -*- coding: utf-8 -*-
from vindauga.utilities.colours.style_mask import StyleMask

from .attribute import TermAttribute
from .colour import TermColour, TermColourTypes

CSI = '\x1b['
bold_on_off = '1', '22'
italic_on_off = '3', '23'
underline_on_off = '4', '24'
blink_on_off = '5', '25'
reverse_on_off = '7', '27'
strike_on_off = '9', '29'


def write_flag(parts: list, attr: TermAttribute, last_attr: TermAttribute, mask: StyleMask, on_off: tuple[str]):
    """
    Append flag change directly to the parts list
    """
    mask_int = int(mask)
    attr_masked = int(attr.style) & mask_int
    last_attr_masked = int(last_attr.style) & mask_int
    
    if attr_masked != last_attr_masked:
        if attr_masked:
            parts.append(on_off[0])
        else:
            parts.append(on_off[1])
        parts.append(';')


def write_colour(parts: list, colour: TermColour, is_fg: bool):
    """
    Append color change directly to the parts list
    """
    match colour.type:
        case TermColourTypes.Default:
            if is_fg:
                parts.append('39;')
            else:
                parts.append('49;')
        case TermColourTypes.Indexed:
            if colour.idx >= 16:
                # Handle split_sgr: if last part ends with ';', replace with 'm' and add CSI
                if parts and parts[-1].endswith(';'):
                    parts[-1] = parts[-1][:-1] + 'm'
                    parts.append(CSI)
                
                if is_fg:
                    parts.append('38;5;')
                else:
                    parts.append('48;5;')
                parts.append(str(colour.idx))
                parts.append(';')
                
                # Second split_sgr: always ends with ';' so replace with 'm' and add CSI
                parts[-1] = 'm'
                parts.append(CSI)
            else:
                if colour.idx >= 8:
                    code = colour.idx - 8 + (90 if is_fg else 100)
                    parts.append(str(code))
                else:
                    code = colour.idx + (30 if is_fg else 40)
                    parts.append(str(code))
                parts.append(';')
        case TermColourTypes.RGB:
            # Handle split_sgr: if last part ends with ';', replace with 'm' and add CSI
            if parts and parts[-1].endswith(';'):
                parts[-1] = parts[-1][:-1] + 'm'
                parts.append(CSI)
            
            if is_fg:
                parts.append('38;2;')
            else:
                parts.append('48;2;')
            for i in range(3):
                parts.append(str(colour.bgr[2 - i]))
                parts.append(';')
                
            # Second split_sgr: always ends with ';' so replace with 'm' and add CSI  
            parts[-1] = 'm'
            parts.append(CSI)
        case TermColourTypes.NoColor:
            pass


def write_attributes(attribute: TermAttribute, last_attribute: TermAttribute) -> str:
    parts = [CSI]
    if attribute != last_attribute:
        write_flag(parts, attribute, last_attribute, StyleMask.Bold, bold_on_off)
        write_flag(parts, attribute, last_attribute, StyleMask.Italic, italic_on_off)
        write_flag(parts, attribute, last_attribute, StyleMask.Underline, underline_on_off)
        write_flag(parts, attribute, last_attribute, StyleMask.Blink, blink_on_off)
        write_flag(parts, attribute, last_attribute, StyleMask.Reverse, reverse_on_off)
        write_flag(parts, attribute, last_attribute, StyleMask.Strike, strike_on_off)

        # Handle colors directly in the same parts list
        if attribute.fg != last_attribute.fg:
            write_colour(parts, attribute.fg, True)
        if attribute.bg != last_attribute.bg:
            write_colour(parts, attribute.bg, False)

    # Final cleanup
    if len(parts) == 1:  # Only CSI, no changes
        return ''
    
    if parts[-1] == ';':
        parts[-1] = 'm'
    elif parts[-1] == CSI:
        # Remove trailing CSI if no attributes were written after it
        parts.pop()
    
    return ''.join(parts)
