# -*- coding: utf-8 -*-
import logging
import platform
import select

from .poll_state import PollState
from .poll_data import PollData

logger = logging.getLogger(__name__)

if platform.system().lower() == 'windows':
    from win32event import WaitForMultipleObjects, WAIT_OBJECT_0

    def poll_handles(pd: PollData, timeout_ms: int):
        handles = pd.handles
        states = pd.states
        
        # Filter out None/invalid handles for Windows
        valid_handles = []
        handle_indices = []
        
        for i, handle in enumerate(handles):
            if handle is None or handle == 0:
                # None handles or invalid handles (e.g., curses input, invalid FDs) - mark as Nothing
                states[i] = PollState.Nothing
            else:
                try:
                    # Additional validation - check if handle is valid
                    # Convert to int if needed to validate
                    if hasattr(handle, 'handle'):
                        # PyHANDLE object
                        handle_val = int(handle.handle) if handle.handle else 0
                    else:
                        handle_val = int(handle) if handle else 0
                    
                    # Windows HANDLE 0 and -1 are typically invalid
                    if handle_val == 0 or handle_val == -1:
                        states[i] = PollState.Nothing
                    else:
                        valid_handles.append(handle)
                        handle_indices.append(i)
                except Exception:
                    states[i] = PollState.Disconnect

        if not valid_handles:
            # No valid handles - don't sleep here as input adapters handle their own timing
            return
        
        try:
            res = WaitForMultipleObjects(valid_handles, False, timeout_ms)

            i = 0
            while WAIT_OBJECT_0 <= res <= WAIT_OBJECT_0 + len(valid_handles) - i - 1:
                handle_idx = handle_indices[i + res - WAIT_OBJECT_0]
                states[handle_idx] = PollState.Ready

                if (i := i + res - WAIT_OBJECT_0 + 1) < len(valid_handles):
                    res = WaitForMultipleObjects(valid_handles[i:], False, 0)
                else:
                    break
        except Exception as e:
            logger.error("poll_handles (Windows): WaitForMultipleObjects failed: %s", e)
            # Mark all valid handles as disconnected on error
            for idx in handle_indices:
                states[idx] = PollState.Disconnect

else:
    def poll_handles(pd: PollData, timeout_ms: int):
        fds = pd.handles
        states = pd.states

        # Filter out invalid file descriptors
        valid_fds = []
        for i, fd in enumerate(fds):
            if fd is None or fd == -1:
                states[i] = PollState.Nothing
                continue
                
            valid_fds.append(fd)

        if not valid_fds:
            return
        
        try:
            r, _w, _x = select.select(valid_fds, [], [], timeout_ms / 1000.0)
        except OSError:
            for i in range(len(fds)):
                states[i] = PollState.Disconnect
            return

        for i, fd in enumerate(r):
            states[i] = PollState.Ready
