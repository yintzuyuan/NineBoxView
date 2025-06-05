# encoding: utf-8
"""
九宮格預覽外掛 - 工具函數（優化版）
Nine Box Preview Plugin - Utility Functions (Optimized)
"""

from __future__ import division, print_function, unicode_literals
import traceback
import random
from GlyphsApp import Glyphs

# 匯入常數
from constants import (
    CACHE_ENABLED, DEFAULT_UPM, MAX_LOCKED_POSITIONS,
    LAST_INPUT_KEY, SELECTED_CHARS_KEY, CURRENT_ARRANGEMENT_KEY,
    ZOOM_FACTOR_KEY, WINDOW_POSITION_KEY, CONTROLS_PANEL_VISIBLE_KEY,
    LOCKED_CHARS_KEY, PREVIOUS_LOCKED_CHARS_KEY, LOCK_MODE_KEY,
    DEFAULT_ZOOM, DEBUG_MODE
)

# === 快取相關 ===

# 全域快取變數
_glyph_cache = {}
_width_cache = {}

def clear_cache():
    """清除快取"""
    global _glyph_cache, _width_cache
    _glyph_cache.clear()
    _width_cache.clear()

# === 日誌相關 ===

def log_to_macro_window(message):
    """記錄訊息到 Macro 視窗"""
    try:
        Glyphs.showMacroWindow()
        print(message)
    except:
        print(message)

def debug_log(message):
    """除錯日誌輸出 - 只在 DEBUG_MODE 開啟時輸出狀態訊息
    
    Args:
        message: 要輸出的訊息
    """
    if DEBUG_MODE:
        print(f"[九宮格預覽] {message}")

def error_log(error_message, exception=None):
    """錯誤日誌輸出 - 無論什麼模式都會輸出錯誤訊息
    
    Args:
        error_message: 錯誤描述
        exception: 例外物件（可選）
    """
    print(f"[九宮格預覽錯誤] {error_message}")
    if exception and not DEBUG_MODE:
        # 一般模式：只印出簡化的錯誤訊息
        print(f"錯誤類型：{type(exception).__name__}")
        print(f"錯誤內容：{str(exception)}")
    elif exception and DEBUG_MODE:
        # 除錯模式：印出完整的 traceback
        print(traceback.format_exc())

# === 偏好設定管理 ===

def load_preferences(plugin):
    """載入偏好設定
    
    Args:
        plugin: 外掛實例
    """
    try:
        # 載入各項設定
        plugin.lastInput = Glyphs.defaults[LAST_INPUT_KEY] or ""
        plugin.selectedChars = Glyphs.defaults[SELECTED_CHARS_KEY] or []
        plugin.currentArrangement = Glyphs.defaults[CURRENT_ARRANGEMENT_KEY] or []
        plugin.zoomFactor = Glyphs.defaults[ZOOM_FACTOR_KEY] or DEFAULT_ZOOM
        plugin.windowPosition = Glyphs.defaults[WINDOW_POSITION_KEY]
        plugin.controlsPanelVisible = Glyphs.defaults[CONTROLS_PANEL_VISIBLE_KEY]
        plugin.lockedChars = Glyphs.defaults[LOCKED_CHARS_KEY] or {}
        plugin.previousLockedChars = Glyphs.defaults[PREVIOUS_LOCKED_CHARS_KEY] or {}
        plugin.isInClearMode = Glyphs.defaults[LOCK_MODE_KEY] or False
        
        # 確保 controlsPanelVisible 有預設值
        if plugin.controlsPanelVisible is None:
            plugin.controlsPanelVisible = True
        
        # 處理 lockedChars 的鍵值類型
        if isinstance(plugin.lockedChars, dict):
            plugin.lockedChars = {int(k): v for k, v in plugin.lockedChars.items()}
        
        debug_log(f"載入偏好設定：lastInput='{plugin.lastInput}', "
                 f"selectedChars={plugin.selectedChars}, "
                 f"lockedChars={plugin.lockedChars}, "
                 f"isInClearMode={plugin.isInClearMode}")
        
    except Exception as e:
        error_log("載入偏好設定時發生錯誤", e)

def save_preferences(plugin):
    """儲存偏好設定
    
    Args:
        plugin: 外掛實例
    """
    try:
        # 儲存各項設定
        Glyphs.defaults[LAST_INPUT_KEY] = plugin.lastInput
        Glyphs.defaults[SELECTED_CHARS_KEY] = plugin.selectedChars
        Glyphs.defaults[CURRENT_ARRANGEMENT_KEY] = plugin.currentArrangement
        Glyphs.defaults[ZOOM_FACTOR_KEY] = plugin.zoomFactor
        
        if hasattr(plugin, 'windowController') and plugin.windowController:
            if hasattr(plugin.windowController, 'window') and plugin.windowController.window():
                Glyphs.defaults[WINDOW_POSITION_KEY] = plugin.windowController.window().frame().origin
        
        Glyphs.defaults[CONTROLS_PANEL_VISIBLE_KEY] = plugin.controlsPanelVisible
        Glyphs.defaults[LOCKED_CHARS_KEY] = plugin.lockedChars
        Glyphs.defaults[PREVIOUS_LOCKED_CHARS_KEY] = plugin.previousLockedChars
        Glyphs.defaults[LOCK_MODE_KEY] = plugin.isInClearMode
        
        debug_log("已儲存偏好設定")
        
    except Exception as e:
        error_log("儲存偏好設定時發生錯誤", e)

# === 字符處理 ===

def get_cached_glyph(font, char_or_name):
    """從快取或字型取得字符
    
    Args:
        font: 字型物件
        char_or_name: 字符或字符名稱
        
    Returns:
        GSGlyph 物件或 None
    """
    if not font or not char_or_name:
        return None
    
    # 檢查快取
    cache_key = (id(font), char_or_name)
    if CACHE_ENABLED and cache_key in _glyph_cache:
        return _glyph_cache[cache_key]
    
    # 嘗試取得字符
    glyph = None
    
    # 嘗試直接取得
    if char_or_name in font.glyphs:
        glyph = font.glyphs[char_or_name]
    
    # 嘗試用 glyphForCharacter（對單一字符）
    elif len(char_or_name) == 1:
        glyph = font.glyphForCharacter_(ord(char_or_name))
    
    # 嘗試用 glyphForName（Nice Name）
    if not glyph:
        glyph = font.glyphForName_(char_or_name)
    
    # 嘗試搜尋（包含）
    if not glyph:
        for g in font.glyphs:
            if g.name and char_or_name in g.name:
                glyph = g
                break
    
    # 儲存到快取
    if CACHE_ENABLED and glyph:
        _glyph_cache[cache_key] = glyph
    
    return glyph

def get_cached_width(layer):
    """從快取取得字符寬度
    
    Args:
        layer: 圖層物件
        
    Returns:
        字符寬度
    """
    if not layer:
        return 0
    
    cache_key = id(layer)
    if CACHE_ENABLED and cache_key in _width_cache:
        return _width_cache[cache_key]
    
    width = layer.width
    
    if CACHE_ENABLED:
        _width_cache[cache_key] = width
    
    return width

def parse_input_text(text):
    """解析輸入文字，提取有效字符（支援 Nice Names）
    
    Args:
        text: 輸入文字
        
    Returns:
        有效字符列表
    """
    if not text or not Glyphs.font:
        return []
    
    chars = []
    
    # 優先處理空格分隔的 Nice Names
    parts = text.split()
    
    for part in parts:
        if not part:
            continue
        
        # 檢查是否為有效的字符或 Nice Name
        if get_cached_glyph(Glyphs.font, part):
            chars.append(part)
        else:
            # 如果不是 Nice Name，嘗試解析為單個字符
            for char in part:
                if get_cached_glyph(Glyphs.font, char):
                    chars.append(char)
    
    # 如果沒有空格分隔，則嘗試解析每個字符
    if not chars and not ' ' in text:
        for char in text:
            if get_cached_glyph(Glyphs.font, char):
                chars.append(char)
    
    return chars

def generate_arrangement(chars, count=8):
    """生成隨機字符排列
    
    Args:
        chars: 可用字符列表
        count: 需要的字符數量
        
    Returns:
        隨機排列的字符列表
    """
    if not chars:
        return []
    
    # 如果字符數量不足，重複使用
    if len(chars) < count:
        arrangement = chars * (count // len(chars) + 1)
        arrangement = arrangement[:count]
    else:
        arrangement = chars[:count]
    
    # 隨機打亂
    random.shuffle(arrangement)
    
    return arrangement

def apply_locked_chars(arrangement, locked_chars, available_chars):
    """應用鎖定字符到排列中
    
    Args:
        arrangement: 基礎排列
        locked_chars: 鎖定字符字典
        available_chars: 可用字符列表（用於填充空位）
        
    Returns:
        應用鎖定後的排列
    """
    if not locked_chars:
        return arrangement
    
    # 複製排列以避免修改原始資料
    result = arrangement[:]
    
    # 確保結果有足夠的長度
    while len(result) < 8:
        if available_chars:
            result.append(random.choice(available_chars))
        else:
            result.append("A")  # 預設字符
    
    # 應用鎖定字符
    for position, char_or_name in locked_chars.items():
        if 0 <= position < 8:
            result[position] = char_or_name
    
    return result

def validate_locked_positions(locked_chars, font):
    """驗證鎖定字符的有效性
    
    Args:
        locked_chars: 鎖定字符字典
        font: 字型物件
        
    Returns:
        驗證後的鎖定字符字典
    """
    if not locked_chars or not font:
        return {}
    
    valid_locked = {}
    
    for position, char_or_name in locked_chars.items():
        # 驗證位置
        try:
            pos = int(position)
            if pos < 0 or pos >= MAX_LOCKED_POSITIONS:
                continue
        except:
            continue
        
        # 驗證字符
        if get_cached_glyph(font, char_or_name):
            valid_locked[pos] = char_or_name
    
    return valid_locked

# === 寬度計算 ===

def get_base_width():
    """取得基準寬度（用於佈局計算）
    
    Returns:
        基準寬度值
    """
    try:
        # 如果有開啟的字型，使用其 UPM 值
        if Glyphs.font:
            return Glyphs.font.upm or DEFAULT_UPM
        else:
            return DEFAULT_UPM
    except Exception as e:
        error_log("取得基準寬度時發生錯誤", e)
        return DEFAULT_UPM