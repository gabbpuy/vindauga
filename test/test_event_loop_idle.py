# -*- coding: utf-8 -*-
import unittest
from unittest.mock import patch

from vindauga.events.event import Event
from vindauga.events.event_queue import event_queue
from vindauga.constants.event_codes import evNothing, evKeyDown, evMouseDown
from vindauga.constants.keys import kbEnter
from vindauga.widgets.program import Program


class TestEventLoopIdle(unittest.TestCase):
    """
    Test that Program.getEvent() calls idle() exactly when no real event was
    available. This exercises the actual Program.getEvent()/idle()
    implementation (with the console I/O mocked out at the event_queue
    singleton), rather than a reimplementation of its logic.
    """

    def setUp(self):
        # Program() requires a real console/screen (systemInterface,
        # initScreen, initDesktop, ...); build a bare instance instead and
        # give it just enough state for getEvent() to run standalone.
        self.program = Program.__new__(Program)
        self.program.statusLine = None
        Program.pending = Event(evNothing)

        self.idle_calls = 0
        self.program.idle = lambda: setattr(self, 'idle_calls', self.idle_calls + 1)

    def test_idle_called_when_no_events(self):
        with patch.object(event_queue, 'waitForEvents'), \
                patch.object(event_queue, 'getMouseEvent'), \
                patch.object(event_queue, 'getKeyEvent'):
            for _ in range(3):
                event = Event(evNothing)
                self.program.getEvent(event)
                self.assertEqual(event.what, evNothing)

        self.assertEqual(self.idle_calls, 3)

    def test_idle_not_called_when_key_event_available(self):
        def fakeGetKeyEvent(event):
            event.what = evKeyDown
            event.keyDown.keyCode = kbEnter

        with patch.object(event_queue, 'waitForEvents'), \
                patch.object(event_queue, 'getMouseEvent'), \
                patch.object(event_queue, 'getKeyEvent', side_effect=fakeGetKeyEvent):
            event = Event(evNothing)
            self.program.getEvent(event)

        self.assertEqual(self.idle_calls, 0)
        self.assertEqual(event.what, evKeyDown)

    def test_idle_not_called_when_mouse_event_available(self):
        def fakeGetMouseEvent(event):
            event.what = evMouseDown

        with patch.object(event_queue, 'waitForEvents'), \
                patch.object(event_queue, 'getMouseEvent', side_effect=fakeGetMouseEvent), \
                patch.object(event_queue, 'getKeyEvent'):
            event = Event(evNothing)
            self.program.getEvent(event)

        self.assertEqual(self.idle_calls, 0)
        self.assertEqual(event.what, evMouseDown)

    def test_pending_event_short_circuits_wait_and_idle(self):
        pending = Event(evKeyDown)
        pending.keyDown.keyCode = kbEnter
        Program.pending = pending

        with patch.object(event_queue, 'waitForEvents') as mockWait, \
                patch.object(event_queue, 'getMouseEvent') as mockMouse, \
                patch.object(event_queue, 'getKeyEvent') as mockKey:
            event = Event(evNothing)
            self.program.getEvent(event)

        mockWait.assert_not_called()
        mockMouse.assert_not_called()
        mockKey.assert_not_called()
        self.assertEqual(self.idle_calls, 0)
        self.assertEqual(event.what, evKeyDown)
        # Consuming the pending event clears it for the next call
        self.assertEqual(Program.pending.what, evNothing)


if __name__ == '__main__':
    unittest.main()
