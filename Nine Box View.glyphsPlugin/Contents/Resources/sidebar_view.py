# encoding: utf-8
"""
九宮格預覽外掛 - 側邊欄視圖
Nine Box Preview Plugin - Sidebar View
"""

from __future__ import division, print_function, unicode_literals
import traceback
import objc
from GlyphsApp import Glyphs
from AppKit import (
    NSView, NSColor, NSRectFill, NSBezierPath, NSFont, 
    NSFontAttributeName, NSForegroundColorAttributeName,
    NSMutableDictionary, NSString, NSMakeRect, NSTextField,
    NSMakePoint, NSButton, NSBezelStyleRounded,
    NSTexturedRoundedBezelStyle, NSButtonTypeMomentaryPushIn,
    NSAttributedString, NSCenterTextAlignment, NSSearchField,
    NSButtonTypeToggle, NSFocusRingTypeNone, 
    NSCompositingOperationSourceOver, NSBorderlessWindowMask,
    NSUserDefaults, NSNotificationCenter, NSUserDefaultsDidChangeNotification,
    NSApp, NSViewWidthSizable, NSViewHeightSizable, NSViewMinYMargin, NSViewMaxYMargin,
    NSMenu, NSMenuItem, NSApplication, NSEventMask, NSEventTypeRightMouseDown,
    NSPointInRect
)

# 修改 CustomTextField 類別，添加文字變更監聽功能
class CustomTextField(NSTextField):
    """支援右鍵選單的文本框類別"""
    
    def initWithFrame_plugin_(self, frame, plugin):
        """初始化文本框"""
        self = objc.super(CustomTextField, self).initWithFrame_(frame)
        if self:
            self.plugin = plugin
            # 設定右鍵選單
            self.setupContextMenu()
            
            # 註冊文本變更通知，實現即時更新
            NSNotificationCenter.defaultCenter().addObserver_selector_name_object_(
                self,
                "textDidChange:",
                "NSControlTextDidChangeNotification",
                self
            )
        return self
    
    def setupContextMenu(self):
        """設定右鍵選單"""
        try:
            # 創建選單
            contextMenu = NSMenu.alloc().init()
            
            # 添加選擇字符選單項
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
            
            # 設定選單
            self.setMenu_(contextMenu)
            
        except Exception as e:
            print(f"設定右鍵選單時發生錯誤: {e}")
            print(traceback.format_exc())
    
    def textDidChange_(self, notification):
        """文本變更時的回調函數"""
        try:
            if hasattr(self, 'plugin') and self.plugin:
                # 直接調用 plugin 的搜尋欄位回調函數，傳遞自己作為參數
                self.plugin.searchFieldCallback(self)
        except Exception as e:
            print(f"處理文本變更時發生錯誤: {e}")
            print(traceback.format_exc())
    
    def pickGlyphAction_(self, sender):
        """選擇字符功能的回調函數"""
        if hasattr(self, 'plugin') and self.plugin:
            self.plugin.pickGlyphCallback(sender)
            
    def dealloc(self):
        """釋放資源"""
        # 移除通知觀察者
        NSNotificationCenter.defaultCenter().removeObserver_(self)
        objc.super(CustomTextField, self).dealloc()


class SidebarView(NSView):
    """
    側邊欄視圖類別，顯示額外資訊和控制項
    Sidebar View Class, displays additional information and controls
    """

    def initWithFrame_plugin_(self, frame, plugin):
        """
        初始化側邊欄視圖
        Initialize the sidebar view
        
        Args:
            frame: 視圖尺寸和位置
            plugin: 外掛主類別實例
        
        Returns:
            self: 初始化後的視圖實例
        """
        self = objc.super(SidebarView, self).initWithFrame_(frame)
        if self:
            self.plugin = plugin
            
            # 設置側邊欄視圖的自動調整掩碼 - 視圖寬度可調整，高度可調整
            self.setAutoresizingMask_(NSViewWidthSizable | NSViewHeightSizable)
            
            # 視圖內部元素的常數設定
            margin = 10
            totalHeight = frame.size.height
            frameWidth = frame.size.width
            
            # 搜尋欄位 - 使用多行文本框佔據整個側邊欄空間
            searchFieldRect = NSMakeRect(margin, margin, frameWidth - margin * 2, totalHeight - margin * 2)
            self.searchField = CustomTextField.alloc().initWithFrame_plugin_(searchFieldRect, plugin)
            
            placeholder = Glyphs.localize({
                'en': u'Input glyphs or nice names (only nice names need spaces)',
                'zh-Hant': u'輸入字符或 Nice Name（僅 Nice Name 需要空格分隔）',
                'zh-Hans': u'输入字符或 Nice Name（仅 Nice Name 需要空格分隔）',
                'ja': u'文字または Nice Name を入力してください（Nice Name のみスペースが必要）',
                'ko': u'문자 또는 Nice Name을 입력하세요 (Nice Name만 공백 필요)',
            })
            
            self.searchField.setStringValue_(plugin.lastInput)
            self.searchField.setPlaceholderString_(placeholder)
            
            # 設定文本框外觀
            self.searchField.setFont_(NSFont.systemFontOfSize_(12.0))
            self.searchField.setFocusRingType_(NSFocusRingTypeNone)
            self.searchField.setBezeled_(True)
            self.searchField.setEditable_(True)
            
            # 設定為多行文本框
            self.searchField.setUsesSingleLineMode_(False)
            
            # 設定提示
            searchTooltip = Glyphs.localize({
                'en': u'Enter glyphs or nice names (only nice names need spaces)\nRight-click to select glyphs from font',
                'zh-Hant': u'輸入字符或 Nice Name，只有 Nice Name 需要用空格分隔\n右鍵點擊可從字型中選擇字符',
                'zh-Hans': u'输入字符或 Nice Name，只有 Nice Name 需要用空格分隔\n右键点击可从字体中选择字符',
                'ja': u'文字または Nice Name を入力してください（Nice Name のみスペースが必要）\n右クリックでフォントから文字を選択',
                'ko': u'문자 또는 Nice Name을 입력하세요 (Nice Name만 공백 필요)\n마우스 오른쪽 버튼으로 글꼴에서 글자 선택',
            })
            
            self.searchField.setToolTip_(searchTooltip)
            self.searchField.setTarget_(self)
            self.searchField.setAction_("searchFieldAction:")
            self.searchField.setAutoresizingMask_(NSViewWidthSizable | NSViewHeightSizable)
            
            self.addSubview_(self.searchField)
            
        return self
    
    def searchFieldAction_(self, sender):
        """處理輸入框的回調函數 / Callback function for the input field"""
        if self.plugin:
            self.plugin.searchFieldCallback(sender)
    
    def updateSearchField(self):
        """更新搜尋欄位文字 / Update search field text"""
        if hasattr(self, 'searchField') and hasattr(self.plugin, 'lastInput'):
            self.searchField.setStringValue_(self.plugin.lastInput)
    
    def drawRect_(self, rect):
        """
        繪製側邊欄背景
        Draw the sidebar background
        
        Args:
            rect: 要繪製的矩形區域
        """
        try:
            # 使用系統深淺色模式設定
            is_black = NSUserDefaults.standardUserDefaults().boolForKey_("GSPreview_Black")
            
            # 設定背景顏色
            if is_black:
                NSColor.colorWithCalibratedWhite_alpha_(0.13, 1.0).set()  # 深色背景
            else:
                NSColor.colorWithCalibratedWhite_alpha_(0.95, 1.0).set()  # 淺色背景
            
            NSRectFill(rect)
            
        except Exception as e:
            print(f"繪製側邊欄時發生錯誤: {e}")
            print(traceback.format_exc()) 