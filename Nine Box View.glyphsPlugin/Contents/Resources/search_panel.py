# encoding: utf-8
"""
九宮格預覽外掛 - 簡化版多行搜尋面板模組
Nine Box Preview Plugin - Simplified Multiline Search Panel Module
"""

from __future__ import division, print_function, unicode_literals
import traceback
import objc
from GlyphsApp import Glyphs
from AppKit import (
    NSView, NSTextView, NSScrollView, NSFont, NSColor, NSApp,
    NSMenu, NSMenuItem, NSNotificationCenter,
    NSViewWidthSizable, NSViewHeightSizable,
    NSMakeRect, NSFocusRingTypeDefault
)
from Foundation import NSObject

from constants import DEBUG_MODE
from utils import debug_log, error_log


class SearchTextView(NSTextView):
    """簡化版多行文字檢視，移除複雜的邊距修正"""
    
    def initWithFrame_plugin_(self, frame, plugin):
        """初始化多行文字檢視 - 使用系統預設設定"""
        self = objc.super(SearchTextView, self).initWithFrame_(frame)
        if self:
            self.plugin = plugin
            self._programmatic_update = False  # 標記是否為程式化更新
            self._setup_basic_properties()
            self._setup_context_menu()
            self._register_notifications()
        return self
    
    def _setup_basic_properties(self):
        """設定基本屬性 - 使用系統預設，最小化手動調整"""
        try:
            # 基本編輯屬性
            self.setEditable_(True)
            self.setSelectable_(True)
            self.setRichText_(False)  # 純文字模式
            self.setImportsGraphics_(False)
            self.setAllowsUndo_(True)
            
            # 字型設定
            self.setFont_(NSFont.systemFontOfSize_(14.0))
            
            # 文字容器設定 - 使用簡潔的方式
            textContainer = self.textContainer()
            if textContainer:
                # 允許文字換行，寬度跟隨檢視
                textContainer.setWidthTracksTextView_(True)
                textContainer.setHeightTracksTextView_(False)
                # 保持適度邊距以提高可讀性（不強制為零）
                textContainer.setLineFragmentPadding_(3.0)
            
            # 簡單的背景顏色設定
            self.setBackgroundColor_(NSColor.textBackgroundColor())
            
            # 設定提示文字
            searchTooltip = Glyphs.localize({
                'en': u'Enter multiple characters or Nice Names separated by spaces',
                'zh-Hant': u'輸入多個字符或以空格分隔的 Nice Names',
                'zh-Hans': u'输入多个字符或以空格分隔的 Nice Names',
                'ja': u'複数の文字またはスペースで区切られた Nice Names を入力',
                'ko': u'여러 문자 또는 공백으로 구분된 Nice Names 입력',
            })
            self.setToolTip_(searchTooltip)
            
        except Exception as e:
            error_log("設定基本屬性時發生錯誤", e)
    
    def _setup_context_menu(self):
        """設定右鍵選單"""
        try:
            contextMenu = NSMenu.alloc().init()
            
            # 標準編輯選單項目
            contextMenu.addItemWithTitle_action_keyEquivalent_("Cut", "cut:", "x")
            contextMenu.addItemWithTitle_action_keyEquivalent_("Copy", "copy:", "c") 
            contextMenu.addItemWithTitle_action_keyEquivalent_("Paste", "paste:", "v")
            contextMenu.addItem_(NSMenuItem.separatorItem())
            
            # 自訂字符選擇功能
            pickGlyphItem = NSMenuItem.alloc().initWithTitle_action_keyEquivalent_(
                Glyphs.localize({
                    'en': u'Glyph Picker...',
                    'zh-Hant': u'字符選擇器...',
                    'zh-Hans': u'字符选择器...',
                    'ja': u'グリフピッカー...',
                    'ko': u'글리프 선택기...',
                }),
                "pickGlyphAction:",
                ""
            )
            contextMenu.addItem_(pickGlyphItem)
            self.setMenu_(contextMenu)
            
        except Exception as e:
            error_log("設定右鍵選單錯誤", e)
    
    def _register_notifications(self):
        """註冊通知"""
        NSNotificationCenter.defaultCenter().addObserver_selector_name_object_(
            self,
            "textDidChange:",
            "NSTextDidChangeNotification",
            self
        )
    
    def pickGlyphAction_(self, sender):
        """選擇字符功能"""
        debug_log("選擇字符選單被點擊")
        if hasattr(self, 'plugin') and self.plugin:
            self.plugin.pickGlyphCallback(sender)
    
    def textDidChange_(self, notification):
        """文字變更時的回呼"""
        try:
            # 檢查是否為程式化更新，如果是則不觸發回調
            if self._programmatic_update:
                debug_log(f"搜尋欄位程式化更新: {self.string()}，跳過觸發排列重新生成")
                return
            
            # 保存當前游標位置
            current_selection = self.selectedRange()
            
            debug_log(f"搜尋欄位使用者輸入變更: {self.string()}")
            if hasattr(self, 'plugin') and self.plugin:
                self.plugin.searchFieldCallback(self)
                
            # 恢復游標位置
            self.setSelectedRange_(current_selection)
            
        except Exception as e:
            error_log("文字變更處理錯誤", e)
    
    def stringValue(self):
        """提供與 NSTextField 相容的 stringValue 方法"""
        return self.string()
    
    def setStringValue_(self, value):
        """提供與 NSTextField 相容的 setStringValue 方法"""
        try:
            # 保存當前游標位置
            current_selection = self.selectedRange()
            
            if value:
                self.setString_(value)
            else:
                self.setString_("")
                
            # 恢復游標位置
            self.setSelectedRange_(current_selection)
            
        except Exception as e:
            error_log("設定文字值時發生錯誤", e)
    
    def dealloc(self):
        """解構式"""
        NSNotificationCenter.defaultCenter().removeObserver_(self)
        objc.super(SearchTextView, self).dealloc()


class SearchPanel(NSView):
    """簡化版搜尋面板 - 保持多行功能但移除複雜修正"""
    
    def initWithFrame_plugin_(self, frame, plugin):
        """初始化搜尋面板"""
        self = objc.super(SearchPanel, self).initWithFrame_(frame)
        if self:
            self.plugin = plugin
            self.searchField = None
            self.scrollView = None
            self.setAutoresizingMask_(NSViewWidthSizable | NSViewHeightSizable)
            self._setup_ui()
        return self
    
    def _setup_ui(self):
        """設定介面 - 簡化版本，使用系統標準設定"""
        bounds = self.bounds()
        margin = 8  # 適度邊距
        
        # 建立 NSScrollView - 使用系統預設設定
        scrollRect = NSMakeRect(margin, margin, 
                              bounds.size.width - 2 * margin, 
                              bounds.size.height - 2 * margin)
        
        self.scrollView = NSScrollView.alloc().initWithFrame_(scrollRect)
        self.scrollView.setAutoresizingMask_(NSViewWidthSizable | NSViewHeightSizable)
        
        # 基本滾動視圖設定 - 使用系統標準
        self.scrollView.setBorderType_(1)  # NSBezelBorder - 標準邊框
        self.scrollView.setHasVerticalScroller_(True)
        self.scrollView.setHasHorizontalScroller_(False)
        self.scrollView.setAutohidesScrollers_(True)  # 系統預設：自動隱藏滾動條
        
        # 聚焦效果
        self.scrollView.setFocusRingType_(NSFocusRingTypeDefault)
        
        # 建立文字檢視 - 使用內容區域大小
        contentSize = self.scrollView.contentSize()
        textViewFrame = NSMakeRect(0, 0, contentSize.width, contentSize.height)
        
        self.searchField = SearchTextView.alloc().initWithFrame_plugin_(
            textViewFrame, self.plugin)
        
        # 設定文字檢視的自動調整
        self.searchField.setAutoresizingMask_(NSViewWidthSizable | NSViewHeightSizable)
        
        # 文字檢視的垂直調整設定
        self.searchField.setVerticallyResizable_(True)
        self.searchField.setHorizontallyResizable_(False)
        
        # 設定尺寸範圍
        self.searchField.setMinSize_(NSMakeRect(0, 0, 0, 0).size)
        self.searchField.setMaxSize_(NSMakeRect(0, 0, 1000000, 1000000).size)
        
        # 文字容器設定
        if self.searchField.textContainer():
            self.searchField.textContainer().setContainerSize_(
                NSMakeRect(0, 0, contentSize.width, 1000000).size)
        
        # 將文字檢視設為滾動視圖的文檔檢視
        self.scrollView.setDocumentView_(self.searchField)
        
        # 添加到當前檢視
        self.addSubview_(self.scrollView)
        
        debug_log("搜尋面板 UI 設定完成（簡化多行版）")
    
    def update_content(self, plugin_state):
        """更新搜尋欄位內容（程式化更新）"""
        try:
            if hasattr(plugin_state, 'lastInput') and self.searchField:
                input_value = plugin_state.lastInput or ""
                
                # 設定程式化更新標記，避免觸發重新生成排列
                self.searchField._programmatic_update = True
                debug_log(f"程式化更新搜尋欄位內容: '{input_value}'")
                
                try:
                    self.searchField.setStringValue_(input_value)
                finally:
                    # 確保標記被清除
                    self.searchField._programmatic_update = False
                    debug_log("程式化更新完成，已清除標記")
                    
        except Exception as e:
            error_log("更新搜尋欄位內容錯誤", e)
            # 發生錯誤時也要確保清除標記
            if hasattr(self, 'searchField') and self.searchField:
                self.searchField._programmatic_update = False
    
    def get_search_value(self):
        """取得搜尋欄位的值"""
        if self.searchField:
            return self.searchField.stringValue()
        return ""
    
    def set_search_value(self, value):
        """設定搜尋欄位的值（程式化更新）"""
        if self.searchField:
            # 設定程式化更新標記，避免觸發重新生成排列
            self.searchField._programmatic_update = True
            debug_log(f"程式化設定搜尋欄位值: '{value}'")
            
            try:
                self.searchField.setStringValue_(value)
            finally:
                # 確保標記被清除
                self.searchField._programmatic_update = False
                debug_log("程式化設定完成，已清除標記")
    
    def dealloc(self):
        """解構式"""
        objc.super(SearchPanel, self).dealloc()
