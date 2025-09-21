# -*- coding: utf-8 -*-
"""
Unit tests for DrawBuffer type normalization functionality.

Tests the  _normalize_attribute() method and enhanced type handling
in moveChar(), moveStr(), and other DrawBuffer methods.
"""
import time
import unittest
from unittest.mock import Mock

from vindauga.utilities.colours.attribute_pair import AttributePair
from vindauga.utilities.colours.colour_attribute import ColourAttribute
from vindauga.types.draw_buffer import DrawBuffer
from vindauga.types.screen import Screen


class TestDrawBufferTypeNormalization(unittest.TestCase):
    """
    Test suite for DrawBuffer type normalization features.
    """

    def setUp(self):
        """
        Set up test fixtures.
        """
        # Create a mock screen with 80x25 dimensions
        mock_screen = Mock()
        mock_screen.screenWidth = 80
        mock_screen.screenHeight = 25

        # Set the global screen instance
        Screen.screen = mock_screen

        self.buffer = DrawBuffer()
        self.attr_pair = AttributePair(0x1234)
        self.color_attr = ColourAttribute.from_bios(0x71)
        self.int_attr = 0x17

    def tearDown(self):
        """
        Clean up test fixtures.
        """
        # Reset the global screen instance
        Screen.screen = None

    def test_normalize_attribute_with_attribute_pair(self):
        """
        Test _normalize_attribute() converts AttributePair to ColourAttribute.
        """
        normalized = self.buffer._normalize_attribute(self.attr_pair)
        
        self.assertIsInstance(normalized, ColourAttribute)
        self.assertEqual(normalized, self.attr_pair._attrs[0])

    def test_normalize_attribute_with_colour_attribute(self):
        """
        Test _normalize_attribute() passes through ColourAttribute unchanged.
        """
        normalized = self.buffer._normalize_attribute(self.color_attr)
        
        self.assertIsInstance(normalized, ColourAttribute)
        self.assertEqual(normalized, self.color_attr)

    def test_normalize_attribute_with_int(self):
        """
        Test _normalize_attribute() converts int to ColourAttribute.
        """
        normalized = self.buffer._normalize_attribute(self.int_attr)
        
        self.assertIsInstance(normalized, ColourAttribute)
        # Should create ColourAttribute from BIOS value
        expected = ColourAttribute.from_bios(self.int_attr)
        self.assertEqual(normalized.as_bios(), expected.as_bios())

    def test_normalize_attribute_with_none(self):
        """
        Test _normalize_attribute() handles None correctly.
        """
        normalized = self.buffer._normalize_attribute(None)
        
        self.assertIsNone(normalized)

    def test_movechar_with_attribute_pair(self):
        """
        Test moveChar() accepts AttributePair and converts correctly.
        """
        count = self.buffer.moveChar(0, 'X', self.attr_pair, 5)
        
        self.assertEqual(count, 5)
        # Verify that characters were set correctly
        for i in range(5):
            self.assertEqual(self.buffer.data[i].char, 'X')
            # Should have attribute from first element of AttributePair
            self.assertIsNotNone(self.buffer.data[i].attr)

    def test_movechar_with_int(self):
        """
        Test moveChar() accepts int attribute and converts correctly.
        """
        count = self.buffer.moveChar(0, 'Y', self.int_attr, 3)
        
        self.assertEqual(count, 3)
        # Verify that characters were set correctly
        for i in range(3):
            self.assertEqual(self.buffer.data[i].char, 'Y')
            self.assertIsNotNone(self.buffer.data[i].attr)

    def test_movechar_with_colour_attribute(self):
        """
        Test moveChar() works with ColourAttribute (existing functionality).
        """
        count = self.buffer.moveChar(0, 'Z', self.color_attr, 4)
        
        self.assertEqual(count, 4)
        # Verify that characters were set correctly
        for i in range(4):
            self.assertEqual(self.buffer.data[i].char, 'Z')
            self.assertEqual(self.buffer.data[i].attr, self.color_attr)

    def test_movestr_with_attribute_pair(self):
        """
        Test moveStr() accepts AttributePair and converts correctly.
        """
        count = self.buffer.moveStr(0, "Hello", self.attr_pair)
        
        self.assertGreater(count, 0)
        # Verify text was written (exact verification depends on Text.draw_str implementation)

    def test_movestr_with_int(self):
        """
        Test moveStr() accepts int attribute and converts correctly.
        """
        count = self.buffer.moveStr(5, "World", self.int_attr)
        
        self.assertGreater(count, 0)
        # Text should be written starting at position 5

    def test_movestr_with_colour_attribute(self):
        """
        Test moveStr() works with ColourAttribute (existing functionality).
        """
        count = self.buffer.moveStr(10, "Test", self.color_attr)
        
        self.assertGreater(count, 0)

    def test_movestr_with_none_attribute(self):
        """
        Test moveStr() handles None attribute correctly.
        """
        count = self.buffer.moveStr(0, "NoAttr", None)
        
        self.assertGreater(count, 0)

    def test_type_conversion_chain_integration(self):
        """
        Test the complete type conversion chain.
        """
        # Simulate the background.py use case:
        # 1. getColor() returns AttributePair
        # 2. Extract using & 0xFF (should return ColourAttribute)
        # 3. Pass to moveChar()
        
        color_pair = AttributePair(0x71)  # Blue on white
        color_attr = color_pair & 0xFF    # Extract normal attribute
        
        # This should work without errors
        count = self.buffer.moveChar(0, '▓', color_attr, 10)
        
        self.assertEqual(count, 10)
        for i in range(10):
            self.assertEqual(self.buffer.data[i].char, '▓')
            self.assertIsInstance(self.buffer.data[i].attr, ColourAttribute)

    def test_widget_integration_simulation(self):
        """
        Test simulating widget color usage patterns.
        """
        # Simulate button.py usage
        cButton = AttributePair(0x0501)  # Normal button colors
        cShadow = AttributePair(0x0808)  # Shadow colors
        
        # These should all work without type errors
        self.buffer.moveChar(0, ' ', cButton, 10)
        self.buffer.putAttribute(0, cShadow)
        
        # Verify no exceptions were raised and data was set
        self.assertIsNotNone(self.buffer.data[0].attr)

    def test_backward_compatibility(self):
        """
        Test that existing code still works with the changes.
        """
        # Original DrawBuffer usage should still work
        color = ColourAttribute.from_bios(0x07)
        
        count1 = self.buffer.moveChar(0, 'A', color, 5)
        count2 = self.buffer.moveStr(5, "BC", color)
        
        self.assertEqual(count1, 5)
        self.assertGreater(count2, 0)
        
        # Check that data was written correctly
        self.assertEqual(self.buffer.data[0].char, 'A')
        self.assertEqual(self.buffer.data[0].attr, color)

    def test_edge_cases(self):
        """
        Test edge cases and error conditions.
        """
        # Test with zero count
        count = self.buffer.moveChar(0, 'X', self.int_attr, 0)
        self.assertEqual(count, 0)
        
        # Test with out-of-bounds indent
        count = self.buffer.moveChar(100, 'Y', self.int_attr, 5)
        self.assertEqual(count, 0)
        
        # Test with negative indent (current implementation allows this)
        count = self.buffer.moveChar(-5, 'Z', self.int_attr, 5)
        # Note: current implementation doesn't check for negative indent
        self.assertGreaterEqual(count, 0)

    def test_performance_impact(self):
        """
        Test that type conversion doesn't significantly impact performance.
        """
        # Test with large operations
        start_time = time.time()
        for i in range(100):
            self.buffer.moveChar(0, 'P', self.attr_pair, 20)
        conversion_time = time.time() - start_time
        
        # Reset buffer
        self.buffer = DrawBuffer()
        
        # Compare with direct ColourAttribute usage
        start_time = time.time()
        for i in range(100):
            self.buffer.moveChar(0, 'P', self.color_attr, 20)
        direct_time = time.time() - start_time
        
        # Type conversion should not be more than 2x slower
        self.assertLess(conversion_time, direct_time * 2.0,
                        f"Type conversion too slow: {conversion_time:.4f}s vs {direct_time:.4f}s")
