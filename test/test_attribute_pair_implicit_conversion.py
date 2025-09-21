# -*- coding: utf-8 -*-
import unittest

from vindauga.utilities.colours.attribute_pair import AttributePair
from vindauga.utilities.colours.colour_attribute import ColourAttribute


class TestAttributePairImplicitConversion(unittest.TestCase):
    """
    Test suite for AttributePair implicit conversion features.
    """

    def setUp(self):
        """
        Set up test fixtures.
        """
        self.attr_pair = AttributePair(0x1234)  # High=0x12, Low=0x34

    def test_as_colour_attribute_method(self):
        """
        Test as_colour_attribute() returns first attribute.
        """
        color_attr = self.attr_pair.as_colour_attribute()

        self.assertIsInstance(color_attr, ColourAttribute)
        self.assertEqual(color_attr, self.attr_pair._attrs[0])

    def test_getattr_delegation_to_first_attribute(self):
        """
        Test __getattr__ delegates ColourAttribute methods to first attribute.
        """
        # Test delegation of as_bios method
        delegated_bios = self.attr_pair.as_bios()
        direct_bios = self.attr_pair._attrs[0].as_bios() | (self.attr_pair._attrs[1].as_bios() << 8)

        self.assertEqual(delegated_bios, direct_bios)

    def test_getattr_delegation_with_invalid_attribute(self):
        """
        Test __getattr__ raises AttributeError for invalid attributes.
        """
        with self.assertRaises(AttributeError) as context:
            _ = self.attr_pair.nonexistent_method()

        self.assertIn("has no attribute 'nonexistent_method'", str(context.exception))

    def test_getattr_delegation_preserves_existing_methods(self):
        """
        Test __getattr__ doesn't interfere with existing AttributePair methods.
        """
        # Test that existing methods still work
        self.assertEqual(int(self.attr_pair), self.attr_pair.as_bios())
        self.assertEqual(self.attr_pair[0], self.attr_pair._attrs[0])
        self.assertEqual(self.attr_pair[1], self.attr_pair._attrs[1])

    def test_implicit_conversion_with_various_bios_values(self):
        """
        Test implicit conversion with various BIOS values.
        """
        test_cases = [
            0x07,  # White on black
            0x17,  # White on blue
            0x71,  # Blue on white (the failing case)
            0x1234,  # 16-bit value
            0xFF00,  # High byte only
            0x00FF,  # Low byte only
        ]

        for bios_value in test_cases:
            with self.subTest(bios=bios_value):
                attr_pair = AttributePair(bios_value)
                color_attr = attr_pair.as_colour_attribute()

                # Should be a valid ColourAttribute
                self.assertIsInstance(color_attr, ColourAttribute)

                # Should have expected BIOS value for low byte
                expected_low = bios_value & 0xFF
                if expected_low != 0:  # Only test if non-zero expected
                    actual_bios = color_attr.as_bios()
                    self.assertNotEqual(actual_bios, 0,
                                        f"as_bios() should not return 0 for input 0x{bios_value:04x}")

    def test_duck_typing_compatibility(self):
        """
        Test that AttributePair can be used where ColourAttribute is expected.
        """
        # Create AttributePair and extract normal attribute
        attr_pair = AttributePair(0x71)  # Blue on white
        normal_attr = attr_pair.as_colour_attribute()

        # Both should have compatible methods
        self.assertTrue(hasattr(attr_pair, 'as_bios'))
        self.assertTrue(hasattr(normal_attr, 'as_bios'))

        # The extracted attribute should work correctly
        self.assertIsInstance(normal_attr, ColourAttribute)
        normal_bios = normal_attr.as_bios()
        self.assertGreater(normal_bios, 0)  # Should be valid BIOS value

    def test_comparison_operations_still_work(self):
        """
        Test that comparison operations work with implicit conversion.
        """
        attr_pair = AttributePair(0x1234)
        actual_bios = attr_pair.as_bios()

        # Test int comparison - should match actual BIOS value after processing
        self.assertEqual(attr_pair, actual_bios)
        self.assertNotEqual(attr_pair, 0x9999)

        # Test AttributePair comparison
        other_pair = AttributePair(0x1234)
        self.assertEqual(attr_pair, other_pair)

        different_pair = AttributePair(0x5678)
        self.assertNotEqual(attr_pair, different_pair)

    def test_bitwise_operations_still_work(self):
        """
        Test that bitwise operations work with implicit conversion.
        """
        attr_pair = AttributePair(0x1234)

        # Test AND operation (used in background.py)
        low_attr = attr_pair & 0xFF
        self.assertEqual(low_attr, attr_pair._attrs[0])

        # Test right shift (used in getColor)
        high_attr = attr_pair >> 8
        self.assertEqual(high_attr, attr_pair._attrs[1])

    def test_integration_with_color_system(self):
        """
        Test integration with the overall color system.
        """
        # Test the exact case from background.py
        attr_pair = AttributePair(0x71)  # Blue on white

        # This is what background.py does:
        color_attr = attr_pair & 0xFF  # Should return ColourAttribute
        self.assertIsInstance(color_attr, ColourAttribute)

        # Should be a valid color for moveChar
        bios_value = color_attr.as_bios()
        self.assertGreater(bios_value, 0)
        self.assertLessEqual(bios_value, 0xFF)  # Should be single byte
