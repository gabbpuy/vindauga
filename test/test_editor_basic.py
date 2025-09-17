# -*- coding: utf-8 -*-
"""Basic tests for Editor class to verify C++ TEditor conversion."""
import unittest
from vindauga.types.rect import Rect
from vindauga.widgets.editor import Editor


class TestEditorBasic(unittest.TestCase):
    """Test basic Editor functionality."""

    def setUp(self):
        """Set up test editor."""
        bounds = Rect(0, 0, 80, 25)
        self.editor = Editor(bounds, None, None, None, 4096)

    def test_editor_creation(self):
        """Test that editor can be created."""
        self.assertIsNotNone(self.editor)
        self.assertTrue(self.editor.isValid)
        self.assertEqual(self.editor.bufLen, 0)

    def test_basic_navigation_methods_exist(self):
        """Test that the navigation methods exist."""
        self.assertTrue(hasattr(self.editor, 'nextChar'))
        self.assertTrue(hasattr(self.editor, 'prevChar'))
        self.assertTrue(hasattr(self.editor, 'nextLine'))
        self.assertTrue(hasattr(self.editor, 'prevLine'))
        self.assertTrue(hasattr(self.editor, 'nextWord'))
        self.assertTrue(hasattr(self.editor, 'prevWord'))

    def test_text_class_usage(self):
        """Test that Text class methods are being used correctly."""
        from vindauga.screen_driver.text.text import Text

        # Insert some text
        test_text = "Hello, Unicode! 😊"
        self.editor.insertText(test_text, len(test_text), False)

        # Test that nextChar and prevChar work with Unicode
        start_pos = 0
        next_pos = self.editor.nextChar(start_pos)
        self.assertGreaterEqual(next_pos, start_pos + 1)

        # Test that we can move back
        prev_pos = self.editor.prevChar(next_pos)
        self.assertEqual(prev_pos, start_pos)

    def test_basic_text_operations(self):
        """Test basic text insertion and navigation."""
        # Insert simple text
        test_text = "Line 1\nLine 2\nLine 3"
        self.editor.insertText(test_text, len(test_text), False)

        self.assertEqual(self.editor.bufLen, len(test_text))

        # Test line navigation
        pos = self.editor.lineStart(0)
        self.assertEqual(pos, 0)

        # Move to next line
        next_line_pos = self.editor.nextLine(pos)
        self.assertGreater(next_line_pos, pos)

    def test_selection_operations(self):
        """Test selection functionality."""
        # Insert text
        test_text = "Hello World"
        self.editor.insertText(test_text, len(test_text), False)

        # Test selection
        self.editor.setSelect(0, 5, False)  # Select "Hello"
        self.assertTrue(self.editor.hasSelection())
        self.assertEqual(self.editor.selStart, 0)
        self.assertEqual(self.editor.selEnd, 5)

        # Test hiding selection
        self.editor.hideSelect()
        self.assertFalse(self.editor.hasSelection())


if __name__ == '__main__':
    unittest.main()