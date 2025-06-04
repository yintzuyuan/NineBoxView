# encoding: utf-8
"""
九宮格預覽外掛 - 工具函數（優化版）
Nine Box Preview Plugin - Utility Functions (Optimized)
"""

from __future__ import division, print_function, unicode_literals
import traceback
import random
import objc
from GlyphsApp import Glyphs
from constants import (
    DEBUG_MODE, DEFAULT_UPM, MAX_LOCKED_POSITIONS, CACHE_ENABLED,
    # 偏好設定鍵值
    LAST_INPUT_KEY, SELECTED_CHARS_KEY, CURRENT_ARRANGEMENT_KEY,
    ZOOM_FACTOR_KEY, WINDOW_POSITION_KEY, CONTROLS_PANEL_VISIBLE_KEY,
    LOCKED_CHARS_KEY, PREVIOUS_LOCKED_CHARS_KEY, LOCK_MODE_KEY,
    SIDEBAR_VISIBLE_KEY,
    # 預設值
    DEFAULT_ZOOM
)

# 全域快取
_width_cache = {}
_glyph_cache = {}

# === 除錯工具 ===

def debug_log(message):
    """
    條件式除錯記錄 - 僅在DEBUG_MODE=True時輸出
    Conditional debug logging - only outputs when DEBUG_MODE=True
    
    Args:
        message: 要記錄的訊息內容
    """
    if DEBUG_MODE:
        print(f"[NineBoxView Debug] {message}")

def log_to_macro_window(message):
    """
    將訊息記錄到巨集視窗 - 僅在DEBUG_MODE=True時輸出
    Log message to the Macro Window - only outputs when DEBUG_MODE=True
    
    Args:
        message: 要記錄的訊息內容
    """
    if DEBUG_MODE:
        Glyphs.clearLog()
        print(message)

# === 快取管理 ===

def clear_cache():
    """清除所有快取"""
    global _width_cache, _glyph_cache
    _width_cache.clear()
    _glyph_cache.clear()
    debug_log("快取已清除")

def get_cached_glyph(font, char_or_name):
    """
    取得快取的字形物件
    Get cached glyph object
    
    Args:
        font: 字型物件
        char_or_name: 字符或名稱
        
    Returns:
        GSGlyph or None
    """
    if not CACHE_ENABLED:
        return font.glyphs[char_or_name] if font else None
        
    cache_key = (id(font), char_or_name)
    if cache_key not in _glyph_cache:
        _glyph_cache[cache_key] = font.glyphs[char_or_name] if font else None
    return _glyph_cache[cache_key]

def get_cached_width(layer):
    """
    取得快取的圖層寬度
    Get cached layer width
    
    Args:
        layer: GSLayer 物件
        
    Returns:
        float: 圖層寬度
    """
    if not CACHE_ENABLED or not layer:
        return layer.width if layer else 0
        
    layer_id = id(layer)
    if layer_id not in _width_cache:
        _width_cache[layer_id] = layer.width
    return _width_cache[layer_id]

# === 尺寸計算 ===

def get_base_width():
    """
    取得基準寬度（優化版）
    Get the base width (optimized)
    
    Returns:
        float: 基準寬度值
    """
    try:
        if not Glyphs.font:
            return DEFAULT_UPM

        current_master = Glyphs.font.selectedFontMaster
        if not current_master:
            return DEFAULT_UPM

        # 1. 檢查主板的 Default Layer Width 參數
        try:
            # 修正 CustomParametersProxy 物件處理方式
            default_width_param = None
            for param in current_master.customParameters:
                if param.name == 'Default Layer Width':
                    default_width_param = param.value
                    break
                    
            if default_width_param:
                try:
                    # 處理可能的格式如 'han: 950'
                    if isinstance(default_width_param, str) and ':' in default_width_param:
                        value_part = default_width_param.split(':', 1)[1].strip()
                        default_width = float(value_part)
                    else:
                        default_width = float(default_width_param)
                    
                    if default_width > 0:
                        return default_width
                except (ValueError, TypeError):
                    debug_log(f"無法解析預設圖層寬度參數: {default_width_param}")
        except Exception as e:
            debug_log(f"檢查主板參數時發生錯誤: {e}")

        # 2. 使用選取的字符層寬度
        if Glyphs.font.selectedLayers:
            selected_layer = Glyphs.font.selectedLayers[0]
            return get_cached_width(selected_layer)

        # 3. 使用字型的 UPM 值
        if hasattr(Glyphs.font, 'upm'):
            return max(Glyphs.font.upm, 500)

        # 4. 預設值
        return DEFAULT_UPM
        
    except Exception as e:
        debug_log(f"get_base_width 錯誤: {e}")
        return DEFAULT_UPM

# === 字符處理 ===

def parse_input_text(text, font=None):
    """
    解析輸入文字並返回有效的字符列表（優化版）
    Parse input text and return valid character list (optimized)
    
    Args:
        text: 要解析的文字
        font: 字型對象，預設使用 Glyphs.font
    
    Returns:
        list: 有效的字符名稱列表
    """
    if font is None:
        font = Glyphs.font
    
    if not font:
        debug_log("警告：沒有開啟字型檔案")
        return []

    chars = []
    
    # 優化：預先處理空格
    cleaned_text = ' '.join(text.split())
    parts = cleaned_text.split(' ')
    
    for part in parts:
        if not part:
            continue
            
        # 先檢查是否為 Nice Name (完整名稱)
        glyph = get_cached_glyph(font, part)
        if glyph and len(part) > 1:  # Nice Name 通常長度 > 1
            # 檢查是否有 Unicode 值
            if glyph.unicode:
                try:
                    char = chr(int(glyph.unicode, 16))
                    chars.append(char)
                except ValueError:
                    chars.append(part)  # 無效 Unicode，使用名稱
            else:
                # 對於沒有 Unicode 的字符，使用名稱
                chars.append(part)
        else:
            # 不是 Nice Name，按字符逐個處理
            for c in part:
                if c and get_cached_glyph(font, c):
                    chars.append(c)
    
    return chars

def generate_arrangement(char_list, max_chars=8):
    """
    生成新的隨機排列（優化版）
    Generate a new random arrangement (optimized)
    
    Args:
        char_list: 字符列表
        max_chars: 最大字符數，預設為8
    
    Returns:
        list: 隨機排列後的字符列表
    """
    if not char_list:
        return []
    
    char_count = len(char_list)
    
    # 優化：減少列表操作
    if char_count > max_chars:
        # 隨機選擇 max_chars 個
        display_chars = random.sample(char_list, max_chars)
    elif char_count < max_chars:
        # 重複填充到 max_chars 個
        repeat_times = (max_chars + char_count - 1) // char_count
        display_chars = (char_list * repeat_times)[:max_chars]
    else:
        # 剛好足夠，直接複製
        display_chars = list(char_list)
    
    # 隨機打亂
    random.shuffle(display_chars)
    return display_chars

def validate_locked_positions(locked_chars, font):
    """
    驗證鎖定位置的有效性
    Validate locked positions
    
    Args:
        locked_chars: 鎖定字符字典
        font: 字型物件
        
    Returns:
        dict: 有效的鎖定字符字典
    """
    if not locked_chars or not font:
        return {}
    
    valid_locks = {}
    for position, char_or_name in locked_chars.items():
        if position < MAX_LOCKED_POSITIONS:
            glyph = get_cached_glyph(font, char_or_name)
            if glyph:
                valid_locks[position] = char_or_name
            else:
                debug_log(f"移除無效的鎖定字符: 位置 {position}, 字符 '{char_or_name}'")
    
    return valid_locks

def apply_locked_chars(arrangement, locked_chars, selected_chars):
    """
    應用鎖定字符到排列中（修正版）
    Apply locked characters to arrangement (Fixed)
    
    Args:
        arrangement: 基礎隨機排列
        locked_chars: 鎖定字符字典
        selected_chars: 選擇的字符列表（此參數已不需要，保留以維持向後兼容）
        
    Returns:
        list: 應用鎖定後的排列
    """
    if not locked_chars:
        return arrangement
    
    # 創建新排列的副本
    new_arrangement = list(arrangement)
    
    # 只應用鎖定字符，不重新分配未鎖定位置
    # 將鎖定字符應用到指定位置
    for position, char_or_name in locked_chars.items():
        if position < len(new_arrangement):
            new_arrangement[position] = char_or_name
            debug_log(f"[Lock] 位置 {position} 鎖定為字符：{char_or_name}")
        else:
            debug_log(f"[Lock] 警告：鎖定位置 {position} 超出範圍")
    
    debug_log(f"[Lock] 應用鎖定後的排列：{new_arrangement}")
    return new_arrangement

# === 偏好設定管理 ===

def load_preferences(plugin):
    """
    載入所有偏好設定
    
    Args:
        plugin: 外掛實例
    """
    # 基本設定
    plugin.lastInput = Glyphs.defaults.get(LAST_INPUT_KEY, "")
    plugin.selectedChars = Glyphs.defaults.get(SELECTED_CHARS_KEY, [])
    plugin.currentArrangement = Glyphs.defaults.get(CURRENT_ARRANGEMENT_KEY, [])
    plugin.zoomFactor = float(Glyphs.defaults.get(ZOOM_FACTOR_KEY, DEFAULT_ZOOM))
    
    # 視窗位置
    plugin.windowPosition = Glyphs.defaults.get(WINDOW_POSITION_KEY, None)
    
    # 控制面板可見性
    controls_panel_visible_value = Glyphs.defaults.get(CONTROLS_PANEL_VISIBLE_KEY)
    
    if controls_panel_visible_value is not None:
        plugin.controlsPanelVisible = bool(controls_panel_visible_value)
        plugin.sidebarVisible = bool(controls_panel_visible_value)  # 同步
    else:
        # 向後相容性
        sidebar_visible_value = Glyphs.defaults.get(SIDEBAR_VISIBLE_KEY)
        if sidebar_visible_value is not None:
            plugin.controlsPanelVisible = bool(sidebar_visible_value)
            plugin.sidebarVisible = bool(sidebar_visible_value)
        else:
            plugin.controlsPanelVisible = True
            plugin.sidebarVisible = True
    
    # 載入鎖頭狀態
    lock_mode_value = Glyphs.defaults.get(LOCK_MODE_KEY)
    if lock_mode_value is not None:
        plugin.isInClearMode = bool(lock_mode_value)
    else:
        plugin.isInClearMode = False  # 預設為上鎖狀態
    
    # 鎖定字符
    _load_locked_chars(plugin)
    
    # 如果有選定字符但沒有排列，則生成初始排列
    if plugin.selectedChars and not plugin.currentArrangement:
        # 需要通過事件處理器生成排列
        if hasattr(plugin, 'event_handlers'):
            plugin.event_handlers.generate_new_arrangement()
    
    # 如果控制面板已初始化，更新其UI
    if (hasattr(plugin, 'windowController') and plugin.windowController and 
        hasattr(plugin.windowController, 'controlsPanelView') and 
        plugin.windowController.controlsPanelView):
        plugin.windowController.controlsPanelView.update_ui(plugin, update_lock_fields=True)
    
    debug_log("偏好設定載入完成")

def save_preferences(plugin):
    """
    儲存所有偏好設定
    
    Args:
        plugin: 外掛實例
    """
    # 基本設定
    Glyphs.defaults[LAST_INPUT_KEY] = plugin.lastInput
    Glyphs.defaults[SELECTED_CHARS_KEY] = plugin.selectedChars
    Glyphs.defaults[CURRENT_ARRANGEMENT_KEY] = plugin.currentArrangement
    Glyphs.defaults[ZOOM_FACTOR_KEY] = plugin.zoomFactor
    
    # 控制面板可見性 - 同時更新新舊兩個 key
    current_controls_panel_visible = getattr(plugin, 'controlsPanelVisible', True)
    Glyphs.defaults[CONTROLS_PANEL_VISIBLE_KEY] = current_controls_panel_visible
    Glyphs.defaults[SIDEBAR_VISIBLE_KEY] = current_controls_panel_visible  # 保持同步
    
    # 儲存鎖頭狀態
    if hasattr(plugin, 'isInClearMode'):
        Glyphs.defaults[LOCK_MODE_KEY] = plugin.isInClearMode
    
    # 視窗位置
    if hasattr(plugin, 'windowPosition') and plugin.windowPosition:
        Glyphs.defaults[WINDOW_POSITION_KEY] = plugin.windowPosition
    
    # 鎖定字符
    _save_locked_chars(plugin)
    
    debug_log("偏好設定儲存完成")

def _load_locked_chars(plugin):
    """載入鎖定字符設定（內部函數）"""
    try:
        locked_chars_str = Glyphs.defaults.get(LOCKED_CHARS_KEY)
        if locked_chars_str:
            plugin.lockedChars = {int(k): v for k, v in locked_chars_str.items()}
            # 驗證載入的鎖定字符
            if Glyphs.font:
                plugin.lockedChars = validate_locked_positions(plugin.lockedChars, Glyphs.font)
            debug_log(f"已載入鎖定字符：{plugin.lockedChars}")
        else:
            plugin.lockedChars = {}
            debug_log("沒有已儲存的鎖定字符")
        
        previous_locked_chars_str = Glyphs.defaults.get(PREVIOUS_LOCKED_CHARS_KEY)
        if previous_locked_chars_str:
            plugin.previousLockedChars = {int(k): v for k, v in previous_locked_chars_str.items()}
            debug_log(f"已載入先前鎖定字符：{plugin.previousLockedChars}")
        else:
            plugin.previousLockedChars = {}
            
    except Exception as e:
        debug_log(f"載入鎖定字符時發生錯誤：{e}")
        if DEBUG_MODE:
            print(traceback.format_exc())
        plugin.lockedChars = {}
        plugin.previousLockedChars = {}

def _save_locked_chars(plugin):
    """儲存鎖定字符設定（內部函數）"""
    try:
        if hasattr(plugin, 'lockedChars'):
            # 驗證鎖定字符的有效性
            if Glyphs.font:
                plugin.lockedChars = validate_locked_positions(plugin.lockedChars, Glyphs.font)
            # 轉換並儲存
            locked_chars_str = {str(k): v for k, v in plugin.lockedChars.items()}
            Glyphs.defaults[LOCKED_CHARS_KEY] = locked_chars_str
            debug_log(f"已儲存鎖定字符：{plugin.lockedChars}")
        
        if hasattr(plugin, 'previousLockedChars'):
            # 轉換並儲存
            previous_locked_chars_str = {str(k): v for k, v in plugin.previousLockedChars.items()}
            Glyphs.defaults[PREVIOUS_LOCKED_CHARS_KEY] = previous_locked_chars_str
            debug_log(f"已儲存先前鎖定字符：{plugin.previousLockedChars}")
            
    except Exception as e:
        debug_log(f"儲存鎖定字符時發生錯誤：{e}")
        if DEBUG_MODE:
            print(traceback.format_exc())
