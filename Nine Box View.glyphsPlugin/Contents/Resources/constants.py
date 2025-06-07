# encoding: utf-8
"""
九宮格預覽外掛 - 常數定義（最佳化版）
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
LOCK_MODE_KEY = f"{PLUGIN_ID_PREFIX}.lockMode"  # 鎖頭狀態（True=解鎖，False=上鎖）
ORIGINAL_ARRANGEMENT_KEY = f"{PLUGIN_ID_PREFIX}.originalArrangement"  # 儲存原始隨機排列

# 畫面尺寸常數
DEFAULT_WINDOW_SIZE = (300, 340)
MIN_WINDOW_SIZE = (270, 300)
SIDEBAR_WIDTH = 180  # 保留向後相容性
CONTROLS_PANEL_WIDTH = 160
CONTROLS_PANEL_MIN_HEIGHT = 220  # 減少最小高度，確保主視窗最小尺寸時也能完整顯示控制面板
CONTROLS_PANEL_SPACING = 15  # 控制面板與主視窗之間的間距，用於避免陰影干擾

# 繪圖相關參數
MARGIN_RATIO = 0.07
SPACING_RATIO = 0.0
MIN_ZOOM = 0.5
MAX_ZOOM = 2.0
DEFAULT_ZOOM = 0.85

# 預設 UPM 值
DEFAULT_UPM = 1000

# 效能最佳化設定
REDRAW_THRESHOLD = 0.016  # 重繪間隔閾值（約 60 FPS）
MAX_LOCKED_POSITIONS = 8  # 最大鎖定位置數

# 九宮格設定
GRID_SIZE = 3
GRID_TOTAL = GRID_SIZE * GRID_SIZE
CENTER_POSITION = 4  # 中央位置索引（0-8）

# 顯示選項
DEFAULT_PREVIEW_DPI = 72.0

# ========== 訊息列印模式設定 ==========
# 除錯模式開關
# False = 一般模式（預設）：只顯示錯誤訊息和 traceback，隱藏狀態訊息
# True = 除錯模式：顯示所有錯誤訊息、traceback 和狀態訊息
DEBUG_MODE = False

# 快取設定
CACHE_ENABLED = True  # 啟用快取機制