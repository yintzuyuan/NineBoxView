# encoding: utf-8
"""
九宮格預覽外掛 - 工具函數
Nine Box Preview Plugin - Utility Functions
"""

from __future__ import division, print_function, unicode_literals
import traceback
import random
import objc
from GlyphsApp import Glyphs

def log_to_macro_window(message):
    """
    將訊息記錄到巨集視窗
    Log message to the Macro Window
    
    Args:
        message: 要記錄的訊息內容
    """
    Glyphs.clearLog()
    print(message)

def get_base_width():
    """
    取得基準寬度
    Get the base width
    
    Returns:
        float: 基準寬度值
    """
    # 從常數模組中導入預設 UPM 值
    from constants import DEFAULT_UPM
    
    if not Glyphs.font:
        return DEFAULT_UPM

    current_master = Glyphs.font.selectedFontMaster

    # 1. 檢查主板是否有 Default Layer Width 參數
    default_width = None
    if current_master.customParameters['Default Layer Width']:
        try:
            param_value = current_master.customParameters['Default Layer Width']
            # 處理可能的格式如 'han: 950'
            if isinstance(param_value, str) and ':' in param_value:
                # 取冒號後的數值部分
                value_part = param_value.split(':', 1)[1].strip()
                default_width = float(value_part)
            else:
                default_width = float(param_value)
            
            if default_width > 0:
                return default_width
        except (ValueError, TypeError) as e:
            log_to_macro_window(f"無法解析預設圖層寬度參數: {e}")

    # 2. 使用選取的字符層寬度
    if Glyphs.font.selectedLayers:
        return Glyphs.font.selectedLayers[0].width

    # 3. 使用字型的 UPM (units per em) 值
    if hasattr(Glyphs.font, 'upm'):
        return max(Glyphs.font.upm, 500)

    # 4. 最後的預設值
    return DEFAULT_UPM

def parse_input_text(text, font=None):
    """
    解析輸入文字並返回有效的字符列表
    
    處理規則：
        - Nice Name：需要用空格分隔
        - 其他所有文字（包含漢字/東亞文字/ASCII字符）：直接連續處理，不需空格分隔
    
    Args:
        text: 要解析的文字
        font: 字型對象，預設使用 Glyphs.font
    
    Returns:
        list: 有效的字符名稱列表
    """
    # 使用提供的字型或預設的 Glyphs.font
    if font is None:
        font = Glyphs.font
    
    # 檢查是否有開啟字型檔案
    if not font:
        log_to_macro_window("警告：沒有開啟字型檔案")
        return []

    chars = []
    
    # 先檢查輸入文字中是否有 Nice Name (需要空格分隔的名稱)
    # 移除連續的多餘空格，但保留有意義的單個空格
    parts = ' '.join(text.split())
    parts = parts.split(' ')
    
    for part in parts:
        if not part:
            continue
            
        # 先檢查是否為 Nice Name (完整名稱)
        glyph = font.glyphs[part]
        if glyph and len(part) > 1:  # 只有當字符名稱長度>1時才視為 Nice Name
            # 檢查是否有 Unicode 值
            if glyph.unicode:
                # 如果有 Unicode，轉換為實際字符
                char = chr(int(glyph.unicode, 16))
                chars.append(char)
            else:
                # 對於沒有 Unicode 的字符（如 .notdef 或自定義字符），使用名稱
                chars.append(part)
        else:
            # 不是 Nice Name，按字符逐個處理
            for c in part:
                if c and font.glyphs[c]:
                    chars.append(c)
    
    return chars

def generate_arrangement(char_list, max_chars=8):
    """
    生成新的隨機排列
    Generate a new random arrangement
    
    Args:
        char_list: 字符列表
        max_chars: 最大字符數，預設為8
    
    Returns:
        list: 隨機排列後的字符列表
    """
    if not char_list:
        return []
        
    display_chars = list(char_list)  # 複製一份字符列表

    # 如果字符數量超過 max_chars 個，隨機選擇 max_chars 個
    if len(display_chars) > max_chars:
        display_chars = random.sample(display_chars, max_chars)
    elif display_chars:
        # 如果字符數量不足 max_chars 個，從現有字符中隨機選擇來填充
        while len(display_chars) < max_chars:
            display_chars.append(random.choice(display_chars))

    # 隨機打亂順序
    random.shuffle(display_chars)
    return display_chars 