# -*- coding: utf-8 -*-
import locale
import logging
import sys

import win32api
import win32console

from vindauga.constants.command_codes import cmScreenChanged
from vindauga.constants.event_codes import evKeyDown, evMouse, evNothing, evCommand
from vindauga.constants.keys import (
    kbShift, kbCtrlShift, kbAltShift, kbScrollState, kbNumState, kbCapsState, kbEnhanced,
    kbEsc, kbTab, kbEnter, kbBackSpace, kbDel, kbIns,
    kbHome, kbEnd, kbPgUp, kbPgDn, kbUp, kbDown, kbLeft, kbRight,
    kbF1, kbF2, kbF3, kbF4, kbF5, kbF6, kbF7, kbF8, kbF9, kbF10, kbF11, kbF12
)
from vindauga.events.mouse_event import MouseEvent
from vindauga.events.key_down_event import KeyDownEvent
from vindauga.utilities.platform.adapters.console_ctl import ConsoleCtl
from vindauga.utilities.platform.adapters.input_adapter import InputAdapter
from vindauga.utilities.platform.events.input_state import InputState
from vindauga.types.point import Point

from .scan_code_tables import NORMAL_CVT, SHIFT_CVT, CTRL_CVT, ALT_CVT
from . import windows_keys as VKeys

logger = logging.getLogger(__name__)


class WindowsConsoleInputAdapter(InputAdapter):
    """
    Windows Console input event source
    """
    def __init__(self, console_ctl: ConsoleCtl, display, input_state: InputState, mouse_enabled: bool = True):
        self._input_handle = None
        self._output_handle = None
        self._startup_input_mode = None
        self._startup_output_mode = None
        self._startup_input_cp = None
        self._startup_output_cp = None

        try:
            self._input_handle = win32console.GetStdHandle(win32console.STD_INPUT_HANDLE)
            self._output_handle = win32console.GetStdHandle(win32console.STD_OUTPUT_HANDLE)
            # Pass the Windows console handle to the parent
            super().__init__(self._input_handle)
        except Exception as e:
            logger.error("Failed to get Windows console handles: %s", e)
            # Fallback to stdin fileno
            super().__init__(sys.stdin.fileno() if hasattr(sys.stdin, 'fileno') else 0)

        self._setup_console_modes()

    def _setup_console_modes(self):
        """
        Set up console modes
        """
        try:

            # Save startup states for restoration
            self._startup_input_mode = self._input_handle.GetConsoleMode()
            self._startup_output_mode = self._output_handle.GetConsoleMode()
            self._startup_input_cp = win32console.GetConsoleCP()
            self._startup_output_cp = win32console.GetConsoleOutputCP()
            
            input_mode = self._startup_input_mode
            input_mode |= win32console.ENABLE_WINDOW_INPUT  # Report changes in buffer size
            input_mode |= win32console.ENABLE_MOUSE_INPUT   # Report mouse events
            input_mode &= ~win32console.ENABLE_PROCESSED_INPUT  # Report CTRL+C and SHIFT+Arrow events
            input_mode &= ~(win32console.ENABLE_ECHO_INPUT | win32console.ENABLE_LINE_INPUT)  # Report Ctrl+S
            
            # Try to enable extended flags and disable quick edit if available
            input_mode |= getattr(win32console, 'ENABLE_EXTENDED_FLAGS', 0x80)
            input_mode &= ~getattr(win32console, 'ENABLE_QUICK_EDIT_MODE', 0x40)
            
            self._input_handle.SetConsoleMode(input_mode)
            
            output_mode = self._startup_output_mode
            output_mode &= ~getattr(win32console, 'ENABLE_WRAP_AT_EOL_OUTPUT', 0x02)  # Avoid scrolling at line end
            
            # Try enabling VT sequences for ANSI support
            vt_processing_flag = getattr(win32console, 'ENABLE_VIRTUAL_TERMINAL_PROCESSING', 0x04)
            newline_auto_return_flag = getattr(win32console, 'DISABLE_NEWLINE_AUTO_RETURN', 0x08)
            
            # Check if we're running under Wine (simplified check)
            try:
                wine_version = win32api.GetProcAddress(
                    win32api.GetModuleHandle("ntdll"), "wine_get_version"
                )
                is_wine = wine_version is not None
            except Exception:
                is_wine = False
            
            if not is_wine:
                output_mode |= newline_auto_return_flag  # Do not do CR on LF
                output_mode |= vt_processing_flag  # Allow ANSI escape sequences
                
            self._output_handle.SetConsoleMode(output_mode)
            
            # Check if VT processing was actually enabled
            actual_output_mode = self._output_handle.GetConsoleMode()
            # CP_UTF8 = 65001
            win32console.SetConsoleCP(65001)
            win32console.SetConsoleOutputCP(65001)
            
            # Set locale for UTF-8 support
            try:
                locale.setlocale(locale.LC_ALL, ".utf8")
            except locale.Error:
                # Fallback for systems that don't support .utf8
                try:
                    locale.setlocale(locale.LC_ALL, "en_US.UTF-8")
                except locale.Error:
                    logger.error("Could not set UTF-8 locale")
            
        except Exception as e:
            logger.error("Failed to setup Windows console modes: %s", e)

    def __del__(self):
        """
        Restore console settings on cleanup
        """
        self._restore_console_settings()

    def _restore_console_settings(self):
        """
        Restore original console settings
        """
        try:
            if self._input_handle and self._startup_input_mode is not None:
                self._input_handle.SetConsoleMode(self._startup_input_mode)
            if self._output_handle and self._startup_output_mode is not None:
                self._output_handle.SetConsoleMode(self._startup_output_mode)
            if self._startup_input_cp is not None:
                win32console.SetConsoleCP(self._startup_input_cp)
            if self._startup_output_cp is not None:
                win32console.SetConsoleOutputCP(self._startup_output_cp)
        except Exception as e:
            logger.error("Failed to restore Windows console settings: %s", e)

    def has_pending_events(self) -> bool:
        """
        Check if input events are available
        """
        if self._input_handle:
            try:
                # Check console input buffer
                num_events = self._input_handle.GetNumberOfConsoleInputEvents()
                return num_events > 0
            except Exception as e:
                logger.error("WindowsConsoleInputAdapter.has_pending_events: exception %s", e)
        return False

    def get_event(self, event):
        """
        Get single event in Vindauga event format
        """
        if not self._input_handle:
            event.what = evNothing
            return False
        
        try:
            # ReadConsoleInput can sleep the process, so we first check the number
            # of available input events
            events_available = self._input_handle.GetNumberOfConsoleInputEvents()
            
            while events_available > 0:
                while events_available > 0:
                    events_available -= 1
                    input_records = self._input_handle.ReadConsoleInput(1)
                    if not input_records:
                        return False
                    input_record = input_records[0]
                    if self._process_input_record(input_record, event):
                        return True
                # Check again for more events after processing
                events_available = self._input_handle.GetNumberOfConsoleInputEvents()
                
        except Exception as e:
            logger.error("WindowsConsoleInputAdapter.get_event: exception %s", e)
            
        event.what = evNothing
        return False

    def _process_input_record(self, input_record, event):
        """
        Process single input record
        """
        event_type = input_record.EventType
        
        if event_type == win32console.KEY_EVENT:
            key_event = input_record.KeyDown
            if key_event or (input_record.VirtualKeyCode == VKeys.VK_MENU and input_record.Char):  # VKeys.VK_MENU = 18 (ALT)
                return self._process_win32_key(input_record, event)
                
        elif event_type == win32console.MOUSE_EVENT:
            self._process_win32_mouse(input_record, event)
            return True
            
        elif event_type == win32console.WINDOW_BUFFER_SIZE_EVENT:
            event.what = evCommand
            event.message.command = cmScreenChanged
            event.message.infoPtr = 0
            return True

        return False

    def _process_win32_key(self, input_record, event):
        key_event = KeyDownEvent()
        event.what = evKeyDown
        
        # Extract basic information from input record
        unicode_char = input_record.Char
        char_code = ord(unicode_char) if unicode_char else 0
        virtual_key = input_record.VirtualKeyCode  
        scan_code = getattr(input_record, 'VirtualScanCode', 0)
        control_state = input_record.ControlKeyState
        
        key_event.charScan.scanCode = scan_code
        key_event.charScan.charCode = chr(char_code) if char_code != 0 else '\x00'
        key_event.controlKeyState = self._convert_windows_control_state_to_vindauga(control_state)
        # Convert scan codes to key codes using modifier state
        if scan_code < 89:  # Valid range for conversion tables
            key_code = self._convert_scan_code_to_key_code(scan_code, key_event.controlKeyState, char_code)
            if key_code != 0:
                key_event.keyCode = key_code
            else:
                # Fallback for unmapped keys - use virtual key mapping when no character
                if char_code != 0:
                    key_event.keyCode = char_code
                else:
                    # No character - try virtual key mapping
                    key_event.keyCode = self._map_virtual_key_to_turbo_vision(virtual_key, key_event.controlKeyState)
        else:
            # Outside conversion range - use character or virtual key
            key_event.keyCode = char_code if char_code != 0 else self._map_virtual_key_to_turbo_vision(virtual_key,
                                                                                                       control_state)
        
        # Check if we have a valid key
        if key_event.keyCode != 0:
            event.keyDown = key_event
            return True
        
        return False
    
    def _map_virtual_key_to_turbo_vision(self, virtual_key, control_state):
        # Basic mapping table

        vk_map = {
            VKeys.VK_ESCAPE: kbEsc,      # VKeys.VK_ESCAPE
            VKeys.VK_TAB: kbTab,        # VKeys.VK_TAB
            VKeys.VK_RETURN: kbEnter,    # VKeys.VK_RETURN
            VKeys.VK_BACK: kbBackSpace,  # VKeys.VK_BACK
            VKeys.VK_DELETE: kbDel,      # VKeys.VK_DELETE
            VKeys.VK_INSERT: kbIns,      # VKeys.VK_INSERT
            VKeys.VK_HOME: kbHome,     # VKeys.VK_HOME
            VKeys.VK_END: kbEnd,      # VKeys.VK_END
            VKeys.VK_PRIOR: kbPgUp,     # VKeys.VK_PRIOR
            VKeys.VK_NEXT: kbPgDn,     # VKeys.VK_NEXT
            VKeys.VK_UP: kbUp,       # VKeys.VK_UP
            VKeys.VK_DOWN: kbDown,     # VKeys.VK_DOWN
            VKeys.VK_LEFT: kbLeft,     # VKeys.VK_LEFT
            VKeys.VK_RIGHT: kbRight,    # VKeys.VK_RIGHT
            VKeys.VK_F1: kbF1,      # VKeys.VK_F1
            VKeys.VK_F2: kbF2,      # VKeys.VK_F2
            VKeys.VK_F3: kbF3,      # VKeys.VK_F3
            VKeys.VK_F4: kbF4,      # VKeys.VK_F4
            VKeys.VK_F5: kbF5,      # VKeys.VK_F5
            VKeys.VK_F6: kbF6,      # VKeys.VK_F6
            VKeys.VK_F7: kbF7,      # VKeys.VK_F7
            VKeys.VK_F8: kbF8,      # VKeys.VK_F8
            VKeys.VK_F9: kbF9,      # VKeys.VK_F9
            VKeys.VK_F10: kbF10,     # VKeys.VK_F10
            VKeys.VK_F11: kbF11,     # VKeys.VK_F11
            VKeys.VK_F12: kbF12,     # VKeys.VK_F12
        }
        return vk_map.get(virtual_key, 0)
    
    def _convert_windows_control_state_to_vindauga(self, windows_control_state):
        """
        Convert Windows control key state flags to Vindauga flags
        Windows uses different bit positions than Vindauga
        """
        
        # Windows control state constants (from wincon.h)
        SHIFT_PRESSED = 0x0010
        LEFT_CTRL_PRESSED = 0x0008  
        RIGHT_CTRL_PRESSED = 0x0004
        LEFT_ALT_PRESSED = 0x0002
        RIGHT_ALT_PRESSED = 0x0001
        SCROLLLOCK_ON = 0x0040
        NUMLOCK_ON = 0x0020
        CAPSLOCK_ON = 0x0080
        ENHANCED_KEY = 0x0100
        
        vindauga_state = 0
        
        # Convert each flag
        if windows_control_state & SHIFT_PRESSED:
            vindauga_state |= kbShift
        if windows_control_state & (LEFT_CTRL_PRESSED | RIGHT_CTRL_PRESSED):
            vindauga_state |= kbCtrlShift  
        if windows_control_state & (LEFT_ALT_PRESSED | RIGHT_ALT_PRESSED):
            vindauga_state |= kbAltShift
        if windows_control_state & SCROLLLOCK_ON:
            vindauga_state |= kbScrollState
        if windows_control_state & NUMLOCK_ON:
            vindauga_state |= kbNumState
        if windows_control_state & CAPSLOCK_ON:
            vindauga_state |= kbCapsState
        if windows_control_state & ENHANCED_KEY:
            vindauga_state |= kbEnhanced
            
        return vindauga_state
    
    def _convert_scan_code_to_key_code(self, scan_code, control_state, char_code):
        """
        Convert scan codes to Vindauga key codes using modifier state
        """
        if (control_state & kbAltShift) and scan_code in ALT_CVT:
            return ALT_CVT[scan_code]
        elif (control_state & kbCtrlShift) and scan_code in CTRL_CVT:
            return CTRL_CVT[scan_code]  
        elif (control_state & kbShift) and scan_code in SHIFT_CVT:
            return SHIFT_CVT[scan_code]
        elif not (control_state & (kbShift | kbCtrlShift | kbAltShift)) and scan_code in NORMAL_CVT:
            return NORMAL_CVT[scan_code]
        
        return 0
        
    def _process_win32_mouse(self, input_record, event):
        """
        Process Windows mouse event
        """
        event.what = evMouse
        event.mouse = MouseEvent()
        event.mouse.where = Point(input_record.MousePosition.X, input_record.MousePosition.Y)
        event.mouse.buttons = input_record.ButtonState
        event.mouse.eventFlags = input_record.EventFlags
        
        KB_SHIFT = 0x03
        KB_CTRL_SHIFT = 0x0C  
        KB_ALT_SHIFT = 0x30
        KB_SCROLL_STATE = 0x40
        KB_NUM_STATE = 0x80
        KB_CAPS_STATE = 0x100
        KB_ENHANCED = 0x200
        
        valid_flags = KB_SHIFT | KB_CTRL_SHIFT | KB_ALT_SHIFT | KB_SCROLL_STATE | KB_NUM_STATE | KB_CAPS_STATE | KB_ENHANCED
        event.mouse.controlKeyState = input_record.ControlKeyState & valid_flags
        
        event.mouse.wheel = 0
        button_state_high = input_record.ButtonState & 0x80000000
        is_positive_rotation = not button_state_high
        
        MOUSE_WHEELED = 0x0004
        MOUSE_HWHEELED = 0x0008
        
        if input_record.EventFlags & MOUSE_WHEELED:
            # Vertical wheel
            event.mouse.wheel = 1 if is_positive_rotation else -1  # mwUp : mwDown
        elif input_record.EventFlags & MOUSE_HWHEELED:
            # Horizontal wheel  
            event.mouse.wheel = 2 if is_positive_rotation else -2  # mwRight : mwLeft
