# encoding: utf-8

"""
九宮格預覽外掛 - 核心工具函數
包含字體管理、等寬字體支援等工具函數
"""

from __future__ import division, print_function, unicode_literals
import traceback

# 字體相關常數
MONOSPACE_FONT_NAMES = ["Menlo", "Monaco", "Consolas", "SF Mono", "Courier New"]
SEARCH_INPUT_FONT_SIZE = 14.0
SEARCH_INPUT_LINE_SPACING = 0
LOCK_FIELD_MONOSPACE_FONT_SIZE = 16.0
FONT_FALLBACK_ENABLED = True
DEFAULT_SYSTEM_FONT_SIZE = 13.0

# 搜尋功能設定
SEARCH_FUNCTION_ENABLED = True
SEARCH_USE_FIND_BAR = True
SEARCH_USE_FIND_PANEL_FALLBACK = True


def get_monospace_font(size=14.0):
    """獲取等寬字體（基於 DrawBot 的實作）
    
    Args:
        size: 字體大小
        
    Returns:
        NSFont: 等寬字體物件，若無法獲取則返回系統等寬字體
    """
    try:
        from AppKit import NSFont, NSFontWeightRegular
        
        # 按照優先順序嘗試各種等寬字體（DrawBot 風格）
        for font_name in MONOSPACE_FONT_NAMES:
            font = NSFont.fontWithName_size_(font_name, size)
            if font:
                return font
        
        # 嘗試系統內建等寬字體 (macOS 10.15+)
        try:
            font = NSFont.monospacedSystemFontOfSize_weight_(size, NSFontWeightRegular)
            if font:
                return font
        except AttributeError:
            pass  # 舊版系統不支援此 API
        
        # 復原到系統預設字體
        if FONT_FALLBACK_ENABLED:
            fallback_font = NSFont.systemFontOfSize_(DEFAULT_SYSTEM_FONT_SIZE)
            return fallback_font
            
        return None
        
    except Exception:
        print(traceback.format_exc())
        return None


class FontManager:
    """字體管理工具類別"""
    
    _font_cache = {}  # 字體快取
    
    @classmethod
    def get_monospace_font_for_search(cls, size=None):
        """為搜尋輸入框獲取等寬字體"""
        try:
            font_size = size if size is not None else SEARCH_INPUT_FONT_SIZE
            cache_key = f"search_{font_size}"
            
            # 檢查快取
            if cache_key in cls._font_cache:
                return cls._font_cache[cache_key]
            
            # 獲取字體並快取
            font = get_monospace_font(font_size)
            if font:
                cls._font_cache[cache_key] = font
            
            return font
            
        except Exception:
            print(traceback.format_exc())
            return None
    
    @classmethod
    def get_monospace_font_for_lock_field(cls, size=None):
        """為鎖定輸入框獲取等寬字體"""
        try:
            font_size = size if size is not None else LOCK_FIELD_MONOSPACE_FONT_SIZE
            cache_key = f"lock_{font_size}"
            
            # 檢查快取
            if cache_key in cls._font_cache:
                return cls._font_cache[cache_key]
            
            # 獲取字體並快取
            font = get_monospace_font(font_size)
            if font:
                cls._font_cache[cache_key] = font
            
            return font
            
        except Exception:
            print(traceback.format_exc())
            return None
    
    @classmethod
    def get_font_attributes_for_search(cls, font=None):
        """獲取搜尋輸入框的字體屬性字典"""
        try:
            from AppKit import NSFontAttributeName, NSParagraphStyleAttributeName, NSMutableParagraphStyle
            
            if not font:
                font = cls.get_monospace_font_for_search()
            
            if not font:
                return {}
            
            # 設定段落樣式
            paragraph_style = NSMutableParagraphStyle.alloc().init()
            paragraph_style.setLineSpacing_(SEARCH_INPUT_LINE_SPACING)
            
            attributes = {
                NSFontAttributeName: font,
                NSParagraphStyleAttributeName: paragraph_style
            }
            
            return attributes
            
        except Exception:
            print(traceback.format_exc())
            return {}
    
    @classmethod
    def getCurrentFontContext(cls):
        """統一的字型上下文獲取（官方模式，遵循 Glyphs 命名慣例）
        
        統一的字型上下文工具，替代各模組中重複的 _getCurrentFontContext 方法
        
        Returns:
            tuple: (font, master) 元組，失敗時返回 (None, None)
        """
        try:
            from .glyphs_service import get_glyphs_service
            glyphs_service = get_glyphs_service()
            
            font = glyphs_service.get_current_font()
            if not font:
                return (None, None)
            
            master = font.selectedFontMaster
            if not master:
                return (None, None)
                
            return (font, master)
            
        except Exception:
            print(traceback.format_exc())
            return (None, None)
    
    @classmethod
    def clear_font_cache(cls):
        """清除字體快取"""
        cls._font_cache.clear()


def setup_text_view_for_monospace_search(text_view):
    """為 NSTextView 設定等寬字體和搜尋功能（基於 DrawBot 實作）
    
    Args:
        text_view: NSTextView 實例
        
    Returns:
        bool: 設定是否成功
    """
    try:
        if not text_view:
            return False
        
        # 設定等寬字體
        font = FontManager.get_monospace_font_for_search()
        if font:
            text_view.setFont_(font)
        
        # 啟用搜尋功能（參考 DrawBot CodeEditor 實作）
        if SEARCH_FUNCTION_ENABLED:
            try:
                if SEARCH_USE_FIND_BAR:
                    text_view.setUsesFindBar_(True)
                else:
                    raise AttributeError("跳過現代搜尋列")
            except (AttributeError, Exception):
                if SEARCH_USE_FIND_PANEL_FALLBACK:
                    try:
                        text_view.setUsesFindPanel_(True)
                    except (AttributeError, Exception):
                        print(traceback.format_exc())
        
        # 關閉自動功能以獲得更好的程式碼編輯體驗
        text_view.setAutomaticTextReplacementEnabled_(False)
        text_view.setAutomaticQuoteSubstitutionEnabled_(False)
        text_view.setAutomaticLinkDetectionEnabled_(False)
        text_view.setAutomaticDataDetectionEnabled_(False)
        text_view.setAutomaticDashSubstitutionEnabled_(False)
        text_view.setAutomaticSpellingCorrectionEnabled_(False)
        text_view.setContinuousSpellCheckingEnabled_(False)
        
        return True
        
    except Exception:
        print(traceback.format_exc())
        return False


def setup_text_field_for_monospace(text_field):
    """為 NSTextField 設定等寬字體
    
    Args:
        text_field: NSTextField 實例
        
    Returns:
        bool: 設定是否成功
    """
    try:
        if not text_field:
            return False
        
        # 設定等寬字體
        font = FontManager.get_monospace_font_for_lock_field()
        if font:
            text_field.setFont_(font)
            return True
            
        return False
        
    except Exception:
        print(traceback.format_exc())
        return False