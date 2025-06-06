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
    ORIGINAL_ARRANGEMENT_KEY,
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
        plugin.originalArrangement = Glyphs.defaults[ORIGINAL_ARRANGEMENT_KEY] or []
        plugin.zoomFactor = Glyphs.defaults[ZOOM_FACTOR_KEY] or DEFAULT_ZOOM
        
        # 處理窗口位置 - 統一使用 list 格式
        window_pos = Glyphs.defaults[WINDOW_POSITION_KEY]
        
        # 檢查是否為 NSArray（Objective-C 陣列）
        if window_pos:
            try:
                # 嘗試直接存取元素（NSArray 支援索引存取）
                if len(window_pos) >= 2:
                    plugin.windowPosition = [float(window_pos[0]), float(window_pos[1])]
                    debug_log(f"成功從 NSArray/list/tuple 載入視窗位置: {plugin.windowPosition}")
                else:
                    plugin.windowPosition = None
                    debug_log(f"視窗位置資料長度不足: {len(window_pos)}")
            except (TypeError, IndexError):
                # 如果不是陣列類型，檢查是否為字典
                if isinstance(window_pos, dict) and 'x' in window_pos and 'y' in window_pos:
                    # 向後相容：支援舊的字典格式
                    plugin.windowPosition = [float(window_pos['x']), float(window_pos['y'])]
                    debug_log(f"從字典格式載入視窗位置: {plugin.windowPosition}")
                else:
                    plugin.windowPosition = None
                    debug_log(f"無法解析視窗位置資料，類型: {type(window_pos)}")
        else:
            plugin.windowPosition = None
            debug_log("沒有儲存的視窗位置")
            
        plugin.controlsPanelVisible = Glyphs.defaults[CONTROLS_PANEL_VISIBLE_KEY]
        
        # 使用 JSON 解碼載入 lockedChars
        import json
        
        # 載入鎖定字符並處理 JSON 解碼
        locked_chars_json = Glyphs.defaults[LOCKED_CHARS_KEY]
        plugin.lockedChars = {}
        
        if locked_chars_json:
            try:
                # 嘗試解析 JSON 字串
                if isinstance(locked_chars_json, str):
                    locked_chars_dict = json.loads(locked_chars_json)
                    
                    # 將字串鍵轉換為整數鍵
                    for position_str, char_or_name in locked_chars_dict.items():
                        try:
                            position = int(position_str)
                            plugin.lockedChars[position] = char_or_name
                        except:
                            debug_log(f"警告: 忽略非整數位置 '{position_str}'")
                elif isinstance(locked_chars_json, dict):
                    # 舊格式兼容 - 直接是字典
                    for position_str, char_or_name in locked_chars_json.items():
                        try:
                            position = int(position_str)
                            plugin.lockedChars[position] = char_or_name
                        except:
                            debug_log(f"警告: 忽略非整數位置 '{position_str}'")
            except Exception as e:
                error_log(f"解析 lockedChars JSON 時出錯: {e}")
        
        # 載入前一版鎖定字符並處理 JSON 解碼
        previous_locked_chars_json = Glyphs.defaults[PREVIOUS_LOCKED_CHARS_KEY]
        plugin.previousLockedChars = {}
        
        if previous_locked_chars_json:
            try:
                # 嘗試解析 JSON 字串
                if isinstance(previous_locked_chars_json, str):
                    previous_locked_chars_dict = json.loads(previous_locked_chars_json)
                    
                    # 將字串鍵轉換為整數鍵
                    for position_str, char_or_name in previous_locked_chars_dict.items():
                        try:
                            position = int(position_str)
                            plugin.previousLockedChars[position] = char_or_name
                        except:
                            debug_log(f"警告: 忽略非整數位置 '{position_str}'")
                elif isinstance(previous_locked_chars_json, dict):
                    # 舊格式兼容 - 直接是字典
                    for position_str, char_or_name in previous_locked_chars_json.items():
                        try:
                            position = int(position_str)
                            plugin.previousLockedChars[position] = char_or_name
                        except:
                            debug_log(f"警告: 忽略非整數位置 '{position_str}'")
            except Exception as e:
                error_log(f"解析 previousLockedChars JSON 時出錯: {e}")
        
        plugin.isInClearMode = Glyphs.defaults[LOCK_MODE_KEY] or False
        # 同步兩個屬性（如果需要）
        plugin.isLockModeActive = plugin.isInClearMode
        
        # 確保 controlsPanelVisible 有預設值
        if plugin.controlsPanelVisible is None:
            plugin.controlsPanelVisible = True
        
        # 額外除錯：記錄所有載入的屬性
        debug_log(f"plugin.isLockModeActive = {getattr(plugin, 'isLockModeActive', 'Not set')}")
        debug_log(f"plugin.isInClearMode = {plugin.isInClearMode}")
        
        debug_log(f"載入偏好設定：lastInput='{plugin.lastInput}', "
                 f"selectedChars={plugin.selectedChars}, "
                 f"lockedChars={plugin.lockedChars}, "
                 f"isInClearMode={plugin.isInClearMode}, "
                 f"windowPosition={plugin.windowPosition}")
        
        # 額外除錯資訊
        debug_log(f"WINDOW_POSITION_KEY = '{WINDOW_POSITION_KEY}'")
        debug_log(f"Glyphs.defaults[WINDOW_POSITION_KEY] = {Glyphs.defaults.get(WINDOW_POSITION_KEY)}")
        debug_log(f"Type of window_pos = {type(window_pos)}")
        debug_log(f"window_pos value = {window_pos}")
        debug_log(f"plugin.windowPosition = {plugin.windowPosition}")
        
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
        Glyphs.defaults[ORIGINAL_ARRANGEMENT_KEY] = getattr(plugin, 'originalArrangement', [])
        Glyphs.defaults[ZOOM_FACTOR_KEY] = plugin.zoomFactor
        
        # 處理窗口位置 - 統一使用 list 格式
        if hasattr(plugin, 'windowController') and plugin.windowController:
            if hasattr(plugin.windowController, 'window') and plugin.windowController.window():
                frame_origin = plugin.windowController.window().frame().origin
                # 儲存為 list 格式，確保一致性
                window_pos_list = [float(frame_origin.x), float(frame_origin.y)]
                Glyphs.defaults[WINDOW_POSITION_KEY] = window_pos_list
                debug_log(f"已儲存視窗位置：{window_pos_list}")
                debug_log(f"WINDOW_POSITION_KEY = '{WINDOW_POSITION_KEY}'")
                debug_log(f"驗證儲存：Glyphs.defaults[WINDOW_POSITION_KEY] = {Glyphs.defaults.get(WINDOW_POSITION_KEY)}")
        
        Glyphs.defaults[CONTROLS_PANEL_VISIBLE_KEY] = plugin.controlsPanelVisible
        
        # 使用 JSON 編碼安全處理 lockedChars 和 previousLockedChars
        import json
        
        # 安全處理 lockedChars - 使用 JSON 字串格式
        if hasattr(plugin, 'lockedChars') and plugin.lockedChars:
            # 將整數鍵轉換為字符串鍵，以便 JSON 序列化
            locked_chars_json = {}
            for position, char_or_name in plugin.lockedChars.items():
                locked_chars_json[str(position)] = char_or_name
            
            try:
                # 將字典轉換為 JSON 字串
                json_str = json.dumps(locked_chars_json)
                Glyphs.defaults[LOCKED_CHARS_KEY] = json_str
                debug_log(f"已將 lockedChars 編碼為 JSON: {json_str}")
            except Exception as e:
                error_log(f"儲存 lockedChars 時 JSON 編碼失敗: {e}")
                Glyphs.defaults[LOCKED_CHARS_KEY] = "{}"  # 使用空字典字串作為安全值
        else:
            Glyphs.defaults[LOCKED_CHARS_KEY] = "{}"  # 使用空字典字串
            
        # 安全處理 previousLockedChars - 使用 JSON 字串格式
        if hasattr(plugin, 'previousLockedChars') and plugin.previousLockedChars:
            # 將整數鍵轉換為字符串鍵，以便 JSON 序列化
            previous_locked_chars_json = {}
            for position, char_or_name in plugin.previousLockedChars.items():
                previous_locked_chars_json[str(position)] = char_or_name
            
            try:
                # 將字典轉換為 JSON 字串
                json_str = json.dumps(previous_locked_chars_json)
                Glyphs.defaults[PREVIOUS_LOCKED_CHARS_KEY] = json_str
                debug_log(f"已將 previousLockedChars 編碼為 JSON: {json_str}")
            except Exception as e:
                error_log(f"儲存 previousLockedChars 時 JSON 編碼失敗: {e}")
                Glyphs.defaults[PREVIOUS_LOCKED_CHARS_KEY] = "{}"  # 使用空字典字串作為安全值
        else:
            Glyphs.defaults[PREVIOUS_LOCKED_CHARS_KEY] = "{}"  # 使用空字典字串
            
        Glyphs.defaults[LOCK_MODE_KEY] = plugin.isInClearMode
        
        debug_log("已儲存偏好設定")
        debug_log(f"最終確認視窗位置：{Glyphs.defaults.get(WINDOW_POSITION_KEY)}")
        
    except Exception as e:
        error_log("儲存偏好設定時發生錯誤", e)

# === 字符處理 ===

def get_cached_glyph(font, char_or_name):
    """從快取或字型取得字符（優化版）
    
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
    
    # 優化：使用 Glyphs 內建的快速查找方法
    try:
        # 1. 直接通過 glyphs 字典存取（最快）
        glyph = font.glyphs[char_or_name]
        if glyph:
            if CACHE_ENABLED:
                _glyph_cache[cache_key] = glyph
            return glyph
    except:
        pass
    
    # 2. 如果是單一字符，嘗試通過 Unicode
    if len(char_or_name) == 1:
        try:
            unicode_val = format(ord(char_or_name), '04X')
            glyph = font.glyphs[unicode_val]
            if glyph:
                if CACHE_ENABLED:
                    _glyph_cache[cache_key] = glyph
                return glyph
        except:
            pass
    
    # 3. 嘗試用 glyphForName（Nice Name）
    try:
        glyph = font.glyphForName_(char_or_name)
        if glyph:
            if CACHE_ENABLED:
                _glyph_cache[cache_key] = glyph
            return glyph
    except:
        pass
    
    # 移除遍歷所有字符的部分，這在大型字型中會造成嚴重效能問題
    # 如果上述方法都找不到，就返回 None
    
    return None

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
    import random  # 確保在函數開頭就導入 random 模組
    
    if not chars:
        return []
    
    # 如果字符數量不足，重複使用
    if len(chars) < count:
        arrangement = chars * (count // len(chars) + 1)
        arrangement = arrangement[:count]
    else:
        # 不再只取前 count 個字符，而是從所有字符中隨機選擇
        arrangement = random.sample(chars, min(count, len(chars)))
        # 如果還不夠，填充剩餘的位置
        while len(arrangement) < count:
            arrangement.append(random.choice(chars))
    
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
        # 確保返回可變列表
        return list(arrangement) if arrangement else []
    
    # 複製排列以避免修改原始資料
    # 確保結果是可變列表
    result = list(arrangement) if arrangement else []
    
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