# -*- coding: utf-8 -*-
"""
Unit tests for color conversion utilities in vindauga.

This module tests the critical color conversion pipeline that converts
TVision palette indices through to BIOS format for ncurses display.
"""

import unittest
import sys
import os

# Add the parent directory to the path so we can import vindauga modules
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from vindauga.screen_driver.colours.attribute_pair import AttributePair
from vindauga.screen_driver.colours.colour_attribute import ColourAttribute
from vindauga.screen_driver.colours.desired_colour import DesiredColour


class TestColorConversion(unittest.TestCase):
    """Test suite for color conversion utilities."""

    def test_attribute_pair_constructor_with_bios(self):
        """Test AttributePair constructor with BIOS value."""
        # Test case: colorPair=0x71 (113) from getColor logs
        # Expected: fg=0x71, bg=0x00 (since 113 >> 8 = 0)
        attr_pair = AttributePair(113)  # 0x71
        
        # Check internal structure
        self.assertEqual(len(attr_pair._attrs), 2)
        
        # Print debug info for analysis
        print(f"AttributePair(113):")
        print(f"  _attrs[0] (fg): {attr_pair._attrs[0]}")
        print(f"  _attrs[1] (bg): {attr_pair._attrs[1]}")
        
        # Test as_bios() method
        bios_result = attr_pair.as_bios()
        print(f"  as_bios(): 0x{bios_result:02x} ({bios_result})")
        
        # This should NOT be 0 if working correctly
        self.assertNotEqual(bios_result, 0, "as_bios() should not return 0 for valid input")

    def test_attribute_pair_bios_roundtrip(self):
        """Test that BIOS values can be converted and back."""
        test_values = [0x07, 0x17, 0x71, 0x1f, 0x74]
        
        for original_bios in test_values:
            with self.subTest(bios=original_bios):
                attr_pair = AttributePair(original_bios)
                converted_bios = attr_pair.as_bios()
                print(f"BIOS roundtrip: 0x{original_bios:02x} -> AttributePair -> 0x{converted_bios:02x}")

    def test_colour_attribute_constructor(self):
        """Test ColourAttribute constructor behavior."""
        # Test with the value that AttributePair passes to ColourAttribute
        color_attr = ColourAttribute(113)  # What AttributePair(113) passes to ColourAttribute
        
        print(f"ColourAttribute(113):")
        print(f"  _style: {color_attr._style}")
        print(f"  _fg: {color_attr._fg}")  
        print(f"  _bg: {color_attr._bg}")
        
        # Test as_bios()
        bios_result = color_attr.as_bios()
        print(f"  as_bios(): 0x{bios_result:02x} ({bios_result})")

    def test_colour_attribute_from_bios(self):
        """Test ColourAttribute.from_bios() constructor."""
        # Test the proper constructor for BIOS values
        color_attr = ColourAttribute.from_bios(113)  # 0x71
        
        print(f"ColourAttribute.from_bios(113):")
        print(f"  _style: {color_attr._style}")
        print(f"  _fg: {color_attr._fg}")
        print(f"  _bg: {color_attr._bg}")
        
        # Test as_bios()
        bios_result = color_attr.as_bios()
        print(f"  as_bios(): 0x{bios_result:02x} ({bios_result})")

    def test_tvision_expected_behavior(self):
        """Test expected TVision color behavior."""
        # In TVision BIOS format:
        # - Low 4 bits: foreground color (0-15)  
        # - High 4 bits: background color (0-15)
        
        test_cases = [
            (0x07, 7, 0),    # White on black (normal text)
            (0x17, 7, 1),    # White on blue  
            (0x71, 1, 7),    # Blue on white (our failing case)
            (0x1f, 15, 1),   # Bright white on blue
            (0x74, 4, 7),    # Red on white
        ]
        
        for bios, expected_fg, expected_bg in test_cases:
            with self.subTest(bios=bios):
                print(f"\nTesting BIOS 0x{bios:02x}:")
                print(f"  Expected: fg={expected_fg}, bg={expected_bg}")
                
                # Test AttributePair path
                attr_pair = AttributePair(bios)
                result_bios = attr_pair.as_bios()
                result_fg = result_bios & 0x0F
                result_bg = (result_bios >> 4) & 0x0F
                
                print(f"  AttributePair result: 0x{result_bios:02x} (fg={result_fg}, bg={result_bg})")
                
                # Test ColourAttribute.from_bios path  
                color_attr = ColourAttribute.from_bios(bios)
                result_bios2 = color_attr.as_bios()
                result_fg2 = result_bios2 & 0x0F
                result_bg2 = (result_bios2 >> 4) & 0x0F
                
                print(f"  ColourAttribute.from_bios result: 0x{result_bios2:02x} (fg={result_fg2}, bg={result_bg2})")

    def test_palette_value_113_analysis(self):
        """Deep dive analysis of the failing value 113."""
        print(f"\n=== Deep Analysis of Value 113 (0x{113:02x}) ===")
        
        # What should happen:
        # getColor() returns AttributePair(113)
        # AttributePair.as_bios() should return a valid BIOS value
        # Display adapter converts to ncurses colors
        
        # Test the exact failing case
        attr_pair = AttributePair(113)
        bios_value = attr_pair.as_bios()
        
        print(f"1. AttributePair(113).as_bios() = 0x{bios_value:02x}")
        
        if bios_value == 0:
            print("   ❌ PROBLEM: as_bios() returns 0!")
            
            # Analyze why it's returning 0
            fg_attr = attr_pair._attrs[0]
            bg_attr = attr_pair._attrs[1]
            
            print(f"   Analyzing components:")
            print(f"     _attrs[0] (fg): {fg_attr}")
            print(f"     _attrs[1] (bg): {bg_attr}")
            
            # Test individual as_bios() calls
            if hasattr(fg_attr, 'as_bios'):
                fg_bios = fg_attr.as_bios()
                print(f"     _attrs[0].as_bios(): 0x{fg_bios:02x}")
            
            if hasattr(bg_attr, 'as_bios'):
                bg_bios = bg_attr.as_bios()
                print(f"     _attrs[1].as_bios(): 0x{bg_bios:02x}")
        else:
            print(f"   ✅ as_bios() returns valid value: 0x{bios_value:02x}")

    def test_desired_colour_behavior(self):
        """Test DesiredColour behavior which AttributePair uses."""
        print(f"\n=== DesiredColour Analysis ===")
        
        # Test creating DesiredColour with different values
        test_values = [0, 1, 7, 15, 113]
        
        for value in test_values:
            desired = DesiredColour(value)

            print(f"DesiredColour(bit_cast={value}):")
            print(f"  is_bios(): {desired.is_bios()}")
            print(f"  is_default(): {desired.is_default()}")
            print(f"  is_rgb(): {desired.is_rgb()}")
            
            if hasattr(desired, 'as_bios'):
                bios_val = desired.as_bios()
                print(f"  as_bios(): 0x{bios_val:02x}")


if __name__ == '__main__':
    # Run tests with verbose output
    unittest.main(verbosity=2)