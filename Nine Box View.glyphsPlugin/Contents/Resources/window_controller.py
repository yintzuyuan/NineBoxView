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
    NSBackingStoreBuffered, NSTitlebarAccessoryViewController, NSLayoutConstraint,
    NSView, NSViewMaxYMargin, NSViewMinYMargin, NSLayoutAttributeBottom,
    NSLayoutAttributeTop, NSLayoutAttributeRight, NSLayoutAttributeLeft,
    NSLayoutRelationEqual, NSStackView, NSStackViewGravityTrailing
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
            from sidebar_view import SidebarView
            self.NineBoxPreviewView = NineBoxPreviewView
            self.SidebarView = SidebarView
            
            # 載入上次儲存的視窗大小 / Load last saved window size
            from constants import WINDOW_SIZE_KEY, DEFAULT_WINDOW_SIZE, MIN_WINDOW_SIZE, SIDEBAR_WIDTH
            self.SIDEBAR_WIDTH = SIDEBAR_WIDTH
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
                self.sidebarButton = None
                self.sidebarView = None
                
                contentView = panel.contentView()
                
                # 建立預覽畫面 - 擴展到整個視窗區域
                previewRect = NSMakeRect(0, 0, panel.frame().size.width, panel.frame().size.height)
                self.previewView = self.NineBoxPreviewView.alloc().initWithFrame_plugin_(previewRect, plugin)
                contentView.addSubview_(self.previewView)
                
                # 建立側邊欄按鈕並放置在標題列上
                # 首先創建按鈕
                self.sidebarButton = NSButton.alloc().init()
                self.sidebarButton.setTitle_("≡")  # 使用漢堡選單圖示
                self.sidebarButton.setTarget_(self)
                self.sidebarButton.setAction_("sidebarAction:")
                self.sidebarButton.setBezelStyle_(NSTexturedRoundedBezelStyle)  # 使用紋理圓角按鈕樣式
                self.sidebarButton.setButtonType_(NSButtonTypeToggle)  # 使用開關按鈕類型
                
                # 設定側邊欄按鈕提示 / Set sidebar button tooltip
                sidebarTooltip = Glyphs.localize({
                    'en': u'Show/hide controls panel',
                    'zh-Hant': u'顯示/隱藏控制面板',
                    'zh-Hans': u'显示/隐藏控制面板',
                    'ja': u'コントロールパネルを表示/非表示',
                    'ko': u'컨트롤 패널 표시/숨기기',
                })
                
                self.sidebarButton.setToolTip_(sidebarTooltip)
                
                # 設定按鈕狀態 / Set button state
                if plugin.sidebarVisible:
                    self.sidebarButton.setState_(1)  # 1 表示開啟
                else:
                    self.sidebarButton.setState_(0)  # 0 表示關閉
                
                # 創建一個容器視圖來放置按鈕
                buttonView = NSView.alloc().initWithFrame_(NSMakeRect(0, 0, 30, 24))
                buttonView.addSubview_(self.sidebarButton)
                self.sidebarButton.setFrame_(NSMakeRect(0, 0, 30, 24))
                
                # 創建標題列附件控制器
                accessoryController = NSTitlebarAccessoryViewController.alloc().init()
                accessoryController.setView_(buttonView)
                accessoryController.setLayoutAttribute_(NSLayoutAttributeRight)  # 放在右邊
                
                # 添加到視窗的標題列
                panel.addTitlebarAccessoryViewController_(accessoryController)
                
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
                
                # 如果側邊欄可見，則創建並顯示側邊欄
                if plugin.sidebarVisible:
                    self._showSidebar()
            
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
                
                # 調整預覽畫面大小 - 始終填滿整個視窗
                if hasattr(self, 'previewView') and self.previewView:
                    # 預覽視圖始終佔據整個視窗，不留工具欄區域
                    if hasattr(self, 'sidebarView') and self.sidebarView and hasattr(self.plugin, 'sidebarVisible') and self.plugin.sidebarVisible:
                        self.previewView.setFrame_(NSMakeRect(0, 0, contentSize.width - self.SIDEBAR_WIDTH, contentSize.height))
                    else:
                        self.previewView.setFrame_(NSMakeRect(0, 0, contentSize.width, contentSize.height))
                
                # 調整側邊欄大小
                if hasattr(self, 'sidebarView') and self.sidebarView:
                    self.sidebarView.setFrame_(NSMakeRect(contentSize.width - self.SIDEBAR_WIDTH, 0, self.SIDEBAR_WIDTH, contentSize.height))
                
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
    
    def _showSidebar(self):
        """顯示側邊欄"""
        try:
            # 如果側邊欄視圖不存在，則創建它
            if not hasattr(self, 'sidebarView') or not self.sidebarView:
                contentSize = self.window().contentView().frame().size
                sidebarRect = NSMakeRect(contentSize.width - self.SIDEBAR_WIDTH, 0, self.SIDEBAR_WIDTH, contentSize.height)
                self.sidebarView = self.SidebarView.alloc().initWithFrame_plugin_(sidebarRect, self.plugin)
                self.window().contentView().addSubview_(self.sidebarView)
            else:
                self.sidebarView.setHidden_(False)
                
            # 調整預覽視圖大小 - 為側邊欄留出空間
            contentSize = self.window().contentView().frame().size
            self.previewView.setFrame_(NSMakeRect(0, 0, contentSize.width - self.SIDEBAR_WIDTH, contentSize.height))
            
            # 更新側邊欄內容
            self.sidebarView.updateFontInfo()
            self.sidebarView.updateSearchField()
        except Exception as e:
            print(f"顯示側邊欄時發生錯誤: {e}")
            print(traceback.format_exc())
    
    def _hideSidebar(self):
        """隱藏側邊欄"""
        try:
            # 隱藏側邊欄
            if hasattr(self, 'sidebarView') and self.sidebarView:
                self.sidebarView.setHidden_(True)
            
            # 調整預覽視圖大小 - 佔據整個視窗
            contentSize = self.window().contentView().frame().size
            self.previewView.setFrame_(NSMakeRect(0, 0, contentSize.width, contentSize.height))
        except Exception as e:
            print(f"隱藏側邊欄時發生錯誤: {e}")
            print(traceback.format_exc())
    
    def sidebarAction_(self, sender):
        """側邊欄按鈕動作"""
        try:
            # 切換側邊欄可見性
            self.plugin.sidebarVisible = not (hasattr(self.plugin, 'sidebarVisible') and self.plugin.sidebarVisible)
            
            # 更新側邊欄按鈕狀態
            if self.plugin.sidebarVisible:
                self.sidebarButton.setState_(1)  # 1 表示開啟
                self._showSidebar()
            else:
                self.sidebarButton.setState_(0)  # 0 表示關閉
                self._hideSidebar()
            
            # 保存偏好設定
            self.plugin.savePreferences()
            
            # 重繪
            self.redraw()
        except Exception as e:
            print(f"處理側邊欄按鈕動作時發生錯誤: {e}")
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
            # 重繪預覽視圖
            if hasattr(self, 'previewView') and self.previewView:
                self.previewView.setNeedsDisplay_(True)
            
            # 重繪側邊欄
            if hasattr(self, 'sidebarView') and self.sidebarView and not self.sidebarView.isHidden():
                self.sidebarView.updateFontInfo()
                self.sidebarView.setNeedsDisplay_(True)
        except Exception as e:
            print(f"重繪介面時發生錯誤: {e}")
            print(traceback.format_exc()) 