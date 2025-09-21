# -*- coding: utf-8 -*-
import unittest
from unittest.mock import Mock

from vindauga.types.draw_buffer import DrawBuffer
from vindauga.types.rect import Rect
from vindauga.types.view import View
from vindauga.utilities.colours.attribute_pair import AttributePair
from vindauga.utilities.colours.colour_attribute import ColourAttribute
from vindauga.types.screen import Screen


class TestDrawBufferMoveCStr(unittest.TestCase):
    """
    Test DrawBuffer.moveCStr method for hotkey text formatting
    """

    def setUp(self):
        """
        Set up test fixtures
        """
        # Create a mock screen with 80x25 dimensions
        mock_screen = Mock()
        mock_screen.screenWidth = 80
        mock_screen.screenHeight = 25

        # Set the global screen instance
        Screen.screen = mock_screen

        self.buffer = DrawBuffer()
        self.normal_attr = ColourAttribute.from_bios(0x17)  # White on blue
        self.highlight_attr = ColourAttribute.from_bios(0x1F)  # White on white
        self.attrs = AttributePair(pair=(self.normal_attr, self.highlight_attr))

    def tearDown(self):
        """
        Clean up test fixtures
        """
        # Reset the global screen instance
        Screen.screen = None

    def test_simple_text_no_tildes(self):
        """
        Test moveCStr with plain text (no ~ characters)
        """
        text = "Hello World"
        count = self.buffer.moveCStr(0, text, self.attrs)
        
        self.assertEqual(count, len(text))
        result = self._get_buffer_text(count)
        self.assertEqual(result, text)

    def test_single_tilde_toggle(self):
        """
        Test moveCStr with single ~ to toggle highlighting
        """
        text = "~Alt+X~ Exit"
        count = self.buffer.moveCStr(0, text, self.attrs)
        
        # Should render as "Alt+X Exit" (~ characters removed)
        expected = "Alt+X Exit"
        result = self._get_buffer_text(count)
        self.assertEqual(result, expected)

    def test_multiple_tilde_toggles(self):
        """
        Test moveCStr with multiple ~ toggles
        """
        text = "~F1~ Help ~F2~ Save ~F3~ Exit"
        count = self.buffer.moveCStr(0, text, self.attrs)
        
        expected = "F1 Help F2 Save F3 Exit"
        result = self._get_buffer_text(count)
        self.assertEqual(result, expected)

    def test_alt_x_exit_statusbar_item(self):
        """
        Test the specific Alt-X Exit text that was garbling
        """
        text = "~Alt+X~ Exit"
        count = self.buffer.moveCStr(0, text, self.attrs)
        
        expected = "Alt+X Exit"
        result = self._get_buffer_text(count)
        self.assertEqual(result, expected)
        self.assertNotIn("tttt", result, "Text should not be garbled with repeated 't' characters")

    def test_f11_help_statusbar_item(self):
        """
        Test F11 Help statusbar text
        """
        text = "~F11~ Help"
        count = self.buffer.moveCStr(0, text, self.attrs)
        
        expected = "F11 Help"
        result = self._get_buffer_text(count)
        self.assertEqual(result, expected)

    def test_attribute_toggling(self):
        """
        Test that attributes properly toggle between normal and highlight
        """
        text = "~Alt+X~ Exit"
        count = self.buffer.moveCStr(0, text, self.attrs)
        
        # Check that first part (Alt+X) uses highlight, second part (Exit) uses normal
        alt_x_attr = self.buffer.data[0].attr.as_bios() if self.buffer.data[0].attr else 0
        exit_attr = self.buffer.data[7].attr.as_bios() if self.buffer.data[7].attr else 0  # ' Exit' starts at position 7
        
        # Alt+X should use highlight attribute (0x1F), Exit should use normal (0x17)
        self.assertEqual(alt_x_attr, 0x1F, "Alt+X should use highlight attribute")
        self.assertEqual(exit_attr, 0x17, "Exit should use normal attribute")

    def test_empty_text(self):
        """
        Test moveCStr with empty text
        """
        count = self.buffer.moveCStr(0, "", self.attrs)
        self.assertEqual(count, 0)

    def test_only_tildes(self):
        """
        Test moveCStr with only tilde characters
        """
        text = "~~~~"
        count = self.buffer.moveCStr(0, text, self.attrs)
        
        # Should render empty (all tildes consumed as toggles)
        self.assertEqual(count, 0)

    def test_indent_parameter(self):
        """
        Test moveCStr with non-zero indent
        """
        text = "~F1~ Help"
        indent = 5
        count = self.buffer.moveCStr(indent, text, self.attrs)
        
        expected = "F1 Help"
        result = self._get_buffer_text_from_position(indent, count)
        self.assertEqual(result, expected)

    def test_attribute_pair_extraction(self):
        """
        Test that AttributePair attributes are properly extracted
        """
        text = "Test"
        count = self.buffer.moveCStr(0, text, self.attrs)
        
        # All characters should have the normal attribute initially
        for i in range(count):
            cell_attr = self.buffer.data[i].attr
            self.assertIsNotNone(cell_attr, f"Cell {i} should have an attribute")
            self.assertEqual(cell_attr.as_bios(), 0x17, f"Cell {i} should have normal attribute")

    def _get_buffer_text(self, count):
        """
        Helper to extract text from buffer
        """
        return ''.join(cell.char or '' for cell in self.buffer.data[:count])

    def _get_buffer_text_from_position(self, start, count):
        """
        Helper to extract text from buffer starting at position
        """
        return ''.join(cell.char or '' for cell in self.buffer.data[start:start+count])

    def test_statusline_scenario_getcolor_result(self):
        """
        Test moveCStr with AttributePair from getColor() like StatusLine uses
        """
        # Simulate what StatusLine does: getColor(0x0301) returns AttributePair

        # Create a mock view to test getColor
        view = View(Rect(0, 0, 10, 1))
        attrs = view.getColor(0x0301)  # This returns AttributePair
        
        text = "~Alt+X~ Exit"
        count = self.buffer.moveCStr(0, text, attrs)
        
        expected = "Alt+X Exit"
        result = self._get_buffer_text(count)
        self.assertEqual(result, expected)
        self.assertNotIn("tttt", result, "Should not be garbled")
