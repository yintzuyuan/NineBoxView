# encoding: utf-8
"""
九宮格預覽外掛 - 常數定義
Nine Box Preview Plugin - Constants Definition
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
SIDEBAR_VISIBLE_KEY = f"{PLUGIN_ID_PREFIX}.sidebarVisible"

# 畫面尺寸常數
DEFAULT_WINDOW_SIZE = (300, 340)
MIN_WINDOW_SIZE = (200, 240)
SIDEBAR_WIDTH = 180

# 繪圖相關參數
MARGIN_RATIO = 0.07
SPACING_RATIO = 0.03
MIN_ZOOM = 0.5
MAX_ZOOM = 2.0
DEFAULT_ZOOM = 1.0

# 預設 UPM 值
DEFAULT_UPM = 1000 