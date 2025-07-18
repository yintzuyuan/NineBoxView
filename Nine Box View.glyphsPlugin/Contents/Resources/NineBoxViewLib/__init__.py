# encoding: utf-8
"""
九宮格預覽外掛 - 模組化程式碼
Nine Box Preview Plugin - Modular Code
"""

from __future__ import division, print_function, unicode_literals

# 匯入核心模組
from .core import *
from .ui import *

__all__ = [
    # 從 core 模組
    'DEBUG_MODE', 'DEFAULT_ZOOM', 'FULL_ARRANGEMENT_SIZE', 'CENTER_POSITION', 
    'SURROUNDING_POSITIONS', 'MAX_LOCKED_POSITIONS', 'DEFAULT_WINDOW_SIZE',
    'MIN_WINDOW_SIZE', 'CONTROLS_PANEL_WIDTH', 'GRID_SIZE', 'GRID_TOTAL',
    'LAST_INPUT_KEY', 'SELECTED_CHARS_KEY', 'CURRENT_ARRANGEMENT_KEY',
    'ZOOM_FACTOR_KEY', 'WINDOW_POSITION_KEY', 'CONTROLS_PANEL_VISIBLE_KEY',
    'LOCKED_CHARS_KEY', 'PREVIOUS_LOCKED_CHARS_KEY', 'LOCK_MODE_KEY',
    'WINDOW_SIZE_KEY', 'ORIGINAL_ARRANGEMENT_KEY', 'FINAL_ARRANGEMENT_KEY',
    'debug_log', 'error_log', 'log_to_macro_window', 'clear_cache',
    'load_preferences', 'save_preferences', 'get_base_width',
    'parse_input_text', 'get_cached_glyph', 'get_cached_width',
    'EventHandlers',
    
    # 從 ui 模組
    'NineBoxWindow', 'NineBoxPreviewView', 'ControlsPanelView',
    'SearchPanel', 'LockFieldsPanel'
]
