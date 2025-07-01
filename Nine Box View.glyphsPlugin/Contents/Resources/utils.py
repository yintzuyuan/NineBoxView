# encoding: utf-8
"""
九宮格預覽外掛 - 工具函數
Nine Box Preview Plugin - Utility Functions
"""

from __future__ import division, print_function, unicode_literals
import traceback
import random
from GlyphsApp import Glyphs, objc

# 匯入常數
from constants import (
    CACHE_ENABLED, DEFAULT_UPM, MAX_LOCKED_POSITIONS,
    LAST_INPUT_KEY, SELECTED_CHARS_KEY, CURRENT_ARRANGEMENT_KEY, WINDOW_SIZE_KEY,
    ZOOM_FACTOR_KEY, WINDOW_POSITION_KEY, CONTROLS_PANEL_VISIBLE_KEY,
    LOCKED_CHARS_KEY, PREVIOUS_LOCKED_CHARS_KEY, LOCK_MODE_KEY,
    ORIGINAL_ARRANGEMENT_KEY, FINAL_ARRANGEMENT_KEY,
    DEFAULT_ZOOM, DEBUG_MODE, FULL_ARRANGEMENT_SIZE, LEGACY_ARRANGEMENT_SIZE
)

# === 快取相關 ===

# 全域快取變數
_glyph_cache = {}
_width_cache = {}

def clear_cache():
    """清除快取（包含官方和傳統快取）"""
    global _glyph_cache, _width_cache
    
    # 清除傳統快取
    _glyph_cache.clear()
    _width_cache.clear()
    
    # 清除官方字型快取（如果可用）
    try:
        font = Glyphs.font
        if font and hasattr(font, 'tempData'):
            # 清除字符快取
            keys_to_remove = [key for key in font.tempData.keys() if key.startswith('glyph_cache_')]
            for key in keys_to_remove:
                del font.tempData[key]
            
            debug_log(f"已清除 {len(keys_to_remove)} 個官方字符快取項目")
    except Exception as e:
        debug_log(f"清除官方快取時發生錯誤: {e}")
    
    debug_log("已清除所有快取")

# === 記錄相關 ===

def log_to_macro_window(message):
    """記錄訊息到巨集視窗"""
    try:
        Glyphs.showMacroWindow()
        print(message)
    except:
        print(message)

def debug_log(message):
    """除錯記錄輸出 - 只在 DEBUG_MODE 開啟時輸出狀態訊息
    
    Args:
        message: 要輸出的訊息
    """
    if DEBUG_MODE:
        print(f"[九宮格預覽] {message}")

def error_log(error_message, exception=None):
    """錯誤記錄輸出 - 無論什麼模式都會輸出錯誤訊息
    
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
        
        # 載入排列並處理向前相容性
        # 載入順序：finalArrangement > currentArrangement > originalArrangement
        loaded_final = Glyphs.defaults[FINAL_ARRANGEMENT_KEY] or []
        plugin.finalArrangement = _convert_arrangement_to_9_slots(loaded_final)
        
        loaded_arrangement = Glyphs.defaults[CURRENT_ARRANGEMENT_KEY] or []
        plugin.currentArrangement = _convert_arrangement_to_9_slots(loaded_arrangement)
        
        loaded_original = Glyphs.defaults[ORIGINAL_ARRANGEMENT_KEY] or []
        plugin.originalArrangement = _convert_arrangement_to_9_slots(loaded_original)
        
        # 智慧載入優先順序：確保關閉前的狀態能被正確恢復
        debug_log(f"載入排列狀態分析:")
        debug_log(f"  - finalArrangement: {plugin.finalArrangement} (有效: {bool(plugin.finalArrangement and any(item is not None for item in plugin.finalArrangement))})")
        debug_log(f"  - currentArrangement: {plugin.currentArrangement} (有效: {bool(plugin.currentArrangement and any(item is not None for item in plugin.currentArrangement))})")
        debug_log(f"  - originalArrangement: {plugin.originalArrangement} (有效: {bool(plugin.originalArrangement and any(item is not None for item in plugin.originalArrangement))})")
        
        # 1. 優先使用最終狀態（關閉前的狀態）
        if plugin.finalArrangement and any(item is not None for item in plugin.finalArrangement):
            plugin.currentArrangement = list(plugin.finalArrangement)
            debug_log("✅ 使用 finalArrangement 作為初始排列（關閉前狀態）")
        # 2. 次選使用當前排列（如果有效）
        elif plugin.currentArrangement and any(item is not None for item in plugin.currentArrangement):
            debug_log("✅ 保持現有的 currentArrangement（已有有效排列）")
        # 3. 最後使用原始排列
        elif plugin.originalArrangement and any(item is not None for item in plugin.originalArrangement):
            plugin.currentArrangement = list(plugin.originalArrangement)
            debug_log("✅ 使用 originalArrangement 作為初始排列（備用）")
        else:
            debug_log("⚠️ 沒有任何有效的已儲存排列，將由初始化邏輯生成新排列")
        
        debug_log(f"最終載入的 currentArrangement: {plugin.currentArrangement}")
        plugin.zoomFactor = Glyphs.defaults[ZOOM_FACTOR_KEY] or DEFAULT_ZOOM
        plugin.windowSize = Glyphs.defaults[WINDOW_SIZE_KEY] or plugin.DEFAULT_WINDOW_SIZE
        
        # 處理視窗位置 - 統一使用 list 格式
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
            
        # 處理控制面板可見性
        # 使用 .get() 以安全處理鍵值不存在的情況，並明確檢查 NSNull
        debug_log(f"load_preferences: Attempting to read key '{CONTROLS_PANEL_VISIBLE_KEY}'")
        saved_controls_visible = Glyphs.defaults.get(CONTROLS_PANEL_VISIBLE_KEY)
        debug_log(f"load_preferences: Raw value for '{CONTROLS_PANEL_VISIBLE_KEY}' from Glyphs.defaults = {saved_controls_visible} (type: {type(saved_controls_visible)})")

        default_controls_visible = False # 預設為關閉

        if saved_controls_visible is None or isinstance(saved_controls_visible, objc.lookUpClass("NSNull")):
            plugin.controlsPanelVisible = default_controls_visible
            debug_log(f"load_preferences: '{CONTROLS_PANEL_VISIBLE_KEY}' set to default: {plugin.controlsPanelVisible} (reason: None or NSNull)")
        elif isinstance(saved_controls_visible, (int, bool)): # int for 0/1 from NSUserDefaults
            plugin.controlsPanelVisible = bool(saved_controls_visible)
            debug_log(f"load_preferences: '{CONTROLS_PANEL_VISIBLE_KEY}' set to: {plugin.controlsPanelVisible} (reason: int or bool, raw value was {saved_controls_visible})")
        else:
            # 處理非預期類型，使用預設值並記錄錯誤
            plugin.controlsPanelVisible = default_controls_visible
            error_log(f"'{CONTROLS_PANEL_VISIBLE_KEY}' has unexpected type: {type(saved_controls_visible)}. Using default: {default_controls_visible}")
            debug_log(f"load_preferences: '{CONTROLS_PANEL_VISIBLE_KEY}' set to default: {plugin.controlsPanelVisible} (reason: unexpected type)")

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
                    # 舊格式相容 - 直接是字典
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
                    # 舊格式相容 - 直接是字典
                    for position_str, char_or_name in previous_locked_chars_json.items():
                        try:
                            position = int(position_str)
                            plugin.previousLockedChars[position] = char_or_name
                        except:
                            debug_log(f"警告: 忽略非整數位置 '{position_str}'")
            except Exception as e:
                error_log(f"解析 previousLockedChars JSON 時出錯: {e}")
        
        plugin.isInClearMode = Glyphs.defaults[LOCK_MODE_KEY] or False
        
        # 額外除錯：記錄所有載入的屬性
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
        
        # 處理 currentArrangement - 將 None 轉換為空字串
        current_arrangement = getattr(plugin, 'currentArrangement', [])
        safe_current_arrangement = [item if item is not None else "" for item in current_arrangement]
        Glyphs.defaults[CURRENT_ARRANGEMENT_KEY] = safe_current_arrangement
        
        # 處理 originalArrangement - 將 None 轉換為空字串
        original_arrangement = getattr(plugin, 'originalArrangement', [])
        safe_original_arrangement = [item if item is not None else "" for item in original_arrangement]
        Glyphs.defaults[ORIGINAL_ARRANGEMENT_KEY] = safe_original_arrangement
        
        # 處理 finalArrangement - 將 None 轉換為空字串
        final_arrangement = getattr(plugin, 'finalArrangement', [])
        safe_final_arrangement = [item if item is not None else "" for item in final_arrangement]
        Glyphs.defaults[FINAL_ARRANGEMENT_KEY] = safe_final_arrangement
        Glyphs.defaults[ZOOM_FACTOR_KEY] = plugin.zoomFactor
        Glyphs.defaults[WINDOW_SIZE_KEY] = plugin.windowSize
        
        # 處理視窗位置 - 統一使用 list 格式
        if plugin.windowPosition:
            try:
                # 確保儲存的是 Python list of floats
                pos_list = [float(plugin.windowPosition[0]), float(plugin.windowPosition[1])]
                Glyphs.defaults[WINDOW_POSITION_KEY] = pos_list
                debug_log(f"已儲存視窗位置 (from plugin.windowPosition)：{pos_list}")
            except (TypeError, IndexError, ValueError) as e:
                error_log(f"儲存 plugin.windowPosition 錯誤, value: {plugin.windowPosition}, error: {e}")
                Glyphs.defaults[WINDOW_POSITION_KEY] = None # 儲存無效值時清除
        else:
            Glyphs.defaults[WINDOW_POSITION_KEY] = None # 如果 plugin.windowPosition 是 None，則儲存 None
            debug_log(f"plugin.windowPosition is None, setting preference to None.")
            
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
    """從快取或字型取得字符
    
    Args:
        font: GSFont 字型物件
        char_or_name: 字符或字符名稱
        
    Returns:
        GSGlyph 物件或 None
    """
    if not font or not char_or_name:
        return None
    
    # 使用官方 API 的安全快取機制
    # 優先使用 font.tempData 進行快取（官方推薦）
    cache_key = f"glyph_cache_{char_or_name}"
    
    # 檢查官方臨時快取
    if CACHE_ENABLED and hasattr(font, 'tempData') and cache_key in font.tempData:
        return font.tempData[cache_key]
    
    # 如果官方快取不可用，使用傳統快取
    fallback_cache_key = (id(font), char_or_name)
    if CACHE_ENABLED and fallback_cache_key in _glyph_cache:
        return _glyph_cache[fallback_cache_key]
    
    # 使用官方 API 查找字符
    glyph = _find_glyph_with_official_api(font, char_or_name)
    
    # 存入快取
    if glyph and CACHE_ENABLED:
        # 優先存入官方快取
        if hasattr(font, 'tempData'):
            font.tempData[cache_key] = glyph
        else:
            # 備用快取
            _glyph_cache[fallback_cache_key] = glyph
    
    return glyph


def _find_glyph_with_official_api(font, char_or_name):
    """使用官方 API 查找字符的內部函數
    
    Args:
        font: GSFont 字型物件
        char_or_name: 字符或字符名稱
        
    Returns:
        GSGlyph 物件或 None
    """
    if not font or not char_or_name:
        return None
    
    try:
        # 1. 使用官方推薦的字典訪問方式（最快速的方法）
        # 根據 GSFont API 文檔，這是查找字符的首選方法
        glyph = font.glyphs[char_or_name]
        if glyph:
            debug_log(f"透過字典訪問找到字符: {char_or_name}")
            return glyph
    except (KeyError, TypeError):
        # 正常的查找失敗，繼續嘗試其他方法
        pass
    except Exception as e:
        debug_log(f"字典訪問時發生未預期錯誤: {e}")
    
    # 2. 如果是單字符，嘗試 Unicode 十六進制查找
    if len(char_or_name) == 1:
        try:
            unicode_hex = format(ord(char_or_name), '04X')
            glyph = font.glyphs[unicode_hex]
            if glyph:
                debug_log(f"透過 Unicode 找到字符: {char_or_name} -> {unicode_hex}")
                return glyph
        except (KeyError, ValueError, TypeError):
            pass
        except Exception as e:
            debug_log(f"Unicode 查找時發生錯誤: {e}")
    
    # 3. 使用官方 glyphForName_ 方法（支援 Nice Names）
    try:
        if hasattr(font, 'glyphForName_'):
            glyph = font.glyphForName_(char_or_name)
            if glyph:
                debug_log(f"透過 glyphForName_ 找到字符: {char_or_name}")
                return glyph
    except Exception as e:
        debug_log(f"glyphForName_ 查找時發生錯誤: {e}")
    
    # 4. 嘗試 Unicode 字符值的其他格式
    if len(char_or_name) == 1:
        try:
            # 嘗試不同的 Unicode 格式
            unicode_variants = [
                format(ord(char_or_name), 'X'),      # 不補零的十六進制
                format(ord(char_or_name), '04x'),    # 小寫
                format(ord(char_or_name), '08X'),    # 8位數大寫
            ]
            
            for variant in unicode_variants:
                try:
                    glyph = font.glyphs[variant]
                    if glyph:
                        debug_log(f"透過 Unicode 變體找到字符: {char_or_name} -> {variant}")
                        return glyph
                except:
                    continue
        except Exception as e:
            debug_log(f"Unicode 變體查找時發生錯誤: {e}")
    
    # 未找到字符
    debug_log(f"無法找到字符: {char_or_name}")
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

def generate_arrangement(source_chars, locked_map, total_slots=8):
    """
    生成考慮到鎖定字符的最終字符排列。
    
    Args:
        source_chars: 用於填充未鎖定位置的可用字符列表（通常來自搜尋框）。
        locked_map: 一個字典，鍵是位置索引 (0-7)，值是鎖定的字符。
        total_slots: 排列中的總位置數量（預設為 8）。
        
    Returns:
        一個包含 total_slots 個字符的列表，代表最終的排列。
    """
    import random
    
    final_arrangement = [None] * total_slots
    unlocked_indices = []
    current_locked_map = locked_map or {}

    # 1. 填入鎖定的字符並找出未鎖定的索引
    for i in range(total_slots):
        if i in current_locked_map:
            final_arrangement[i] = current_locked_map[i]
        else:
            unlocked_indices.append(i)
            
    num_unlocked_to_fill = len(unlocked_indices)
    
    # 2. 為未鎖定的位置準備填充字符
    chars_for_filling_unlocked = []
    if num_unlocked_to_fill > 0:
        # 調用者 (event_handlers.py) 應確保 source_chars 在需要填充時至少包含一個字符
        # (例如，如果搜尋框為空，則使用目前編輯的字符)。
        if source_chars:
            unique_source_chars = list(dict.fromkeys(source_chars))

            if len(unique_source_chars) >= num_unlocked_to_fill:
                # 如果唯一字符足夠，則從中隨機選取不重複的字符。
                chars_for_filling_unlocked = random.sample(unique_source_chars, num_unlocked_to_fill)
            else:
                # 唯一字符不足，先全部選入，再從原始列表（允許重複）中補充。
                chars_for_filling_unlocked = list(unique_source_chars) # 複製
                
                num_still_to_fill_with_duplicates = num_unlocked_to_fill - len(chars_for_filling_unlocked)
                
                for _ in range(num_still_to_fill_with_duplicates):
                    chars_for_filling_unlocked.append(random.choice(source_chars))
            
            random.shuffle(chars_for_filling_unlocked) # 打亂將用於填充的字符順序
        else:
            # 如果 source_chars 為空但仍有未鎖定位置需要填充，
            # 這裡可以留空（None），依賴預覽畫面的後備邏輯，
            # 或者使用一個預設字符。目前行為是留空。
            debug_log("警告: source_chars 為空，但有未鎖定的位置需要填充。")

    # 3. 將準備好的字符填入未鎖定的位置
    fill_iter = iter(chars_for_filling_unlocked)
    for index_to_fill in unlocked_indices:
        try:
            final_arrangement[index_to_fill] = next(fill_iter)
        except StopIteration:
            # 如果 chars_for_filling_unlocked 比未鎖定位置少（例如 source_chars 為空時），
            # 則剩餘的未鎖定位置將保持為 None。
            break 
            
    return final_arrangement

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
            if pos < 0 or pos >= FULL_ARRANGEMENT_SIZE:
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

# === 排列格式轉換 ===

def _convert_arrangement_to_9_slots(arrangement):
    """將排列轉換為9格格式
    
    Args:
        arrangement: 原始排列（可能是8格或9格）
        
    Returns:
        9格排列列表
    """
    if not arrangement:
        return [None] * FULL_ARRANGEMENT_SIZE
    
    arrangement_list = list(arrangement)  # 確保是可變列表
    
    # 將空字串轉換回 None（從偏好設定載入時）
    arrangement_list = [item if item != "" else None for item in arrangement_list]
    
    if len(arrangement_list) == LEGACY_ARRANGEMENT_SIZE:
        # 8格轉9格：在位置4插入None作為中心格
        debug_log(f"轉換8格排列為9格: {arrangement_list}")
        new_arrangement = [None] * FULL_ARRANGEMENT_SIZE
        
        # 位置映射：0,1,2,3 -> 0,1,2,3，4,5,6,7 -> 5,6,7,8
        for i in range(4):
            new_arrangement[i] = arrangement_list[i]
        # 位置4保持為None（中心格）
        for i in range(4, 8):
            new_arrangement[i + 1] = arrangement_list[i]
            
        debug_log(f"轉換結果: {new_arrangement}")
        return new_arrangement
        
    elif len(arrangement_list) == FULL_ARRANGEMENT_SIZE:
        # 已經是9格，直接返回
        return arrangement_list
        
    else:
        # 其他長度，返回空的9格排列
        debug_log(f"無法識別的排列長度: {len(arrangement_list)}，返回空排列")
        return [None] * FULL_ARRANGEMENT_SIZE

def generate_non_repeating_batch(batch_chars, num_slots):
    """
    根據 batch_chars 和 num_slots 產生一個排列，符合：
    - 多於 num_slots：隨機抽取 num_slots 個不重複字元
    - 等於 num_slots：隨機排列
    - 少於 num_slots：每個字元至少出現一次，剩下的隨機補齊
    Args:
        batch_chars: 有效字元列表
        num_slots: 欲產生的排列長度
    Returns:
        一個長度為 num_slots 的字元列表
    """
    import random
    chars = list(batch_chars)
    if not chars or num_slots <= 0:
        return []
    if len(chars) >= num_slots:
        arrangement = random.sample(chars, num_slots)
    else:
        arrangement = chars.copy()
        while len(arrangement) < num_slots:
            arrangement.append(random.choice(chars))
        random.shuffle(arrangement)
    return arrangement
