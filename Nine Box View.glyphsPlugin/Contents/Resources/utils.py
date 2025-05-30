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
from constants import DEBUG_MODE, DEFAULT_UPM, MAX_LOCKED_POSITIONS, CACHE_ENABLED

# 全域快取
_width_cache = {}
_glyph_cache = {}

def debug_log(message):
    """
    條件式除錯記錄
    Conditional debug logging
    
    Args:
        message: 要記錄的訊息內容
    """
    if DEBUG_MODE:
        print(f"[NineBoxView Debug] {message}")

def log_to_macro_window(message):
    """
    將訊息記錄到巨集視窗（僅在需要時）
    Log message to the Macro Window (only when needed)
    
    Args:
        message: 要記錄的訊息內容
    """
    if DEBUG_MODE:
        Glyphs.clearLog()
        print(message)

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
        default_width_param = current_master.customParameters.get('Default Layer Width')
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
    應用鎖定字符到排列中
    Apply locked characters to arrangement
    
    Args:
        arrangement: 基礎排列
        locked_chars: 鎖定字符字典
        selected_chars: 選擇的字符列表
        
    Returns:
        list: 應用鎖定後的排列
    """
    if not locked_chars:
        return arrangement
    
    new_arrangement = list(arrangement)
    locked_positions = set()
    
    # 應用鎖定字符
    for position, char_or_name in locked_chars.items():
        if position < len(new_arrangement):
            new_arrangement[position] = char_or_name
            locked_positions.add(position)
    
    # 確保未鎖定的字符至少出現一次
    if selected_chars and locked_positions:
        locked_chars_used = set(new_arrangement[pos] for pos in locked_positions)
        remaining_chars = [char for char in set(selected_chars) if char not in locked_chars_used]
        available_positions = [i for i in range(len(new_arrangement)) if i not in locked_positions]
        
        if remaining_chars and available_positions:
            # 優化：使用更有效率的方式分配剩餘字符
            for i, char in enumerate(remaining_chars):
                if i < len(available_positions):
                    new_arrangement[available_positions[i]] = char
    
    return new_arrangement