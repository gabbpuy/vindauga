# -*- coding: utf-8 -*-
"""
Unit tests for color conversion utilities in vindauga.

This module tests the critical color conversion pipeline that converts
TVision palette indices through to BIOS format for ncurses display.
"""
import unittest

from vindauga.utilities.colours.attribute_pair import AttributePair
from vindauga.utilities.colours.colour_attribute import ColourAttribute
from vindauga.utilities.colours.desired_colour import DesiredColour


class TestColorConversion(unittest.TestCase):
    """
    Test suite for color conversion utilities.
    """

    def test_attribute_pair_constructor_with_bios(self):
        """
        Test AttributePair constructor with BIOS value.
        """
        # Test case: colorPair=0x71 (113) from getColor logs
        # Expected: fg=0x71, bg=0x00 (since 113 >> 8 = 0)
        attr_pair = AttributePair(113)  # 0x71
        
        # Check internal structure
        self.assertEqual(len(attr_pair._attrs), 2)
        
        # Test as_bios() method
        bios_result = attr_pair.as_bios()
        
        # This should NOT be 0 if working correctly
        self.assertNotEqual(bios_result, 0, "as_bios() should not return 0 for valid input")

    def test_attribute_pair_bios_roundtrip(self):
        """
        Test that BIOS values can be converted and back.
        """
        test_values = [0x07, 0x17, 0x71, 0x1f, 0x74]
        
        for original_bios in test_values:
            with self.subTest(bios=original_bios):
                attr_pair = AttributePair(original_bios)
                converted_bios = attr_pair.as_bios()
                self.assertEqual(int(converted_bios), original_bios)

    def test_colour_attribute_constructor(self):
        """
        Test ColourAttribute constructor behavior.
        """
        # Test with the value that AttributePair passes to ColourAttribute
        color_attr = ColourAttribute(113)  # What AttributePair(113) passes to ColourAttribute

        # Test as_bios()
        bios_result = color_attr.as_bios()
        # ColourAttribute(113) should return 0 since it interprets 113 as RGB value, not BIOS
        self.assertEqual(int(bios_result), 0)

    def test_colour_attribute_from_bios(self):
        """
        Test ColourAttribute.from_bios() constructor.
        """
        # Test the proper constructor for BIOS values
        color_attr = ColourAttribute.from_bios(113)  # 0x71

        # Test as_bios()
        bios_result = color_attr.as_bios()
        # from_bios(113) should roundtrip back to 113
        self.assertEqual(int(bios_result), 113)

    def test_tvision_expected_behavior(self):
        """
        Test expected TVision color behavior.
        """
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
                # Test AttributePair path
                attr_pair = AttributePair(bios)
                result_bios = attr_pair.as_bios()
                result_fg = int(result_bios) & 0x0F
                result_bg = (int(result_bios) >> 4) & 0x0F

                self.assertEqual(result_fg, expected_fg)
                self.assertEqual(result_bg, expected_bg)

                # Test ColourAttribute.from_bios path
                color_attr = ColourAttribute.from_bios(bios)
                result_bios2 = color_attr.as_bios()
                result_fg2 = int(result_bios2) & 0x0F
                result_bg2 = (int(result_bios2) >> 4) & 0x0F

                self.assertEqual(result_fg2, expected_fg)
                self.assertEqual(result_bg2, expected_bg)

    def test_palette_value_113_analysis(self):
        """
        Deep dive analysis of the failing value 113.
        """
        # Test the exact failing case
        attr_pair = AttributePair(113)
        bios_value = attr_pair.as_bios()

        # Should return 113 for roundtrip
        self.assertEqual(int(bios_value), 113)

    def test_desired_colour_behavior(self):
        """
        Test DesiredColour behavior which AttributePair uses.
        """
        # Test creating DesiredColour with different values
        test_values = [0, 1, 7, 15, 113]

        for value in test_values:
            desired = DesiredColour(value)

            # Test that basic methods work
            self.assertIsInstance(desired.is_bios(), bool)
            self.assertIsInstance(desired.is_default(), bool)
            self.assertIsInstance(desired.is_rgb(), bool)

            if hasattr(desired, 'as_bios'):
                bios_val = desired.as_bios()
                self.assertIsNotNone(bios_val)
