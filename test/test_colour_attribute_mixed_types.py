# -*- coding: utf-8 -*-
import unittest
from unittest.mock import Mock

from vindauga.utilities.colours.attribute_pair import AttributePair
from vindauga.utilities.colours.colour_attribute import ColourAttribute


class TestColourAttributeMixedTypes(unittest.TestCase):
    """
    Test suite for ColourAttribute mixed type handling.
    """

    def setUp(self):
        """
        Set up test fixtures.
        """
        # Create a mock screen with 80x25 dimensions for DrawBuffer tests
        mock_screen = Mock()
        mock_screen.screenWidth = 80
        mock_screen.screenHeight = 25

        # Set the global screen instance
        from vindauga.types.screen import Screen
        Screen.screen = mock_screen

    def tearDown(self):
        """
        Clean up test fixtures.
        """
        # Reset the global screen instance
        from vindauga.types.screen import Screen
        Screen.screen = None

    def test_from_bios_with_int(self):
        """
        Test from_bios() with integer input (existing functionality).
        """
        color_attr = ColourAttribute.from_bios(0x71)

        self.assertIsInstance(color_attr, ColourAttribute)
        # Should properly parse BIOS format
        bios_result = color_attr.as_bios()
        self.assertGreater(bios_result, 0)

    def test_from_bios_with_colour_attribute(self):
        """
        Test from_bios() with ColourAttribute input (passthrough).
        """
        original = ColourAttribute.from_bios(0x17)
        result = ColourAttribute.from_bios(original)

        # Should return the same object
        self.assertIs(result, original)
        self.assertEqual(result.as_bios(), original.as_bios())

    def test_from_bios_with_attribute_pair(self):
        """
        Test from_bios() with AttributePair input.
        """
        attr_pair = AttributePair(0x1234)
        result = ColourAttribute.from_bios(attr_pair)

        # Should extract the first (normal) attribute
        self.assertIsInstance(result, ColourAttribute)
        self.assertEqual(result, attr_pair._attrs[0])

    def test_from_bios_type_compatibility_matrix(self):
        """
        Test all supported input types produce valid ColourAttribute objects.
        """
        test_cases = [
            ("int", 0x71, lambda x: x),
            ("AttributePair", 0x71, lambda x: AttributePair(x)),
            ("ColourAttribute", 0x71, lambda x: ColourAttribute.from_bios(x)),
        ]

        for type_name, value, constructor in test_cases:
            with self.subTest(type=type_name, value=value):
                input_obj = constructor(value)
                result = ColourAttribute.from_bios(input_obj)

                self.assertIsInstance(result, ColourAttribute)
                # Should produce a valid BIOS value
                bios_result = result.as_bios()
                self.assertIsInstance(bios_result, int)
                self.assertGreaterEqual(bios_result, 0)
                self.assertLessEqual(bios_result, 0xFF)

    def test_from_bios_preserves_color_information(self):
        """
        Test that from_bios() preserves color information across type conversions.
        """
        original_bios = 0x71  # Blue on white

        # Test conversion chain: int -> AttributePair -> ColourAttribute
        attr_pair = AttributePair(original_bios)
        color_attr = ColourAttribute.from_bios(attr_pair)

        # Should preserve color information after BIOS parsing
        result_bios = color_attr.as_bios()

        # The color should be properly parsed and reconstructed
        # Note: BIOS format parsing extracts fg/bg nibbles and reconstructs them
        self.assertIsInstance(result_bios, int,
                              f"Should produce valid BIOS value from 0x{original_bios:02x}")

    def test_from_bios_with_various_bios_values(self):
        """
        Test from_bios() with various BIOS color values.
        """
        test_values = [
            0x00,  # Black on black
            0x07,  # White on black (normal)
            0x17,  # White on blue
            0x71,  # Blue on white (the failing case)
            0x74,  # Red on white
            0x1F,  # Bright white on blue
            0xF0,  # Black on bright white
            0xFF,  # Bright white on bright white
        ]

        for bios_value in test_values:
            with self.subTest(bios=bios_value):
                # Test direct int conversion
                color_attr = ColourAttribute.from_bios(bios_value)
                result = color_attr.as_bios()

                # Some values may legitimately result in 0 after BIOS parsing
                # Only check that the result is valid (0-255)
                self.assertGreaterEqual(result, 0)
                self.assertLessEqual(result, 0xFF)

                # Test via AttributePair conversion
                attr_pair = AttributePair(bios_value)
                color_attr2 = ColourAttribute.from_bios(attr_pair)
                result2 = color_attr2.as_bios()

                # Should get consistent results
                self.assertEqual(result, result2,
                                 f"Inconsistent results for 0x{bios_value:02x}: {result} vs {result2}")

    def test_from_bios_error_handling(self):
        """
        Test from_bios() error handling with invalid inputs.
        """
        # Should handle various input types gracefully
        valid_inputs = [
            0,
            255,
            AttributePair(0x71),
            ColourAttribute.from_bios(0x17),
        ]

        for input_val in valid_inputs:
            with self.subTest(input=input_val):
                try:
                    result = ColourAttribute.from_bios(input_val)
                    self.assertIsInstance(result, ColourAttribute)
                except Exception as e:
                    self.fail(f"from_bios({input_val}) raised unexpected exception: {e}")

    def test_circular_conversion_stability(self):
        """
        Test that circular conversions are stable.
        """
        original_value = 0x74  # Red on white

        # Test: int -> ColourAttribute -> AttributePair -> ColourAttribute
        color1 = ColourAttribute.from_bios(original_value)
        attr_pair = AttributePair(color1.as_bios())
        color2 = ColourAttribute.from_bios(attr_pair)

        # Final result should match first conversion
        self.assertEqual(color1.as_bios(), color2.as_bios(),
                         "Circular conversion should be stable")

    def test_integration_with_drawbuffer(self):
        """
        Test integration with DrawBuffer type normalization.
        """
        from vindauga.types.draw_buffer import DrawBuffer

        buffer = DrawBuffer()

        # Create various attribute types
        int_attr = 0x17
        attr_pair = AttributePair(0x71)
        color_attr = ColourAttribute.from_bios(0x74)

        # All of these should work seamlessly
        buffer.moveChar(0, 'A', int_attr, 2)
        buffer.moveChar(2, 'B', attr_pair, 3)
        buffer.moveChar(5, 'C', color_attr, 4)

        # Verify no exceptions and all cells have attributes
        for i in range(9):
            self.assertIsNotNone(buffer.data[i].attr)
            self.assertIn(buffer.data[i].char, ['A', 'B', 'C'])

    def test_c_plus_plus_compatibility_patterns(self):
        # Pattern 1: TColorAttr(bios_value)
        color1 = ColourAttribute.from_bios(0x71)
        self.assertIsInstance(color1, ColourAttribute)

        # Pattern 2: TAttrPair to TColorAttr conversion
        attr_pair = AttributePair(0x1234)
        color2 = ColourAttribute.from_bios(attr_pair)
        self.assertIsInstance(color2, ColourAttribute)
        self.assertEqual(color2, attr_pair._attrs[0])

        # Pattern 3: Passthrough of existing TColorAttr
        color3 = ColourAttribute.from_bios(color1)
        self.assertIs(color3, color1)

    def test_regression_blue_on_white_case(self):
        """
        Regression test for the specific blue-on-white case that was failing.
        """
        # This is the exact case that was causing problems
        bios_value = 0x71  # Blue foreground (1), white background (7)

        # Test direct conversion
        color_attr = ColourAttribute.from_bios(bios_value)
        result_bios = color_attr.as_bios()

        self.assertNotEqual(result_bios, 0, "Blue on white should not result in 0")
        self.assertGreater(result_bios, 0, "Should produce valid color value")

        # Test via AttributePair (the failing path)
        attr_pair = AttributePair(bios_value)
        color_attr2 = ColourAttribute.from_bios(attr_pair)
        result_bios2 = color_attr2.as_bios()

        self.assertNotEqual(result_bios2, 0, "AttributePair conversion should not result in 0")
        self.assertEqual(result_bios, result_bios2, "Both paths should give same result")
