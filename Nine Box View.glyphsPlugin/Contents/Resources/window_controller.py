# encoding: utf-8
"""
九宮格預覽外掛 - 視窗控制器
Nine Box Preview Plugin - Window Controller
"""

from __future__ import division, print_function, unicode_literals
import traceback
import objc
from GlyphsApp import Glyphs
from AppKit import (
    NSWindowController, NSPanel, NSButton, NSTextField, NSRect, NSMakeRect, NSString, 
    NSMakeSize, NSWindow, NSNotificationCenter, NSWindowWillCloseNotification, 
    NSWindowDidResizeNotification, NSTitledWindowMask, NSClosableWindowMask,
    NSResizableWindowMask, NSMiniaturizableWindowMask, NSFloatingWindowLevel,
    NSVisualEffectView, NSVisualEffectMaterialLight, NSVisualEffectMaterialDark,
    NSVisualEffectBlendingModeBehindWindow, NSSearchField, NSColor, NSFont,
    NSButtonTypeToggle, NSButtonTypeMomentaryPushIn, NSBezelStyleRounded,
    NSTexturedRoundedBezelStyle, NSFocusRingTypeNone, NSToolTipAttributeName,
    NSBackingStoreBuffered
)
from Foundation import NSObject, NSString, NSDictionary, NSAttributedString

# 注意：NineBoxPreviewView 將在初始化時動態導入，避免循環依賴
# Note: NineBoxPreviewView will be dynamically imported during initialization to avoid circular dependencies

class NineBoxWindow(NSWindowController):
    """
    九宮格預覽視窗控制器，取代原有的 Vanilla FloatingWindow。
    Nine Box Window Controller, replaces the original Vanilla FloatingWindow.
    """
    
    def initWithPlugin_(self, plugin):
        """
        初始化視窗控制器
        Initialize the window controller
        
        Args:
            plugin: 外掛主類別實例
            
        Returns:
            self: 初始化後的視窗控制器實例
        """
        try:
            # 在這裡導入以避免循環依賴
            # Import here to avoid circular dependencies
            from preview_view import NineBoxPreviewView
            self.NineBoxPreviewView = NineBoxPreviewView
            
            # 載入上次儲存的視窗大小 / Load last saved window size
            from constants import WINDOW_SIZE_KEY, DEFAULT_WINDOW_SIZE, MIN_WINDOW_SIZE
            savedSize = Glyphs.defaults.get(WINDOW_SIZE_KEY, DEFAULT_WINDOW_SIZE)
            
            # 建立視窗 / Create window
            windowRect = NSMakeRect(0, 0, savedSize[0], savedSize[1])
            styleMask = NSTitledWindowMask | NSClosableWindowMask | NSResizableWindowMask | NSMiniaturizableWindowMask
            panel = NSPanel.alloc().initWithContentRect_styleMask_backing_defer_(
                windowRect,
                styleMask,
                NSBackingStoreBuffered,
                False
            )
            panel.setTitle_(plugin.name)
            panel.setMinSize_(NSMakeSize(MIN_WINDOW_SIZE[0], MIN_WINDOW_SIZE[1]))
            panel.setLevel_(NSFloatingWindowLevel)
            panel.setReleasedWhenClosed_(False)
            
            # 正確初始化 NSWindowController
            # 使用 objc 的 super 正確地初始化父類別
            self = objc.super(NineBoxWindow, self).init()
            
            if self:
                # 設置視窗
                self.setWindow_(panel)
                
                # 保存相關屬性
                self.plugin = plugin
                self.previewView = None
                self.searchField = None
                self.pickButton = None
                self.darkModeButton = None
                
                contentView = panel.contentView()
                
                # 建立預覽畫面 / Create preview view
                previewRect = NSMakeRect(0, 35, panel.frame().size.width, panel.frame().size.height - 35)
                self.previewView = self.NineBoxPreviewView.alloc().initWithFrame_plugin_(previewRect, plugin)
                contentView.addSubview_(self.previewView)
                
                # 建立搜尋欄位 / Create search field
                placeholder = Glyphs.localize({
                    'en': u'Input glyphs (space-separated) or leave blank',
                    'zh-Hant': u'輸入字符（以空格分隔）或留空',
                    'zh-Hans': u'输入字符（用空格分隔）或留空',
                    'ja': u'文字を入力してください（スペースで区切る）または空欄のまま',
                    'ko': u'문자를 입력하세요 (공백으로 구분) 또는 비워 두세요',
                })
                
                searchFieldRect = NSMakeRect(10, 8, panel.frame().size.width - 110, 22)
                # 使用搜尋欄位替代一般文字欄位 / Use search field instead of text field
                self.searchField = NSSearchField.alloc().initWithFrame_(searchFieldRect)
                self.searchField.setStringValue_(plugin.lastInput)
                self.searchField.setPlaceholderString_(placeholder)
                self.searchField.setTarget_(self)
                self.searchField.setAction_("searchFieldAction:")
                
                # 設定搜尋欄位外觀 / Configure search field appearance
                self.searchField.setFont_(NSFont.systemFontOfSize_(12.0))
                self.searchField.setFocusRingType_(NSFocusRingTypeNone)
                
                # 設定搜尋欄位提示 / Set search field tooltip
                searchTooltip = Glyphs.localize({
                    'en': u'Enter glyphs to display around the selected glyph',
                    'zh-Hant': u'輸入要在選定字符周圍顯示的字符',
                    'zh-Hans': u'输入要在选定字符周围显示的字符',
                    'ja': u'選択された文字の周りに表示する文字を入力してください',
                    'ko': u'선택한 글자 주변에 표시할 글자를 입력하세요',
                })
                
                self.searchField.setToolTip_(searchTooltip)
                contentView.addSubview_(self.searchField)
                
                # 建立選擇字符按鈕 / Create pick glyph button
                pickButtonRect = NSMakeRect(panel.frame().size.width - 95, 8, 40, 22)
                self.pickButton = NSButton.alloc().initWithFrame_(pickButtonRect)
                self.pickButton.setTitle_("🔣")
                self.pickButton.setTarget_(self)
                self.pickButton.setAction_("pickGlyphAction:")
                self.pickButton.setBezelStyle_(NSTexturedRoundedBezelStyle)  # 使用紋理圓角按鈕樣式
                self.pickButton.setButtonType_(NSButtonTypeMomentaryPushIn)
                
                # 設定選擇字符按鈕提示 / Set pick glyph button tooltip
                pickTooltip = Glyphs.localize({
                    'en': u'Select glyphs from the font',
                    'zh-Hant': u'從字型中選擇字符',
                    'zh-Hans': u'从字体中选择字符',
                    'ja': u'フォントから文字を選択',
                    'ko': u'폰트에서 글자 선택',
                })
                
                self.pickButton.setToolTip_(pickTooltip)
                contentView.addSubview_(self.pickButton)
                
                # 建立深色模式按鈕 / Create dark mode button
                darkModeButtonRect = NSMakeRect(panel.frame().size.width - 50, 8, 40, 22)
                self.darkModeButton = NSButton.alloc().initWithFrame_(darkModeButtonRect)
                self.darkModeButton.setTitle_(plugin.getDarkModeIcon())
                self.darkModeButton.setTarget_(self)
                self.darkModeButton.setAction_("darkModeAction:")
                self.darkModeButton.setBezelStyle_(NSTexturedRoundedBezelStyle)  # 使用紋理圓角按鈕樣式
                self.darkModeButton.setButtonType_(NSButtonTypeToggle)  # 使用開關按鈕類型
                
                # 設定深色模式按鈕提示 / Set dark mode button tooltip
                darkModeTooltip = Glyphs.localize({
                    'en': u'Toggle dark mode',
                    'zh-Hant': u'切換深色模式',
                    'zh-Hans': u'切换深色模式',
                    'ja': u'ダークモードを切り替える',
                    'ko': u'다크 모드 전환',
                })
                
                self.darkModeButton.setToolTip_(darkModeTooltip)
                
                # 設定按鈕狀態 / Set button state
                if plugin.darkMode:
                    self.darkModeButton.setState_(1)  # 1 表示開啟
                else:
                    self.darkModeButton.setState_(0)  # 0 表示關閉
                    
                contentView.addSubview_(self.darkModeButton)
                
                # 監聽視窗大小調整 / Listen for window resize events
                NSNotificationCenter.defaultCenter().addObserver_selector_name_object_(
                    self,
                    "windowDidResize:",
                    NSWindowDidResizeNotification,
                    panel
                )
                
                # 監聽視窗關閉 / Listen for window close events
                NSNotificationCenter.defaultCenter().addObserver_selector_name_object_(
                    self,
                    "windowWillClose:",
                    NSWindowWillCloseNotification,
                    panel
                )
                
                # 如果有選取的字符但沒有排列，則生成新排列 / Generate a new arrangement if there are selected characters but no arrangement
                if plugin.selectedChars and not plugin.currentArrangement:
                    plugin.generateNewArrangement()
            
        except Exception as e:
            print(f"初始化視窗時發生錯誤: {e}")
            print(traceback.format_exc())
            
        return self
    
    def windowDidResize_(self, notification):
        """
        視窗大小調整時的處理
        Handle window resize events
        
        Args:
            notification: 通知對象
        """
        try:
            if notification.object() == self.window():
                frame = self.window().frame()
                contentView = self.window().contentView()
                contentSize = contentView.frame().size
                
                # 調整預覽畫面大小 / Adjust preview view size
                if hasattr(self, 'previewView') and self.previewView:
                    self.previewView.setFrame_(NSMakeRect(0, 35, contentSize.width, contentSize.height - 35))
                
                # 調整其他控制項的位置 / Adjust other controls' positions
                if hasattr(self, 'searchField') and self.searchField:
                    self.searchField.setFrame_(NSMakeRect(10, 8, contentSize.width - 110, 22))
                
                if hasattr(self, 'pickButton') and self.pickButton:
                    self.pickButton.setFrame_(NSMakeRect(contentSize.width - 95, 8, 40, 22))
                
                if hasattr(self, 'darkModeButton') and self.darkModeButton:
                    self.darkModeButton.setFrame_(NSMakeRect(contentSize.width - 50, 8, 40, 22))
                
                # 儲存視窗大小 / Save the window size
                if hasattr(self, 'plugin'):
                    newSize = [frame.size.width, frame.size.height]
                    Glyphs.defaults[self.plugin.WINDOW_SIZE_KEY] = newSize
        except Exception as e:
            print(f"處理視窗大小調整時發生錯誤: {e}")
            print(traceback.format_exc())
    
    def windowWillClose_(self, notification):
        """
        視窗關閉時的處理
        Handle window close events
        
        Args:
            notification: 通知對象
        """
        try:
            # 保存偏好設定 / Save preferences
            if hasattr(self, 'plugin'):
                self.plugin.savePreferences()
                
            # 移除通知觀察者 / Remove notification observers
            NSNotificationCenter.defaultCenter().removeObserver_(self)
        except Exception as e:
            print(f"處理視窗關閉時發生錯誤: {e}")
            print(traceback.format_exc())
    
    def searchFieldAction_(self, sender):
        """
        搜尋欄位動作處理
        Handle search field action
        
        Args:
            sender: 事件發送者
        """
        try:
            if hasattr(self, 'plugin'):
                self.plugin.searchFieldCallback(sender)
        except Exception as e:
            print(f"處理搜尋欄位動作時發生錯誤: {e}")
            print(traceback.format_exc())
    
    def pickGlyphAction_(self, sender):
        """
        選擇字符按鈕動作處理
        Handle pick glyph button action
        
        Args:
            sender: 事件發送者
        """
        try:
            if hasattr(self, 'plugin'):
                self.plugin.pickGlyphCallback(sender)
        except Exception as e:
            print(f"處理選擇字符按鈕動作時發生錯誤: {e}")
            print(traceback.format_exc())
    
    def darkModeAction_(self, sender):
        """
        深色模式按鈕動作處理
        Handle dark mode button action
        
        Args:
            sender: 事件發送者
        """
        try:
            if hasattr(self, 'plugin'):
                # 切換深色模式
                self.plugin.darkModeCallback(sender)
                
                # 更新按鈕標題
                self.darkModeButton.setTitle_(self.plugin.getDarkModeIcon())
                
                # 更新按鈕狀態
                self.darkModeButton.setState_(1 if self.plugin.darkMode else 0)
                
                # 重繪預覽視圖
                if hasattr(self, 'previewView') and self.previewView:
                    self.previewView.setNeedsDisplay_(True)
        except Exception as e:
            print(f"處理深色模式按鈕動作時發生錯誤: {e}")
            print(traceback.format_exc())
    
    def makeKeyAndOrderFront(self):
        """
        顯示視窗並成為焦點
        Show the window and become key window
        """
        if hasattr(self, 'window') and self.window():
            self.window().makeKeyAndOrderFront_(self)
    
    def redraw(self):
        """
        重繪介面
        Redraw the interface
        """
        try:
            # 更新按鈕標題 / Update button titles
            if hasattr(self, 'darkModeButton') and self.darkModeButton:
                self.darkModeButton.setTitle_(self.plugin.getDarkModeIcon())
                self.darkModeButton.setState_(1 if self.plugin.darkMode else 0)
            
            # 重繪預覽視圖 / Redraw the preview view
            if hasattr(self, 'previewView') and self.previewView:
                self.previewView.setNeedsDisplay_(True)
        except Exception as e:
            print(f"重繪介面時發生錯誤: {e}")
            print(traceback.format_exc()) 