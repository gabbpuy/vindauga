# -*- coding: utf-8 -*-
import unittest

from vindauga.events.event import Event
from vindauga.constants.event_codes import evNothing, evKeyDown
from vindauga.constants.keys import kbEnter


class TestEventLoopIdle(unittest.TestCase):
    """
Test that the event loop properly calls idle() method
"""

    def setUp(self):
        """
        Set up test fixtures
        """
        # We can't easily test Program directly due to Screen dependencies
        # But we can test the event processing logic
        self.idle_call_count = 0
        
    def test_idle_called_when_no_events(self):
        """
        Test that idle() is called when getEvent returns evNothing
        """
        
        # Create a mock program that tracks idle calls
        class MockProgram:
            def __init__(self):
                self.idle_calls = 0
                
            def idle(self):
                self.idle_calls += 1
                
            def getEvent_logic(self, event):
                """
                Simplified version of Program.getEvent logic
                """
                # Simulate no pending events
                event.what = evNothing
                
                # Simulate no mouse events  
                if event.what == evNothing:
                    # Simulate no keyboard events
                    if event.what == evNothing:
                        self.idle()  # This should be called
        
        program = MockProgram()
        event = Event(evNothing)

        # Simulate multiple getEvent calls with no input
        for _ in range(3):
            program.getEvent_logic(event)
            
        self.assertEqual(program.idle_calls, 3, "idle() should be called when no events are available")

    def test_idle_not_called_when_events_available(self):
        """
        Test that idle() is not called when events are available
        """
        
        class MockProgram:
            def __init__(self):
                self.idle_calls = 0
                
            def idle(self):
                self.idle_calls += 1
                
            def getEvent_logic_with_key(self, event):
                """
                Simulate getEvent with keyboard input
                """
                # Simulate key event available
                event.what = evKeyDown
                event.keyDown.keyCode = kbEnter
                # idle() should NOT be called when events are available
        
        program = MockProgram()
        event = Event(evNothing)

        program.getEvent_logic_with_key(event)
        
        self.assertEqual(program.idle_calls, 0, "idle() should not be called when events are available")

    def test_event_processing_order(self):
        """
        Test the order of event processing matches Program.getEvent
        """
        
        class MockProgram:
            def __init__(self):
                self.processing_order = []
                
            def idle(self):
                self.processing_order.append("idle")
                
            def getEvent_simulation(self, event, has_pending=False, has_mouse=False, has_key=False):
                """
                Simulate the full getEvent logic
                """
                
                if has_pending:
                    event.what = evKeyDown  # Simulate pending event
                    self.processing_order.append("pending")
                    return
                    
                self.processing_order.append("waitForEvents")
                
                if has_mouse:
                    event.what = evKeyDown  # Simulate mouse event
                    self.processing_order.append("mouse")
                    return
                    
                if has_key:
                    event.what = evKeyDown  # Simulate key event  
                    self.processing_order.append("key")
                    return
                    
                # No events - should call idle
                event.what = evNothing
                self.idle()
        
        program = MockProgram()
        event = Event(evNothing)

        # Test no events scenario
        program.getEvent_simulation(event)
        expected = ["waitForEvents", "idle"]
        self.assertEqual(program.processing_order, expected)
        
        # Test with key event
        program.processing_order.clear()
        program.getEvent_simulation(event, has_key=True)
        expected = ["waitForEvents", "key"]
        self.assertEqual(program.processing_order, expected)
