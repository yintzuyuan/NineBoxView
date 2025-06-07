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
    NSView, NSTextView, NSScrollView, NSFont, NSColor, NSApp,
    NSMenu, NSMenuItem, NSNotificationCenter,
    NSViewWidthSizable, NSViewHeightSizable,
    NSMakeRect, NSFocusRingTypeNone, NSTextContainer,
    NSLayoutManager, NSTextStorage, NSBorderlessWindowMask
)
from Foundation import NSObject

from constants import DEBUG_MODE
from utils import debug_log, error_log


class SearchTextView(NSTextView):
    """支援右鍵選單的搜尋文字畫面"""
    
    def initWithFrame_plugin_(self, frame, plugin):
        """初始化搜尋文字畫面"""
        # 建立文字存放區和佈局管理器
        textStorage = NSTextStorage.alloc().init()
        layoutManager = NSLayoutManager.alloc().init()
        textStorage.addLayoutManager_(layoutManager)
        
        # 建立文字容器
        containerSize = NSMakeRect(0, 0, frame.size.width, 1000000.0).size
        textContainer = NSTextContainer.alloc().initWithContainerSize_(containerSize)
        textContainer.setWidthTracksTextView_(True)
        textContainer.setHeightTracksTextView_(False)  # 允許垂直增長
        layoutManager.addTextContainer_(textContainer)
        
        # 初始化 NSTextView
        self = objc.super(SearchTextView, self).initWithFrame_textContainer_(frame, textContainer)
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
        self.setEditable_(True)
        self.setSelectable_(True)
        self.setRichText_(False)  # 只允許純文字
        self.setImportsGraphics_(False)
        self.setAllowsUndo_(True)
        
        # 設定符合 macOS 標準的背景顏色
        isDarkMode = NSApp.effectiveAppearance().name().containsString_("Dark")
        if isDarkMode:
            self.setBackgroundColor_(NSColor.textBackgroundColor())
        else:
            self.setBackgroundColor_(NSColor.whiteColor())
        
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
            error_log("設定右鍵選單錯誤", e)
    
    def _register_notifications(self):
        """註冊通知"""
        NSNotificationCenter.defaultCenter().addObserver_selector_name_object_(
            self,
            "textDidChange:",
            "NSTextDidChangeNotification",
            self
        )
    

    def becomeFirstResponder(self):
        """當文字畫面成為焦點時"""
        result = objc.super(SearchTextView, self).becomeFirstResponder()
        return result
    
    def resignFirstResponder(self):
        """當文字畫面失去焦點時"""
        result = objc.super(SearchTextView, self).resignFirstResponder()
        return result
    

    def pickGlyphAction_(self, sender):
        """選擇字符功能"""
        debug_log("選擇字符選單被點擊")
        if hasattr(self, 'plugin') and self.plugin:
            self.plugin.pickGlyphCallback(sender)
    
    def textDidChange_(self, notification):
        """文字變更時的回呼，並保持游標位置"""
        try:
            debug_log(f"搜尋欄位文字變更: {self.string()}")
            # 儲存目前選擇範圍和游標位置
            selected_range = self.selectedRange()
            
            if hasattr(self, 'plugin') and self.plugin:
                self.plugin.searchFieldCallback(self)
            
            # 回呼完成後恢復游標位置
            if selected_range.location <= len(self.string()):
                self.setSelectedRange_(selected_range)
                
        except Exception as e:
            error_log("文字變更處理錯誤", e)
    
    def stringValue(self):
        """提供與 NSTextField 相容的 stringValue 方法"""
        return self.string()
    
    def setStringValue_(self, value):
        """提供與 NSTextField 相容的 setStringValue 方法，並保持游標位置"""
        try:
            # 儲存目前選擇範圍和游標位置
            selected_range = self.selectedRange()
            
            # 設定新的文字
            if value:
                self.setString_(value)
            else:
                self.setString_("")
            
            # 只有當游標位置在有效範圍內才恢復
            if selected_range.location <= len(self.string()):
                self.setSelectedRange_(selected_range)
            
        except Exception as e:
            error_log("設定文字值時發生錯誤", e)
            # 發生錯誤時，使用原始方法
            if value:
                self.setString_(value)
            else:
                self.setString_("")
    
    def dealloc(self):
        """解構式"""
        NSNotificationCenter.defaultCenter().removeObserver_(self)
        objc.super(SearchTextView, self).dealloc()


class SearchPanel(NSView):
    """搜尋面板畫面"""
    
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
        """設定介面"""
        bounds = self.bounds()
        
        # 建立滾動畫面
        self.scrollView = NSScrollView.alloc().initWithFrame_(bounds)
        self.scrollView.setAutoresizingMask_(NSViewWidthSizable | NSViewHeightSizable)
        self.scrollView.setBorderType_(1)  # NSBezelBorder
        self.scrollView.setHasVerticalScroller_(True)
        self.scrollView.setHasHorizontalScroller_(False)
        self.scrollView.setAutohidesScrollers_(True)
        
        # 建立搜尋文字畫面
        contentSize = self.scrollView.contentSize()
        textViewFrame = NSMakeRect(0, 0, contentSize.width, contentSize.height)
        self.searchField = SearchTextView.alloc().initWithFrame_plugin_(textViewFrame, self.plugin)
        # 設定文字畫面可以垂直調整大小
        self.searchField.setMinSize_(NSMakeRect(0, 0, 0, 0).size)
        self.searchField.setMaxSize_(NSMakeRect(0, 0, 10000000, 10000000).size)
        self.searchField.setVerticallyResizable_(True)
        self.searchField.setHorizontallyResizable_(True)
        self.searchField.setAutoresizingMask_(NSViewWidthSizable)
        
        # 設定文字容器
        self.searchField.textContainer().setContainerSize_(NSMakeRect(0, 0, contentSize.width, 10000000).size)
        self.searchField.textContainer().setWidthTracksTextView_(True)
        self.searchField.textContainer().setHeightTracksTextView_(False)
        
        # 設定滾動畫面的文檔畫面
        self.scrollView.setDocumentView_(self.searchField)
        
        self.addSubview_(self.scrollView)
    
    def update_content(self, plugin_state):
        """更新搜尋欄位內容"""
        try:
            if hasattr(plugin_state, 'lastInput') and self.searchField:
                input_value = plugin_state.lastInput or ""
                self.searchField.setStringValue_(input_value)
        except Exception as e:
            error_log("更新搜尋欄位內容錯誤", e)
    
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
        """解構式"""
        objc.super(SearchPanel, self).dealloc()
