#!/usr/bin/env python
# -*- coding: utf-8 -*-
import unittest
from unittest.mock import Mock, MagicMock, patch
import logging

from vindauga.screen_driver.hardware_info import HardwareInfo
from vindauga.events.event import Event
from vindauga.constants.event_codes import evNothing, evKeyboard

logger = logging.getLogger(__name__)


class TestHardwareInfoEvents(unittest.TestCase):
    
    def setUp(self):
        """Set up test fixtures"""
        self.hardware_info = HardwareInfo()
        
        # Mock the platform to control event behavior
        self.mock_platform = Mock()
        self.hardware_info.platform = self.mock_platform
        
    def test_readEvents_no_infinite_loop(self):
        """Test that readEvents doesn't create infinite loops"""
        # Mock platform.get_event to return False (no events)
        self.mock_platform.get_event.return_value = False
        
        # This should not loop infinitely
        self.hardware_info.readEvents()
        
        # Should have tried to get one event and stopped
        self.mock_platform.get_event.assert_called_once()
        self.assertEqual(self.hardware_info.eventCount, 0)
        
    def test_readEvents_with_events(self):
        """Test readEvents with actual events"""
        # Mock platform to return events for first few calls, then False
        call_count = 0
        def mock_get_event(event):
            nonlocal call_count
            call_count += 1
            if call_count <= 3:  # Return 3 events
                event.what = evKeyboard
                return True
            return False  # No more events
            
        self.mock_platform.get_event.side_effect = mock_get_event
        
        # This should read 3 events and stop
        self.hardware_info.readEvents()
        
        self.assertEqual(self.hardware_info.eventCount, 3)
        self.assertEqual(call_count, 4)  # 3 successful + 1 failed
        
    def test_readEvents_with_problematic_platform(self):
        """Test readEvents with a platform that always returns True but doesn't populate events properly"""
        
        # This is the problematic case: platform.get_event returns True but event count doesn't increase
        # This could happen if there's a bug in the platform layer
        call_count = 0
        def mock_get_event_buggy(event):
            nonlocal call_count
            call_count += 1
            # Always return True but don't actually populate the event properly
            # This could cause infinite loops in the original implementation
            return True
            
        self.mock_platform.get_event.side_effect = mock_get_event_buggy
        
        # This should NOT loop infinitely due to our safety measures
        old_count = self.hardware_info.eventCount
        self.hardware_info.readEvents()
        
        # The safety check should have prevented infinite loop
        # eventCount should not have increased since events weren't properly populated
        self.assertEqual(self.hardware_info.eventCount, old_count)
        
        # Should have hit the safety limit
        self.assertGreaterEqual(call_count, 1)
        
    def test_getPendingEvent_removes_event_correctly(self):
        """Test that getPendingEvent properly removes events from queue"""
        # Manually add some events to the queue
        event1 = Event(evKeyboard)
        event2 = Event(evKeyboard)
        event3 = Event(evKeyboard)
        
        self.hardware_info.eventQ[0] = event1
        self.hardware_info.eventQ[1] = event2  
        self.hardware_info.eventQ[2] = event3
        self.hardware_info.eventCount = 3
        
        # Get the first event
        result_event = Event(evNothing)
        success = self.hardware_info.getPendingEvent(result_event, False)
        
        self.assertTrue(success)
        self.assertEqual(self.hardware_info.eventCount, 2)  # Should be decremented
        self.assertEqual(result_event.what, evKeyboard)
        
        # Remaining events should be shifted down
        self.assertEqual(self.hardware_info.eventQ[0], event2)
        self.assertEqual(self.hardware_info.eventQ[1], event3)
        
    def test_getKeyEvent_flow(self):
        """Test the complete getKeyEvent flow"""
        # Mock readEvents to add one event
        def mock_read_events():
            if self.hardware_info.eventCount == 0:
                event = Event(evKeyboard)
                self.hardware_info.eventQ[0] = event
                self.hardware_info.eventCount = 1
                
        self.hardware_info.readEvents = mock_read_events
        
        # Test getKeyEvent
        test_event = Event(evNothing)
        result = self.hardware_info.getKeyEvent(test_event)
        
        self.assertTrue(result)
        self.assertEqual(test_event.what, evKeyboard)
        self.assertEqual(self.hardware_info.eventCount, 0)  # Event should be consumed


if __name__ == '__main__':
    logging.basicConfig(level=logging.DEBUG)
    unittest.main()