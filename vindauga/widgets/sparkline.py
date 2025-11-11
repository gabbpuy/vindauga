# -*- coding: utf-8 -*-
import logging
from typing import List, Union

from vindauga.types.draw_buffer import DrawBuffer
from vindauga.types.palette import Palette
from vindauga.types.rect import Rect
from vindauga.types.view import View
from vindauga.utilities.colours.attribute_pair import AttributePair

logger = logging.getLogger(__name__)


class Sparkline(View):
    """
    A sparkline widget that displays a series of data points as a compact visualization.
    Supports variable height for multi-line sparklines.
    """

    cpSparkline = '\x17'

    # Unicode block characters for vertical bars (9 levels: empty + 8 filled)
    SPARK_CHARS = ' ▁▂▃▄▅▆▇█'
    BACK_CHAR = ' '

    name = 'Sparkline'

    def __init__(self, bounds: Rect, data: List[Union[int, float]] = None):
        """
        Initialize sparkline widget.

        Args:
            bounds: Rectangle defining the widget's position and size
            data: Initial data points to display
        """
        super().__init__(bounds)
        self.data = data or []
        self.minValue = None
        self.maxValue = None
        self.autoScale = True

    def setData(self, data: List[Union[int, float]]):
        """
        Set the data points for the sparkline.

        Args:
            data: List of numeric values to display
        """
        self.data = list(data) if data else []
        self.drawView()

    def addDataPoint(self, value: Union[int, float]):
        """
        Add a single data point to the sparkline.

        Args:
            value: Numeric value to add
        """
        self.data.append(value)
        self.drawView()

    def setRange(self, minValue: Union[int, float, None], maxValue: Union[int, float, None]):
        """
        Set the min/max range for the sparkline. If None, uses auto-scaling.

        Args:
            minValue: Minimum value for scaling (None for auto)
            maxValue: Maximum value for scaling (None for auto)
        """
        self.minValue = minValue
        self.maxValue = maxValue
        self.autoScale = (minValue is None or maxValue is None)
        self.drawView()

    def clear(self):
        """Clear all data points."""
        self.data = []
        self.drawView()

    def _normalizeValue(self, value: Union[int, float], minVal: float, maxVal: float) -> float:
        """
        Normalize a value to 0-1 range based on min/max.

        Args:
            value: Value to normalize
            minVal: Minimum value in range
            maxVal: Maximum value in range

        Returns:
            Normalized value between 0 and 1
        """
        if maxVal == minVal:
            return 0.5
        return (value - minVal) / (maxVal - minVal)

    def _valueToChar(self, normalizedValue: float) -> str:
        """
        Convert a normalized value (0-1) to a sparkline character.

        Args:
            normalizedValue: Value between 0 and 1

        Returns:
            Unicode character representing the value
        """
        # Clamp to 0-1 range
        normalizedValue = max(0.0, min(1.0, normalizedValue))

        # Map to character index (0-8)
        charIndex = int(normalizedValue * (len(self.SPARK_CHARS) - 1))
        return self.SPARK_CHARS[charIndex]

    def _drawSingleLine(self, buf: DrawBuffer, y: int, color: AttributePair):
        """
        Draw a single line of the sparkline.

        Args:
            buf: DrawBuffer to write to
            y: Line number to draw
            color: Color attribute to use
        """
        if not self.data:
            # Empty sparkline
            buf.moveChar(0, self.BACK_CHAR, color, self.size.x)
            self.writeLine(0, y, self.size.x, 1, buf)
            return

        # Determine min/max for scaling
        if self.autoScale:
            minVal = min(self.data)
            maxVal = max(self.data)
        else:
            minVal = self.minValue if self.minValue is not None else min(self.data)
            maxVal = self.maxValue if self.maxValue is not None else max(self.data)

        # Get the portion of data to display (rightmost points that fit)
        displayData = self.data[-self.size.x:] if len(self.data) > self.size.x else self.data

        # Build the sparkline string
        sparkStr = ''
        for value in displayData:
            normalized = self._normalizeValue(value, minVal, maxVal)
            sparkStr += self._valueToChar(normalized)

        # Pad with spaces if needed
        sparkStr = sparkStr.ljust(self.size.x, self.BACK_CHAR)

        # Write to buffer
        buf.moveStr(0, sparkStr, color)
        self.writeLine(0, y, self.size.x, 1, buf)

    def _drawMultiLine(self):
        """
        Draw a multi-line sparkline with vertical resolution.
        """
        if not self.data:
            # Empty sparkline - fill with spaces
            for y in range(self.size.y):
                buf = DrawBuffer()
                color = self.getColor(1)
                buf.moveChar(0, self.BACK_CHAR, color, self.size.x)
                self.writeLine(0, y, self.size.x, 1, buf)
            return

        # Determine min/max for scaling
        if self.autoScale:
            minVal = min(self.data)
            maxVal = max(self.data)
        else:
            minVal = self.minValue if self.minValue is not None else min(self.data)
            maxVal = self.maxValue if self.maxValue is not None else max(self.data)

        # Get the portion of data to display
        displayData = self.data[-self.size.x:] if len(self.data) > self.size.x else self.data

        color = self.getColor(1)

        # For multi-line, we need to think in terms of vertical blocks
        # Each column represents one data point
        # Height is divided into segments
        heightSegments = self.size.y * 8  # 8 sub-levels per line

        # Draw from bottom to top
        for y in range(self.size.y):
            buf = DrawBuffer()
            lineStr = ''

            for i, value in enumerate(displayData):
                normalized = self._normalizeValue(value, minVal, maxVal)
                # Calculate how high this value reaches in characters
                heightInSegments = normalized * heightSegments

                # Which line are we on from the bottom?
                lineFromBottom = self.size.y - 1 - y
                baseHeight = lineFromBottom * 8

                if heightInSegments >= baseHeight + 8:
                    # This line is fully filled
                    lineStr += self.SPARK_CHARS[-1]
                elif heightInSegments > baseHeight:
                    # Partial fill
                    partialSegments = int(heightInSegments - baseHeight)
                    lineStr += self.SPARK_CHARS[partialSegments]
                else:
                    # Empty
                    lineStr += self.BACK_CHAR

            # Pad with spaces
            lineStr = lineStr.ljust(self.size.x, self.BACK_CHAR)
            buf.moveStr(0, lineStr, color)
            self.writeLine(0, y, self.size.x, 1, buf)

    def draw(self):
        """Draw the sparkline widget."""
        if self.size.y == 1:
            # Single line sparkline
            buf = DrawBuffer()
            color = self.getColor(1)
            self._drawSingleLine(buf, 0, color)
        else:
            # Multi-line sparkline with vertical resolution
            self._drawMultiLine()

    def getPalette(self) -> Palette:
        """Get the color palette for the sparkline."""
        return Palette(self.cpSparkline)