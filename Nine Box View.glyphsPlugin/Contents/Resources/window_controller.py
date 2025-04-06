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
    NSResizableWindowMask, NSMiniaturizableWindowMask, NSFloatingWindowLevel
)
from Foundation import NSObject, NSString

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
            window = NSPanel.alloc().initWithContentRect_styleMask_backing_defer_(
                windowRect,
                styleMask,
                2,
                False
            )
            window.setTitle_(plugin.name)
            window.setMinSize_(NSMakeSize(MIN_WINDOW_SIZE[0], MIN_WINDOW_SIZE[1]))
            window.setLevel_(NSFloatingWindowLevel)
            window.setReleasedWhenClosed_(False)
            
            # 使用規範的 ObjC 初始化方式
            windowController = NSWindowController.alloc().initWithWindow_(window)
            
            # 手動將 self 轉換為擴展的 NSWindowController
            self.window = lambda: window
            self.plugin = plugin
            self.showWindow_ = windowController.showWindow_
            self.previewView = None
            self.searchField = None
            self.pickButton = None
            self.darkModeButton = None
            
            contentView = window.contentView()
            
            # 建立預覽畫面 / Create preview view
            previewRect = NSMakeRect(0, 35, window.frame().size.width, window.frame().size.height - 35)
            self.previewView = self.NineBoxPreviewView.alloc().initWithFrame_plugin_(previewRect, plugin)
            contentView.addSubview_(self.previewView)
            
            # 建立輸入框 / Create input field
            placeholder = Glyphs.localize({
                'en': u'Input glyphs (space-separated) or leave blank',
                'zh-Hant': u'輸入字符（以空格分隔）或留空',
                'zh-Hans': u'输入字符（用空格分隔）或留空',
                'ja': u'文字を入力してください（スペースで区切る）または空欄のまま',
                'ko': u'문자를 입력하세요 (공백으로 구분) 또는 비워 두세요',
            })
            
            searchFieldRect = NSMakeRect(10, 8, window.frame().size.width - 110, 22)
            self.searchField = NSTextField.alloc().initWithFrame_(searchFieldRect)
            self.searchField.setStringValue_(plugin.lastInput)
            self.searchField.setPlaceholderString_(placeholder)
            self.searchField.setTarget_(self)
            self.searchField.setAction_("searchFieldAction:")
            contentView.addSubview_(self.searchField)
            
            # 建立選擇字符按鈕 / Create pick glyph button
            pickButtonRect = NSMakeRect(window.frame().size.width - 95, 8, 40, 22)
            self.pickButton = NSButton.alloc().initWithFrame_(pickButtonRect)
            self.pickButton.setTitle_("🔣")
            self.pickButton.setTarget_(self)
            self.pickButton.setAction_("pickGlyphAction:")
            self.pickButton.setBezelStyle_(1)  # 圓角按鈕 / Rounded button
            contentView.addSubview_(self.pickButton)
            
            # 建立深色模式按鈕 / Create dark mode button
            darkModeButtonRect = NSMakeRect(window.frame().size.width - 50, 8, 40, 22)
            self.darkModeButton = NSButton.alloc().initWithFrame_(darkModeButtonRect)
            self.darkModeButton.setTitle_(plugin.getDarkModeIcon())
            self.darkModeButton.setTarget_(self)
            self.darkModeButton.setAction_("darkModeAction:")
            self.darkModeButton.setBezelStyle_(1)  # 圓角按鈕 / Rounded button
            contentView.addSubview_(self.darkModeButton)
            
            # 監聽視窗大小調整 / Listen for window resize events
            NSNotificationCenter.defaultCenter().addObserver_selector_name_object_(
                self,
                "windowDidResize:",
                NSWindowDidResizeNotification,
                window
            )
            
            # 監聽視窗關閉 / Listen for window close events
            NSNotificationCenter.defaultCenter().addObserver_selector_name_object_(
                self,
                "windowWillClose:",
                NSWindowWillCloseNotification,
                window
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
        if notification.object() == self.window():
            frame = self.window().frame()
            contentView = self.window().contentView()
            contentSize = contentView.frame().size
            
            # 調整預覽畫面大小 / Adjust preview view size
            self.previewView.setFrame_(NSMakeRect(0, 35, contentSize.width, contentSize.height - 35))
            # 調整其他控制項的位置 / Adjust other controls' positions
            self.searchField.setFrame_(NSMakeRect(10, 8, contentSize.width - 110, 22))
            self.pickButton.setFrame_(NSMakeRect(contentSize.width - 95, 8, 40, 22))
            self.darkModeButton.setFrame_(NSMakeRect(contentSize.width - 50, 8, 40, 22))
            
            # 更新重繪 / Update and redraw
            self.previewView.setNeedsDisplay_(True)
    
    def windowWillClose_(self, notification):
        """
        視窗關閉時的處理
        Handle window close events
        
        Args:
            notification: 通知對象
        """
        if notification.object() == self.window():
            # 儲存目前輸入內容 / Save current input
            self.plugin.lastInput = self.searchField.stringValue()
            self.plugin.savePreferences()
            # 儲存視窗大小 / Save window size
            frame = self.window().frame()
            Glyphs.defaults[self.plugin.WINDOW_SIZE_KEY] = (frame.size.width, frame.size.height)
            # 移除觀察者 / Remove observers
            NSNotificationCenter.defaultCenter().removeObserver_(self)
    
    def searchFieldAction_(self, sender):
        """
        輸入框動作處理
        Handle search field action
        
        Args:
            sender: 事件發送者
        """
        self.plugin.searchFieldCallback(sender)
    
    def pickGlyphAction_(self, sender):
        """
        選擇字符按鈕動作處理
        Handle pick glyph button action
        
        Args:
            sender: 事件發送者
        """
        self.plugin.pickGlyph(sender)
    
    def darkModeAction_(self, sender):
        """
        深色模式按鈕動作處理
        Handle dark mode button action
        
        Args:
            sender: 事件發送者
        """
        self.plugin.darkModeCallback(sender)
    
    def redraw(self):
        """
        重繪預覽畫面
        Redraw the preview view
        """
        self.previewView.setNeedsDisplay_(True)
    
    def makeKeyAndOrderFront(self):
        """
        顯示並成為主視窗
        Show and become key window
        """
        try:
            self.showWindow_(None)
            self.window().makeKeyAndOrderFront_(None)
        except Exception as e:
            print(f"顯示視窗時發生錯誤: {e}")
            print(traceback.format_exc()) 