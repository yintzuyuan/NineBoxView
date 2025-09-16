# encoding: utf-8

"""
主題偵測器 - 基於 Georg Seifert 的官方建議
實作條件性主題偵測：
- Edit View + 有字型：使用 tab 層級偵測
- Font View 或無字型：使用系統明暗模式
"""

from __future__ import division, print_function, unicode_literals
import traceback

try:
    from GlyphsApp import Glyphs
except Exception:
    # 測試環境或 Glyphs 未執行（包括 objc.nosuchclass_error: GSFont）
    Glyphs = None

try:
    from AppKit import NSApp, NSAppearanceNameAqua, NSAppearanceNameDarkAqua, NSKeyValueObservingOptionNew, NSKeyValueObservingOptionInitial
    from Foundation import NSObject
    import objc
except Exception:
    # 測試環境復原
    NSApp = None
    NSAppearanceNameAqua = "NSAppearanceNameAqua"
    NSAppearanceNameDarkAqua = "NSAppearanceNameDarkAqua"
    NSKeyValueObservingOptionNew = 1
    NSKeyValueObservingOptionInitial = 4
    NSObject = object
    objc = None

class ThemeDetector:
    """
    主題偵測器 - 基於官方開發者建議的多層級主題偵測
    
    依照 Georg Seifert 在論壇中提到的方法：
    1. Tab 層級：Font.currentTab.previewView().setBlack_()
    2. 復原至檔案層級：Glyphs.defaults["GSPreview_Black"]
    """
    
    def __init__(self):
        self._cached_result = None
        self._last_state = None
    
    def _ensure_environment(self, font=None):
        """統一環境和安全檢查"""
        if Glyphs is None:
            return None, "測試環境"
        
        current_font = font or Glyphs.font
        if not current_font:
            return None, "無字體"
        
        current_tab = getattr(current_font, 'currentTab', None)
        return current_font, current_tab
    
    def get_theme_is_black(self, font=None):
        """
        條件性主題偵測：
        - Edit View + 有字型：使用 tab 層級偵測（Georg Seifert 方法）  
        - Font View 或無字型：使用系統明暗模式（KVO）
        
        Args:
            font: 指定字體，如果為 None 則使用當前字體
        
        Returns:
            bool: True 如果是深色主題
        """
        if self._is_in_edit_view_with_font(font):
            # Edit View + 有字型檔案：使用現有的 tab 層級偵測
            return self._get_tab_level_theme(font)
        else:
            # Font View 或無字型檔案：使用系統明暗模式
            return self._get_system_theme_is_dark()
    
    def _is_in_edit_view_with_font(self, font=None):
        """
        檢查是否在 Edit View 且有字型檔案開啟

        基於 Georg Seifert 官方建議，Edit View 的核心特徵是 currentTab 的存在，
        而非 selectedLayers。未選擇字符時仍應使用 Tab 層級主題。
        """
        try:
            current_font = font or Glyphs.font if Glyphs else None

            # 條件1：必須有字型檔案開啟
            if not current_font:
                return False

            # 條件2：必須有當前 Tab（Edit View 的核心特徵）
            # 有 currentTab 即表示在 Edit View，無論是否有字符選擇
            if not hasattr(current_font, 'currentTab') or not current_font.currentTab:
                return False

            # Edit View 判斷完成：有字體且有 currentTab 即為 Edit View
            # 移除 selectedLayers 檢查：即使無字符選擇也應使用 Tab 層級主題
            return True
        except Exception:
            return False
    
    def _get_tab_level_theme(self, font=None):
        """Tab 層級主題偵測（保持現有邏輯）"""
        current_font, current_tab = self._ensure_environment(font)
        if current_font is None:
            return False if current_tab == "測試環境" else self._get_global_theme_setting()
        
        # 檢查快取
        current_state = (current_font, current_tab)
        if self._cached_result is not None and self._last_state == current_state:
            return self._cached_result
        
        # Tab 層級偵測優先
        is_black = self._detect_tab_theme(current_tab) if current_tab else None
        if is_black is None:
            is_black = self._get_global_theme_setting()
        
        # 更新快取
        self._cached_result = is_black
        self._last_state = current_state
        return is_black
    
    def _detect_tab_theme(self, current_tab):
        """
        Tab 層級主題偵測（Georg Seifert 建議的方法）
        
        Args:
            current_tab: Tab 物件
            
        Returns:
            bool or None: True/False 如果偵測成功，None 如果無法偵測
        """
        try:
            if not current_tab or not hasattr(current_tab, 'previewView'):
                return None
            
            preview_view = current_tab.previewView()
            if not preview_view:
                return None
            
            # 統一的黑色狀態偵測方法
            for method in ['black', 'isBlack']:
                if hasattr(preview_view, method):
                    return getattr(preview_view, method)()
            
            # 復原至背景顏色判斷
            if hasattr(preview_view, 'backgroundColor'):
                bg_color = preview_view.backgroundColor()
                if bg_color:
                    return all(getattr(bg_color, f'{c}Component')() < 0.5 
                              for c in ['red', 'green', 'blue'])
            
            return None
            
        except Exception:
            print(traceback.format_exc())
            return None
    
    def _get_global_theme_setting(self):
        """全域檔案層級主題偵測（復原方法）"""
        try:
            return Glyphs.defaults.get("GSPreview_Black", False) if Glyphs else False
        except Exception:
            print(traceback.format_exc())
            return False
    
    def _get_system_theme_is_dark(self):
        """系統明暗模式偵測（KVO 方法）"""
        try:
            if not NSApp:
                return False
                
            appearance = NSApp.effectiveAppearance()
            if not appearance or not hasattr(appearance, 'bestMatchFromAppearancesWithNames_'):
                # 復原方法：檢查外觀名稱
                appearance_name = str(appearance.name()) if hasattr(appearance, 'name') else ""
                return "Dark" in appearance_name
            
            # 使用官方推薦的 bestMatch 方法
            best_match = appearance.bestMatchFromAppearancesWithNames_([
                NSAppearanceNameAqua, 
                NSAppearanceNameDarkAqua
            ])
            return best_match == NSAppearanceNameDarkAqua
            
        except Exception:
            print(traceback.format_exc())
            return False
    
    def clear_cache(self):
        """清除主題快取"""
        self._cached_result = None
        self._last_state = None
    
    def set_tab_theme(self, is_black, font=None):
        """
        設定 tab 層級主題（Georg Seifert 建議的方法）
        
        Args:
            is_black: True 設為深色主題，False 設為淺色主題
            font: 指定字體，如果為 None 則使用當前字體
            
        Returns:
            bool: True 如果設定成功
        """
        try:
            current_font, current_tab = self._ensure_environment(font)
            if not current_font or not current_tab:
                return False
            
            preview_view = current_tab.previewView() if hasattr(current_tab, 'previewView') else None
            if not preview_view or not hasattr(preview_view, 'setBlack_'):
                return False
            
            preview_view.setBlack_(is_black)
            self.clear_cache()
            return True
            
        except Exception:
            print(traceback.format_exc())
            return False


# 全域實例
_detector = None

def theme_api(action, **kwargs):
    """
    統一的主題 API 介面
    
    Args:
        action: 'get' | 'set' | 'clear'
        **kwargs: 相應參數
        
    Returns:
        根據 action 的結果
    """
    global _detector
    if _detector is None:
        _detector = ThemeDetector()
    
    if action == 'get':
        return _detector.get_theme_is_black(kwargs.get('font'))
    elif action == 'set':
        return _detector.set_tab_theme(kwargs.get('is_black'), kwargs.get('font'))
    elif action == 'clear':
        return _detector.clear_cache()
    else:
        raise ValueError(f"不支援的操作: {action}")

# 直接函數為了相容性（不新增別名）  
get_current_theme_is_black = lambda font=None: theme_api('get', font=font)
clear_theme_cache = lambda: theme_api('clear')
set_current_tab_theme = lambda is_black, font=None: theme_api('set', is_black=is_black, font=font)


class SystemThemeMonitor(NSObject):
    """系統主題監聽器（KVO 實作）"""
    
    def init(self):
        """初始化監聽器"""
        if objc:
            # 使用 objc.super() 正確初始化 Objective-C 物件
            self = objc.super(SystemThemeMonitor, self).init()
        else:
            # 測試環境復原
            self = self.__class__.__bases__[0].__init__(self)
            
        if self:
            self._theme_change_callbacks = []
            self._setup_kvo_monitoring()
        return self
    
    def _setup_kvo_monitoring(self):
        """設定 KVO 監聽系統主題變化"""
        try:
            if NSApp:
                NSApp.addObserver_forKeyPath_options_context_(
                    self, 
                    "effectiveAppearance",
                    NSKeyValueObservingOptionNew | NSKeyValueObservingOptionInitial,
                    None
                )
        except Exception:
            print(traceback.format_exc())
    
    def observeValueForKeyPath_ofObject_change_context_(self, keyPath, observed_object, change, context):
        """KVO 回呼：系統主題變更時觸發"""
        try:
            # 標記未使用的參數（KVO 回呼必須有這些參數）
            _ = observed_object, change, context

            if keyPath == "effectiveAppearance":
                # 清除主題偵測器快取
                clear_theme_cache()

                # 通知所有註冊的回呼函數
                for callback in self._theme_change_callbacks:
                    try:
                        callback()
                    except Exception:
                        print(traceback.format_exc())
        except Exception:
            print(traceback.format_exc())
    
    def add_theme_change_callback(self, callback):
        """新增主題變更回呼函數"""
        if callback not in self._theme_change_callbacks:
            self._theme_change_callbacks.append(callback)
    
    def remove_theme_change_callback(self, callback):
        """移除主題變更回呼函數"""
        if callback in self._theme_change_callbacks:
            self._theme_change_callbacks.remove(callback)
    
    def cleanup(self):
        """清理 KVO 監聽"""
        try:
            if NSApp:
                NSApp.removeObserver_forKeyPath_(self, "effectiveAppearance")
        except Exception:
            print(traceback.format_exc())


# 全域系統主題監聽器實例
_system_theme_monitor = None

def get_system_theme_monitor():
    """取得全域系統主題監聽器實例"""
    global _system_theme_monitor
    if _system_theme_monitor is None:
        _system_theme_monitor = SystemThemeMonitor.alloc().init()
    return _system_theme_monitor

def cleanup_system_theme_monitor():
    """清理系統主題監聽器"""
    global _system_theme_monitor
    if _system_theme_monitor is not None:
        _system_theme_monitor.cleanup()
        _system_theme_monitor = None