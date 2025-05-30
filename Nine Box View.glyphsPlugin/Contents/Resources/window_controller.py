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
    NSWindowDidResizeNotification, NSWindowDidMoveNotification, NSTitledWindowMask, NSClosableWindowMask,
    NSResizableWindowMask, NSMiniaturizableWindowMask, NSFloatingWindowLevel,
    NSVisualEffectView, NSVisualEffectMaterialLight, NSVisualEffectMaterialDark,
    NSVisualEffectBlendingModeBehindWindow, NSSearchField, NSColor, NSFont,
    NSButtonTypeToggle, NSButtonTypeMomentaryPushIn, NSBezelStyleRounded,
    NSTexturedRoundedBezelStyle, NSFocusRingTypeNone, NSToolTipAttributeName,
    NSBackingStoreBuffered, NSTitlebarAccessoryViewController, NSLayoutConstraint,
    NSView, NSViewMaxYMargin, NSViewMinYMargin, NSLayoutAttributeBottom,
    NSLayoutAttributeTop, NSLayoutAttributeRight, NSLayoutAttributeLeft,
    NSLayoutRelationEqual, NSStackView, NSStackViewGravityTrailing,
    NSUserDefaults, NSBorderlessWindowMask, NSUtilityWindowMask
)
from Foundation import NSObject, NSString, NSDictionary, NSAttributedString, NSUserDefaultsDidChangeNotification

# 注意：NineBoxPreviewView 和 ControlsPanelView 將在初始化時動態導入，避免循環依賴
# Note: NineBoxPreviewView and ControlsPanelView will be dynamically imported during initialization to avoid circular dependencies

class ControlsPanelWindow(NSPanel):
    """
    控制面板子視窗類別，無標題列的獨立面板
    Controls Panel Sub-window class, independent panel without title bar
    """
    
    def initWithContentRect_styleMask_backing_defer_mainWindow_(self, contentRect, styleMask, backing, defer, mainWindow):
        """初始化控制面板視窗"""
        # 使用無邊框樣式移除標題列
        styleMask = NSBorderlessWindowMask | NSUtilityWindowMask
        
        self = objc.super(ControlsPanelWindow, self).initWithContentRect_styleMask_backing_defer_(
            contentRect, styleMask, backing, defer
        )
        
        if self:
            self.mainWindow = mainWindow
            
            # 設定面板屬性
            self.setLevel_(NSFloatingWindowLevel)
            self.setReleasedWhenClosed_(False)
            self.setHidesOnDeactivate_(False)  # 不要在失去焦點時隱藏
            self.setFloatingPanel_(True)
            
            # 設定背景顏色
            self.setBackgroundColor_(NSColor.controlBackgroundColor())
            
        return self


class NineBoxWindow(NSWindowController):
    """
    九宮格預覽視窗控制器，管理主視窗和控制面板子視窗。
    Nine Box Window Controller, manages main window and controls panel sub-window.
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
            from controls_panel_view import ControlsPanelView
            self.NineBoxPreviewView = NineBoxPreviewView
            self.ControlsPanelView = ControlsPanelView
            
            # 先確保外掛的偏好設定已經載入
            # Ensure plugin preferences are loaded first
            plugin.loadPreferences()
            
            # 載入上次儲存的視窗大小 / Load last saved window size
            from constants import (
                WINDOW_SIZE_KEY, DEFAULT_WINDOW_SIZE, MIN_WINDOW_SIZE, 
                CONTROLS_PANEL_WIDTH, CONTROLS_PANEL_MIN_HEIGHT,
                CONTROLS_PANEL_VISIBLE_KEY
            )
            self.CONTROLS_PANEL_WIDTH = CONTROLS_PANEL_WIDTH
            self.CONTROLS_PANEL_MIN_HEIGHT = CONTROLS_PANEL_MIN_HEIGHT
            
            savedSize = Glyphs.defaults.get(WINDOW_SIZE_KEY, DEFAULT_WINDOW_SIZE)
            
            # 建立主視窗 / Create main window
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
                # 設置主視窗
                self.setWindow_(panel)
                
                # 保存相關屬性
                self.plugin = plugin
                self.previewView = None
                self.controlsPanelButton = None
                self.controlsPanelWindow = None
                self.controlsPanelView = None
                
                # 載入控制面板顯示狀態
                self.controlsPanelVisible = Glyphs.defaults.get(CONTROLS_PANEL_VISIBLE_KEY, True)
                
                contentView = panel.contentView()
                
                # 建立預覽畫面 - 擴展到整個視窗區域
                previewRect = NSMakeRect(0, 0, panel.frame().size.width, panel.frame().size.height)
                self.previewView = self.NineBoxPreviewView.alloc().initWithFrame_plugin_(previewRect, plugin)
                contentView.addSubview_(self.previewView)
                
                # 確保預覽畫面正確調整到內容區域大小，並觸發初始重繪
                actualContentSize = contentView.frame().size
                self.previewView.setFrame_(NSMakeRect(0, 0, actualContentSize.width, actualContentSize.height))
                self.previewView.setNeedsDisplay_(True)
                
                # 建立控制面板按鈕並放置在標題列上
                self.controlsPanelButton = NSButton.alloc().init()
                self.controlsPanelButton.setTitle_("⚙")  # 使用齒輪圖示
                self.controlsPanelButton.setTarget_(self)
                self.controlsPanelButton.setAction_("controlsPanelAction:")
                self.controlsPanelButton.setBezelStyle_(NSTexturedRoundedBezelStyle)
                self.controlsPanelButton.setButtonType_(NSButtonTypeToggle)
                
                # 設定控制面板按鈕提示
                controlsPanelTooltip = Glyphs.localize({
                    'en': u'Show/hide controls panel',
                    'zh-Hant': u'顯示/隱藏控制面板',
                    'zh-Hans': u'显示/隐藏控制面板',
                    'ja': u'コントロールパネルを表示/非表示',
                    'ko': u'컨트롤 패널 표시/숨기기',
                })
                self.controlsPanelButton.setToolTip_(controlsPanelTooltip)
                
                # 設定按鈕狀態
                if self.controlsPanelVisible:
                    self.controlsPanelButton.setState_(1)  # 1 表示開啟
                else:
                    self.controlsPanelButton.setState_(0)  # 0 表示關閉
                
                # 創建一個容器視圖來放置按鈕
                buttonView = NSView.alloc().initWithFrame_(NSMakeRect(0, 0, 30, 24))
                buttonView.addSubview_(self.controlsPanelButton)
                self.controlsPanelButton.setFrame_(NSMakeRect(0, 0, 30, 24))
                
                # 創建標題列附件控制器
                accessoryController = NSTitlebarAccessoryViewController.alloc().init()
                accessoryController.setView_(buttonView)
                accessoryController.setLayoutAttribute_(NSLayoutAttributeRight)  # 放在右邊
                
                # 添加到視窗的標題列
                panel.addTitlebarAccessoryViewController_(accessoryController)
                
                # 創建控制面板子視窗
                self.createControlsPanelWindow()
                
                # 監聽視窗大小調整 / Listen for window resize events
                NSNotificationCenter.defaultCenter().addObserver_selector_name_object_(
                    self,
                    "windowDidResize:",
                    NSWindowDidResizeNotification,
                    panel
                )
                
                # 監聽視窗移動 / Listen for window move events
                NSNotificationCenter.defaultCenter().addObserver_selector_name_object_(
                    self,
                    "windowDidMove:",
                    NSWindowDidMoveNotification,
                    panel
                )
                
                # 監聽視窗關閉 / Listen for window close events
                NSNotificationCenter.defaultCenter().addObserver_selector_name_object_(
                    self,
                    "windowWillClose:",
                    NSWindowWillCloseNotification,
                    panel
                )
                
                # 如果控制面板應該顯示，則顯示它
                if self.controlsPanelVisible:
                    self.showControlsPanel()
                
            return self
        except Exception as e:
            print(f"初始化視窗控制器時發生錯誤: {e}")
            print(traceback.format_exc())
            return None
    
    def createControlsPanelWindow(self):
        """創建控制面板子視窗"""
        try:
            # 計算控制面板的位置和大小
            mainFrame = self.window().frame()
            panelHeight = max(mainFrame.size.height, self.CONTROLS_PANEL_MIN_HEIGHT)
            
            # 控制面板位置在主視窗右側
            panelX = mainFrame.origin.x + mainFrame.size.width + 10  # 10像素間距
            panelY = mainFrame.origin.y
            
            panelRect = NSMakeRect(panelX, panelY, self.CONTROLS_PANEL_WIDTH, panelHeight)
            
            # 創建控制面板視窗
            self.controlsPanelWindow = ControlsPanelWindow.alloc().initWithContentRect_styleMask_backing_defer_mainWindow_(
                panelRect,
                NSBorderlessWindowMask | NSUtilityWindowMask,
                NSBackingStoreBuffered,
                False,
                self.window()
            )
            
            # 創建控制面板視圖
            contentRect = NSMakeRect(0, 0, self.CONTROLS_PANEL_WIDTH, panelHeight)
            self.controlsPanelView = self.ControlsPanelView.alloc().initWithFrame_plugin_(
                contentRect, self.plugin
            )
            
            # 設定控制面板視窗的內容視圖
            self.controlsPanelWindow.setContentView_(self.controlsPanelView)
            
        except Exception as e:
            print(f"創建控制面板視窗時發生錯誤: {e}")
            print(traceback.format_exc())
    
    def showControlsPanel(self):
        """顯示控制面板"""
        try:
            if self.controlsPanelWindow:
                # 更新控制面板位置和大小
                self.updateControlsPanelPosition()
                
                # 顯示控制面板
                self.controlsPanelWindow.orderFront_(None)
                
                # 更新狀態
                self.controlsPanelVisible = True
                self.controlsPanelButton.setState_(1)
                
                # 儲存偏好設定
                from constants import CONTROLS_PANEL_VISIBLE_KEY
                Glyphs.defaults[CONTROLS_PANEL_VISIBLE_KEY] = True
                
        except Exception as e:
            print(f"顯示控制面板時發生錯誤: {e}")
            print(traceback.format_exc())
    
    def hideControlsPanel(self):
        """隱藏控制面板"""
        try:
            if self.controlsPanelWindow:
                # 隱藏控制面板
                self.controlsPanelWindow.orderOut_(None)
                
                # 更新狀態
                self.controlsPanelVisible = False
                self.controlsPanelButton.setState_(0)
                
                # 儲存偏好設定
                from constants import CONTROLS_PANEL_VISIBLE_KEY
                Glyphs.defaults[CONTROLS_PANEL_VISIBLE_KEY] = False
                
        except Exception as e:
            print(f"隱藏控制面板時發生錯誤: {e}")
            print(traceback.format_exc())
    
    def updateControlsPanelPosition(self):
        """更新控制面板的位置和大小"""
        try:
            if self.controlsPanelWindow:
                # 獲取主視窗的當前位置和大小
                mainFrame = self.window().frame()
                
                # 計算控制面板的新位置和大小
                panelHeight = max(mainFrame.size.height, self.CONTROLS_PANEL_MIN_HEIGHT)
                panelX = mainFrame.origin.x + mainFrame.size.width + 10  # 10像素間距
                panelY = mainFrame.origin.y
                
                newPanelFrame = NSMakeRect(panelX, panelY, self.CONTROLS_PANEL_WIDTH, panelHeight)
                
                # 設定新的框架
                self.controlsPanelWindow.setFrame_display_(newPanelFrame, True)
                
                # 更新內容視圖的大小
                if self.controlsPanelView:
                    contentRect = NSMakeRect(0, 0, self.CONTROLS_PANEL_WIDTH, panelHeight)
                    self.controlsPanelView.setFrame_(contentRect)
                    self.controlsPanelView.setupUI()  # 重新佈局UI元件
                
        except Exception as e:
            print(f"更新控制面板位置時發生錯誤: {e}")
            print(traceback.format_exc())
    
    def controlsPanelAction_(self, sender):
        """控制面板按鈕動作"""
        try:
            # 切換控制面板可見性
            if self.controlsPanelVisible:
                self.hideControlsPanel()
            else:
                self.showControlsPanel()
                
        except Exception as e:
            print(f"控制面板按鈕動作時發生錯誤: {e}")
            print(traceback.format_exc())
    
    def windowDidResize_(self, notification):
        """
        視窗大小調整時的處理
        Handle window resize events
        
        Args:
            notification: 通知對象
        """
        try:
            if notification.object() == self.window():
                # 獲取新的視窗大小
                frame = self.window().frame()
                contentSize = self.window().contentView().frame().size
                
                print(f"九宮格視窗大小調整：新尺寸 {frame.size.width}x{frame.size.height}, 內容區域 {contentSize.width}x{contentSize.height}")
                
                # 調整預覽畫面大小以佔據整個內容區域
                if hasattr(self, 'previewView') and self.previewView:
                    self.previewView.setFrame_(NSMakeRect(0, 0, contentSize.width, contentSize.height))
                    # 觸發預覽畫面重繪以即時反映尺寸變更
                    self.previewView.setNeedsDisplay_(True)
                    print("已觸發預覽畫面重繪")
                
                # 更新控制面板的位置和大小
                if self.controlsPanelVisible:
                    self.updateControlsPanelPosition()
                
                # 儲存視窗大小 / Save the window size
                if hasattr(self, 'plugin'):
                    newSize = [frame.size.width, frame.size.height]
                    Glyphs.defaults[self.plugin.WINDOW_SIZE_KEY] = newSize
                
        except Exception as e:
            print(f"處理視窗大小調整時發生錯誤: {e}")
            print(traceback.format_exc())
    
    def windowDidMove_(self, notification):
        """
        視窗移動時的處理 - 子視窗跟隨移動
        Handle window move events - sub-window follows main window
        
        Args:
            notification: 通知對象
        """
        try:
            if notification.object() == self.window():
                print("九宮格主視窗移動，更新控制面板位置...")
                
                # 如果控制面板正在顯示，更新其位置
                if self.controlsPanelVisible and self.controlsPanelWindow:
                    self.updateControlsPanelPosition()
                    print("控制面板已跟隨主視窗移動")
                
        except Exception as e:
            print(f"處理視窗移動時發生錯誤: {e}")
            print(traceback.format_exc())
    
    def windowWillClose_(self, notification):
        """
        視窗關閉時的處理
        Handle window close events
        
        Args:
            notification: 通知對象
        """
        try:
            print("九宮格主視窗即將關閉...")
            
            # 保存控制面板當前的顯示狀態到偏好設定
            from constants import CONTROLS_PANEL_VISIBLE_KEY
            Glyphs.defaults[CONTROLS_PANEL_VISIBLE_KEY] = self.controlsPanelVisible
            print(f"已保存控制面板狀態: {self.controlsPanelVisible}")
            
            # 如果控制面板視窗存在且正在顯示，則關閉它
            if self.controlsPanelWindow:
                if self.controlsPanelVisible:
                    print("關閉控制面板視窗...")
                self.controlsPanelWindow.orderOut_(None)
            
            # 保存偏好設定 / Save preferences
            if hasattr(self, 'plugin'):
                self.plugin.savePreferences()
                
            # 移除通知觀察者 / Remove notification observers
            NSNotificationCenter.defaultCenter().removeObserver_(self)
            
        except Exception as e:
            print(f"處理視窗關閉時發生錯誤: {e}")
            print(traceback.format_exc())
    
    def request_main_redraw(self):
        """請求主預覽視圖重繪"""
        try:
            if hasattr(self, 'previewView') and self.previewView:
                self.previewView.setNeedsDisplay_(True)
        except Exception as e:
            print(f"請求主預覽重繪時發生錯誤: {e}")
            print(traceback.format_exc())
    
    def request_controls_panel_ui_update(self):
        """請求控制面板UI更新"""
        try:
            if hasattr(self, 'controlsPanelView') and self.controlsPanelView:
                self.controlsPanelView.update_ui(self.plugin)
        except Exception as e:
            print(f"請求控制面板UI更新時發生錯誤: {e}")
            print(traceback.format_exc())
    
    def redraw(self):
        """重繪介面（保持向後相容性）"""
        try:
            # 檢查是否應該更新預覽畫面
            should_update = True
            
            # 如果有控制面板視圖，檢查鎖頭狀態
            if (hasattr(self, 'controlsPanelView') and self.controlsPanelView and 
                hasattr(self.controlsPanelView, 'isInClearMode')):
                
                # 這裡可以添加額外的邏輯來決定是否更新
                # 目前保持簡單，總是允許更新
                pass
            
            if should_update:
                self.request_main_redraw()
                
        except Exception as e:
            print(f"重繪介面時發生錯誤: {e}")
            print(traceback.format_exc())
    
    def redrawIgnoreLockState(self):
        """強制重繪，忽略鎖頭狀態"""
        try:
            self.request_main_redraw()
        except Exception as e:
            print(f"強制重繪時發生錯誤: {e}")
            print(traceback.format_exc())
    
    def makeKeyAndOrderFront(self):
        """顯示並激活視窗"""
        try:
            print("九宮格視窗初次開啟...")
            
            # 顯示主視窗
            self.window().makeKeyAndOrderFront_(None)
            
            # 根據儲存的狀態決定是否顯示控制面板
            print(f"讀取到的控制面板狀態: {self.controlsPanelVisible}")
            if self.controlsPanelVisible:
                print("恢復控制面板顯示狀態...")
                self.showControlsPanel()
            
            # 初始化完成後更新介面，確保預覽畫面即時更新
            if hasattr(self, 'plugin'):
                self.plugin.updateInterface(None)
                
            # 強制重繪預覽畫面，確保初次開啟時內容即時顯示
            if hasattr(self, 'previewView') and self.previewView:
                self.previewView.setNeedsDisplay_(True)
                print("已觸發初次開啟時的預覽畫面重繪")
                
        except Exception as e:
            print(f"顯示視窗時發生錯誤: {e}")
            print(traceback.format_exc())
    
    def dealloc(self):
        """析構函數"""
        try:
            # 移除通知觀察者
            NSNotificationCenter.defaultCenter().removeObserver_(self)
            
            # 關閉控制面板視窗
            if hasattr(self, 'controlsPanelWindow') and self.controlsPanelWindow:
                self.controlsPanelWindow.orderOut_(None)
                
        except:
            pass
        objc.super(NineBoxWindow, self).dealloc()