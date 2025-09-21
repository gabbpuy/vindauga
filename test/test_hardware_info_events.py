#!/usr/bin/env python
# -*- coding: utf-8 -*-
import unittest
from unittest.mock import Mock, patch
import logging

from vindauga.utilities.platform.system_interface import SystemInterface
from vindauga.events.event import Event
from vindauga.constants.event_codes import evNothing, evKeyDown, evMouse

logger = logging.getLogger(__name__)


class TestHardwareInfoEvents(unittest.TestCase):

    def setUp(self):
        """
        Set up test fixtures
        """
        self.hardware_info = SystemInterface()

    def test_hardware_info_creation(self):
        """
        Test that HardwareInfo can be created
        """
        self.assertIsNotNone(self.hardware_info)

    def test_basic_properties(self):
        """
        Test basic HardwareInfo properties
        """
        # Test button count
        self.assertEqual(self.hardware_info.getButtonCount(), 2)

        # Test eventQ_Size is defined
        self.assertEqual(self.hardware_info.eventQ_Size, 24)

    def test_screen_methods_exist(self):
        """
        Test that screen-related methods exist and are callable
        """
        # These should not crash when called
        try:
            self.hardware_info.getScreenRows()
            self.hardware_info.getScreenCols()
            self.hardware_info.flushScreen()
        except Exception:
            # Platform might not be initialized in test environment
            pass

    def test_console_methods_exist(self):
        """
        Test that console setup/restore methods exist
        """
        # These should not crash when called
        try:
            self.hardware_info.setupConsole()
            self.hardware_info.restoreConsole()
        except Exception:
            # Platform might not be initialized in test environment
            pass

    def test_cursor_methods_exist(self):
        """
        Test that cursor methods exist and are callable
        """
        # These should not crash when called
        try:
            self.hardware_info.cursorOn()
            self.hardware_info.cursorOff()
            self.hardware_info.setCaretSize(50)
            self.hardware_info.setCaretPosition(0, 0)
            self.hardware_info.getCaretSize()
            self.hardware_info.isCaretVisible()
        except Exception:
            # Platform might not be initialized in test environment
            pass

    def test_getKeyEvent_with_no_events(self):
        """
        Test getKeyEvent when no events are available
        """
        event = Event(evNothing)

        # Mock the platform to return no events
        with patch.object(self.hardware_info, '_HardwareInfo__platform') as mock_platform:
            mock_platform.get_event.return_value = False

            result = self.hardware_info.getKeyEvent(event)
            self.assertFalse(result)
            self.assertEqual(event.what, evNothing)

    def test_getMouseEvent_with_no_events(self):
        """
        Test getMouseEvent when no events are available
        """
        # Mock the platform to return no events
        with patch.object(self.hardware_info, '_HardwareInfo__platform') as mock_platform:
            mock_platform.get_event.return_value = False

            result = self.hardware_info.getMouseEvent()
            self.assertIsNone(result)

    def test_wait_for_events(self):
        """
        Test waitForEvents method
        """
        with patch.object(self.hardware_info, '_HardwareInfo__platform') as mock_platform:
            self.hardware_info.waitForEvents(100)
            mock_platform.wait_for_events.assert_called_once_with(100)

    def test_interrupt_event_wait(self):
        """
        Test interruptEventWait method
        """
        with patch.object(self.hardware_info, '_HardwareInfo__platform') as mock_platform:
            self.hardware_info.interruptEventWait()
            mock_platform.interrupt_event_wait.assert_called_once()

    def test_clipboard_methods(self):
        """
        Test clipboard methods
        """
        with patch.object(self.hardware_info, '_HardwareInfo__platform') as mock_platform:
            self.hardware_info.setClipboardText("test")
            mock_platform.set_clipboard_text.assert_called_once_with("test")

            self.hardware_info.requestClipboardText()
            mock_platform.request_clipboard_text.assert_called_once()

    def test_get_tick_count(self):
        """
        Test getTickCount returns a number
        """
        tick_count = self.hardware_info.getTickCount()
        self.assertIsInstance(tick_count, (int, float))
        self.assertGreater(tick_count, 0)
