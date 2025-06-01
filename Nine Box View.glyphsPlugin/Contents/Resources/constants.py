# encoding: utf-8
"""
九宮格預覽外掛 - 常數定義（優化版）
Nine Box Preview Plugin - Constants Definition (Optimized)
"""

from __future__ import division, print_function, unicode_literals
from GlyphsApp import WINDOW_MENU

# 外掛識別字串前綴
PLUGIN_ID_PREFIX = "com.YinTzuYuan.NineBoxView"

# 外掛屬性鍵值
LAST_INPUT_KEY = f"{PLUGIN_ID_PREFIX}.lastInput"
SELECTED_CHARS_KEY = f"{PLUGIN_ID_PREFIX}.selectedChars"
CURRENT_ARRANGEMENT_KEY = f"{PLUGIN_ID_PREFIX}.currentArrangement"
TEST_MODE_KEY = f"{PLUGIN_ID_PREFIX}.testMode"
SEARCH_HISTORY_KEY = f"{PLUGIN_ID_PREFIX}.search"
ZOOM_FACTOR_KEY = f"{PLUGIN_ID_PREFIX}.zoomFactor"
SHOW_NUMBERS_KEY = f"{PLUGIN_ID_PREFIX}.showNumbers"
WINDOW_SIZE_KEY = f"{PLUGIN_ID_PREFIX}.windowSize"
WINDOW_POSITION_KEY = f"{PLUGIN_ID_PREFIX}.windowPosition"
SIDEBAR_VISIBLE_KEY = f"{PLUGIN_ID_PREFIX}.sidebarVisible"  # 保留向後相容性
CONTROLS_PANEL_VISIBLE_KEY = f"{PLUGIN_ID_PREFIX}.controlsPanelVisible"
LOCKED_CHARS_KEY = f"{PLUGIN_ID_PREFIX}.lockedChars"
PREVIOUS_LOCKED_CHARS_KEY = f"{PLUGIN_ID_PREFIX}.previousLockedChars"

# del Glyphs.defaults["com.YinTzuYuan.NineBoxView.lastInput"]
# del Glyphs.defaults["com.YinTzuYuan.NineBoxView.selectedChars"]
# del Glyphs.defaults["com.YinTzuYuan.NineBoxView.currentArrangement"]
# del Glyphs.defaults["com.YinTzuYuan.NineBoxView.testMode"]
# del Glyphs.defaults["com.YinTzuYuan.NineBoxView.search"]
# del Glyphs.defaults["com.YinTzuYuan.NineBoxView.zoomFactor"]
# del Glyphs.defaults["com.YinTzuYuan.NineBoxView.showNumbers"]
# del Glyphs.defaults["com.YinTzuYuan.NineBoxView.windowSize"]
# del Glyphs.defaults["com.YinTzuYuan.NineBoxView.windowPosition"]
# del Glyphs.defaults["com.YinTzuYuan.NineBoxView.sidebarVisible"]
# del Glyphs.defaults["com.YinTzuYuan.NineBoxView.controlsPanelVisible"]
# del Glyphs.defaults["com.YinTzuYuan.NineBoxView.lockedChars"]
# del Glyphs.defaults["com.YinTzuYuan.NineBoxView.previousLockedChars"]

# 畫面尺寸常數
DEFAULT_WINDOW_SIZE = (300, 340)
MIN_WINDOW_SIZE = (200, 240)
SIDEBAR_WIDTH = 180  # 保留向後相容性
CONTROLS_PANEL_WIDTH = 180
CONTROLS_PANEL_MIN_HEIGHT = 220  # 減少最小高度，確保主視窗最小尺寸時也能完整顯示控制面板

# 繪圖相關參數
MARGIN_RATIO = 0.07
SPACING_RATIO = 0.03
MIN_ZOOM = 0.5
MAX_ZOOM = 2.0
DEFAULT_ZOOM = 1.0

# 預設 UPM 值
DEFAULT_UPM = 1000

# 效能優化設定
DEBUG_MODE = False  # 設為 True 時才會輸出除錯訊息 (階段1開發中啟用)
CACHE_ENABLED = True  # 啟用快取機制
REDRAW_THRESHOLD = 0.016  # 重繪間隔閾值（約 60 FPS）
MAX_LOCKED_POSITIONS = 8  # 最大鎖定位置數

# 九宮格配置
GRID_SIZE = 3
GRID_TOTAL = GRID_SIZE * GRID_SIZE
CENTER_POSITION = 4  # 中央位置索引（0-8）