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
        default_width = float(current_master.customParameters['Default Layer Width'])
        if default_width > 0:
            return default_width

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
        - 漢字/東亞文字：直接連續處理，不需空格分隔
        - ASCII 字符/字符名稱：需要用空格分隔
        - 混合輸入時，保持上述規則
    
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
    # 移除連續的多餘空格，但保留有意義的單個空格
    parts = ' '.join(text.split())
    parts = parts.split(' ')

    for part in parts:
        if not part:
            continue

        # 檢查是否包含漢字/東亞文字
        if any(ord(c) > 0x4E00 for c in part):
            # 對於漢字，逐字符處理
            for char in part:
                if font.glyphs[char]:
                    chars.append(char)
        else:
            # 對於 ASCII 字符名稱，整體處理
            if font.glyphs[part]:
                chars.append(part)

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