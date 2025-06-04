# encoding: utf-8
"""
九宮格預覽外掛 - 搜尋面板模組
Nine Box Preview Plugin - Search Panel Module
"""

from __future__ import division, print_function, unicode_literals
import traceback
import objc
from GlyphsApp import Glyphs
from AppKit import (
    NSView, NSTextField, NSFont, NSColor, NSApp,
    NSMenu, NSMenuItem, NSNotificationCenter,
    NSViewWidthSizable, NSViewHeightSizable,
    NSMakeRect, NSFocusRingTypeNone
)
from Foundation import NSObject

from constants import DEBUG_MODE
from utils import debug_log


class SearchTextField(NSTextField):
    """支援右鍵選單的搜尋文本框"""
    
    def initWithFrame_plugin_(self, frame, plugin):
        """初始化搜尋文本框"""
        self = objc.super(SearchTextField, self).initWithFrame_(frame)
        if self:
            self.plugin = plugin
            self._setup_appearance()
            self._setup_context_menu()
            self._register_notifications()
        return self
    
    def _setup_appearance(self):
        """設定外觀"""
        self.setFont_(NSFont.systemFontOfSize_(16.0))
        self.setFocusRingType_(NSFocusRingTypeNone)
        self.setBezeled_(True)
        self.setEditable_(True)
        
        # 設定符合 macOS 標準的背景顏色
        isDarkMode = NSApp.effectiveAppearance().name().containsString_("Dark")
        if isDarkMode:
            self.setBackgroundColor_(NSColor.textBackgroundColor())
        else:
            self.setBackgroundColor_(NSColor.whiteColor())
        
        # 設定提示文字
        searchPlaceholder = Glyphs.localize({
            'en': u'Enter characters or Nice Names...',
            'zh-Hant': u'輸入字符或 Nice Names...',
            'zh-Hans': u'输入字符或 Nice Names...',
            'ja': u'文字または Nice Names を入力...',
            'ko': u'문자 또는 Nice Names 입력...',
        })
        self.setPlaceholderString_(searchPlaceholder)
        
        # 設定提示
        searchTooltip = Glyphs.localize({
            'en': u'Enter multiple characters or Nice Names separated by spaces',
            'zh-Hant': u'輸入多個字符或以空格分隔的 Nice Names',
            'zh-Hans': u'输入多个字符或以空格分隔的 Nice Names',
            'ja': u'複数の文字またはスペースで区切られた Nice Names を入力',
            'ko': u'여러 문자 또는 공백으로 구분된 Nice Names 입력',
        })
        self.setToolTip_(searchTooltip)
    
    def _setup_context_menu(self):
        """設定右鍵選單"""
        try:
            contextMenu = NSMenu.alloc().init()
            
            pickGlyphItem = NSMenuItem.alloc().initWithTitle_action_keyEquivalent_(
                Glyphs.localize({
                    'en': u'Select Glyphs from Font...',
                    'zh-Hant': u'從字型中選擇字符...',
                    'zh-Hans': u'从字体中选择字符...',
                    'ja': u'フォントから文字を選択...',
                    'ko': u'글꼴에서 글자 선택...',
                }),
                "pickGlyphAction:",
                ""
            )
            contextMenu.addItem_(pickGlyphItem)
            self.setMenu_(contextMenu)
            
        except Exception as e:
            debug_log(f"設定右鍵選單錯誤: {e}")
    
    def _register_notifications(self):
        """註冊通知"""
        NSNotificationCenter.defaultCenter().addObserver_selector_name_object_(
            self,
            "textDidChange:",
            "NSControlTextDidChangeNotification",
            self
        )
    
    def pickGlyphAction_(self, sender):
        """選擇字符功能"""
        debug_log("選擇字符選單被點擊")
        # 功能暫未實現
        # if hasattr(self, 'plugin') and self.plugin:
        #     self.plugin.pickGlyphCallback(sender)
    
    def textDidChange_(self, notification):
        """文本變更時的回調"""
        try:
            debug_log(f"搜尋欄位文本變更: {self.stringValue()}")
            if hasattr(self, 'plugin') and self.plugin:
                self.plugin.searchFieldCallback(self)
        except Exception as e:
            debug_log(f"文本變更處理錯誤: {e}")
    
    def dealloc(self):
        """析構函數"""
        NSNotificationCenter.defaultCenter().removeObserver_(self)
        objc.super(SearchTextField, self).dealloc()


class SearchPanel(NSView):
    """搜尋面板視圖"""
    
    def initWithFrame_plugin_(self, frame, plugin):
        """初始化搜尋面板"""
        self = objc.super(SearchPanel, self).initWithFrame_(frame)
        if self:
            self.plugin = plugin
            self.searchField = None
            self.setAutoresizingMask_(NSViewWidthSizable | NSViewHeightSizable)
            self._setup_ui()
        return self
    
    def _setup_ui(self):
        """設定介面"""
        bounds = self.bounds()
        
        # 創建搜尋欄位（填滿整個面板）
        searchRect = NSMakeRect(0, 0, bounds.size.width, bounds.size.height)
        self.searchField = SearchTextField.alloc().initWithFrame_plugin_(searchRect, self.plugin)
        self.searchField.setAutoresizingMask_(NSViewWidthSizable | NSViewHeightSizable)
        
        self.addSubview_(self.searchField)
    
    def update_content(self, plugin_state):
        """更新搜尋欄位內容"""
        try:
            if hasattr(plugin_state, 'lastInput') and self.searchField:
                input_value = plugin_state.lastInput or ""
                self.searchField.setStringValue_(input_value)
        except Exception as e:
            debug_log(f"更新搜尋欄位內容錯誤: {e}")
    
    def get_search_value(self):
        """取得搜尋欄位的值"""
        if self.searchField:
            return self.searchField.stringValue()
        return ""
    
    def set_search_value(self, value):
        """設定搜尋欄位的值"""
        if self.searchField:
            self.searchField.setStringValue_(value)
    
    def dealloc(self):
        """析構函數"""
        objc.super(SearchPanel, self).dealloc()
