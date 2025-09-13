# encoding: utf-8

"""
九宮格預覽程式庫
遵循 DrawBot 架構模式，專注九宮格預覽功能
"""

from __future__ import division, print_function, unicode_literals

__version__ = "3.3.0"
__author__ = "TzuYuan Yin"

# 核心模組匯入
from .core.grid_manager import GridManager

# 有條件匯入 GlyphsEventHandler（需要 Glyphs.app 環境）
try:
    from .core.event_handler import GlyphsEventHandler
except ImportError:
    # 在非 Glyphs 環境中跳過
    GlyphsEventHandler = None

# UI 模組匯入（純 AppKit 實作）
try:
    from .ui.preview_view import NineBoxPreviewView, create_preview_view
    from .ui.search_panel import SearchPanel
    from .ui.controls_panel import ControlsPanelView
    from .ui.lock_fields_panel import LockFieldsPanel
except ImportError:
    # 在沒有 AppKit 的環境中跳過 UI 匯入
    pass

# 資料模組匯入
from .data.preferences import PreferencesManager

# 便利函數
def create_grid_manager():
    """建立 GridManager 實例的便利函數"""
    return GridManager()

def get_preferences():
    """獲取偏好設定管理器的便利函數"""
    return PreferencesManager