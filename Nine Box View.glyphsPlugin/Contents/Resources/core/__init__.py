# encoding: utf-8
"""
九宮格預覽外掛 - 核心模組
Nine Box Preview Plugin - Core Module
"""

from __future__ import division, print_function, unicode_literals

from .constants import *
from .utils import *

__all__ = [
    # Constants
    'DEBUG_MODE', 'DEFAULT_ZOOM', 'FULL_ARRANGEMENT_SIZE', 'CENTER_POSITION', 
    'SURROUNDING_POSITIONS', 'MAX_LOCKED_POSITIONS', 'DEFAULT_LOCKED_POSITIONS',
    'MINIMAL_GLYPH_REPRESENTATION', 'ARRANGEMENT_GRID_SIZE', 'REFRESH_INTERVAL',
    'WINDOW_WIDTH', 'WINDOW_HEIGHT', 'PANEL_HEIGHT', 'SEARCH_FIELD_WIDTH',
    'SEARCH_FIELD_HEIGHT', 'INPUT_TEXT_WIDTH', 'INPUT_TEXT_HEIGHT',
    'TOGGLE_BUTTON_HEIGHT', 'BUTTON_WIDTH', 'DEFAULT_FONT_SIZE', 'MINIMUM_FONT_SIZE',
    'MAXIMUM_FONT_SIZE', 'STEP_SIZE',
    
    # Utils
    'debug_log', 'error_log', 'parse_input_text', 'generate_arrangement',
    'validate_locked_positions', 'get_cached_glyph', 'get_cached_width',
    'generate_non_repeating_batch'
]