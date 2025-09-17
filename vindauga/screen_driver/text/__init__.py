# -*- coding: utf-8 -*-
"""
Text handling utilities equivalent to tvision's TText class.
Provides sophisticated multibyte string manipulation and screen cell drawing.
"""

from .text import Text as Text
from .text_metrics import TextMetrics as TextMetrics
from .text import measure_text as measure_text, text_width as text_width, text_fits_width as text_fits_width, truncate_text as truncate_text
