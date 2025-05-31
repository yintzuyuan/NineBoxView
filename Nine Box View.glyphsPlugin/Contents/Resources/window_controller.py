# encoding: utf-8
"""
九宮格預覽外掛 - 視窗控制器（優化版）
Nine Box Preview Plugin - Window Controller (Optimized)
"""

from __future__ import division, print_function, unicode_literals
import traceback
import objc
from GlyphsApp import Glyphs
from AppKit import (
    NSWindowController, NSPanel, NSButton, NSMakeRect, NSMakeSize,
    NSWindow, NSNotificationCenter, NSWindowWillCloseNotification,
    NSWindowDidResizeNotification, NSWindowDidMoveNotification,
    NSTitledWindowMask, NSClosableWindowMask, NSResizableWindowMask,
    NSMiniaturizableWindowMask, NSFloatingWindowLevel,
    NSBackingStoreBuffered, NSTitlebarAccessoryViewController,
    NSView, NSViewMaxYMargin, NSLayoutAttributeRight,
    NSColor, NSButtonTypeToggle, NSButtonTypeMomentaryPushIn,
    NSBezelStyleRounded, NSTexturedRoundedBezelStyle,
    NSFocusRingTypeNone, NSWindowCloseButton,
    NSWindowMiniaturizeButton, NSWindowZoomButton
)
from Foundation import NSObject

from constants import (
    WINDOW_SIZE_KEY, DEFAULT_WINDOW_SIZE, MIN_WINDOW_SIZE,
    CONTROLS_PANEL_WIDTH, CONTROLS_PANEL_MIN_HEIGHT,
    CONTROLS_PANEL_VISIBLE_KEY, DEBUG_MODE
)
from utils import debug_log


class NineBoxWindow(NSWindowController):
    """
    九宮格預覽視窗控制器（優化版）
    Nine Box Window Controller (Optimized)
    """
    
    def initWithPlugin_(self, plugin):
        """初始化視窗控制器（階段1.1基礎版）"""
        try:
            # 動態導入以避免循環依賴
            from preview_view import NineBoxPreviewView
            # === 階段1.1：暫時不導入控制面板 ===
            # from controls_panel_view import ControlsPanelView
            self.NineBoxPreviewView = NineBoxPreviewView
            # self.ControlsPanelView = ControlsPanelView
            
            # 確保偏好設定已載入
            plugin.loadPreferences()
            
            # 載入視窗大小
            savedSize = Glyphs.defaults.get(WINDOW_SIZE_KEY, DEFAULT_WINDOW_SIZE)
            
            # 建立主視窗
            windowRect = NSMakeRect(0, 0, savedSize[0], savedSize[1])
            styleMask = (NSTitledWindowMask | NSClosableWindowMask | 
                        NSResizableWindowMask | NSMiniaturizableWindowMask)
            
            panel = NSPanel.alloc().initWithContentRect_styleMask_backing_defer_(
                windowRect, styleMask, NSBackingStoreBuffered, False
            )
            
            panel.setTitle_(plugin.name)
            panel.setMinSize_(NSMakeSize(MIN_WINDOW_SIZE[0], MIN_WINDOW_SIZE[1]))
            panel.setLevel_(NSFloatingWindowLevel)
            panel.setReleasedWhenClosed_(False)
            
            # 初始化父類
            self = objc.super(NineBoxWindow, self).init()
            
            if self:
                # 設置屬性
                self.setWindow_(panel)
                self.plugin = plugin
                self.previewView = None
                
                # === 階段1.1：暫時停用控制面板相關屬性 ===
                self.controlsPanelButton = None
                self.controlsPanelWindow = None
                self.controlsPanelView = None
                self.controlsPanelVisible = False  # 暫時設為False
                
                # 初始化UI（僅設定主視窗）
                self._setup_main_window_ui(panel)
                
                # === 階段1.1：暫時停用控制面板初始化 ===
                # self._setup_controls_panel()
                
                self._register_notifications(panel)
                
                # === 階段1.1：不顯示控制面板 ===
                # if self.controlsPanelVisible:
                #     self.showControlsPanel()
                
                debug_log("[階段1.1] 主視窗初始化完成")
            
            return self
            
        except Exception as e:
            print(f"[階段1.1] 初始化視窗控制器錯誤: {e}")
            if DEBUG_MODE:
                print(traceback.format_exc())
            return None
    
    def _setup_main_window_ui(self, panel):
        """設定主視窗UI（階段1.1基礎版）"""
        contentView = panel.contentView()
        
        # 建立預覽畫面
        previewRect = NSMakeRect(0, 0, panel.frame().size.width, panel.frame().size.height)
        self.previewView = self.NineBoxPreviewView.alloc().initWithFrame_plugin_(previewRect, self.plugin)
        contentView.addSubview_(self.previewView)
        
        # 調整預覽畫面大小
        actualContentSize = contentView.frame().size
        self.previewView.setFrame_(NSMakeRect(0, 0, actualContentSize.width, actualContentSize.height))
        self.previewView.setNeedsDisplay_(True)
        
        # === 階段1.1：暫時不建立控制面板按鈕 ===
        # self._create_controls_panel_button(panel)
        
        debug_log(f"[階段1.1] 預覽視圖初始化完成，尺寸：{actualContentSize.width}x{actualContentSize.height}")
    
    def _create_controls_panel_button(self, panel):
        """創建控制面板按鈕"""
        self.controlsPanelButton = NSButton.alloc().init()
        self.controlsPanelButton.setTitle_("⚙")
        self.controlsPanelButton.setTarget_(self)
        self.controlsPanelButton.setAction_("controlsPanelAction:")
        self.controlsPanelButton.setBezelStyle_(NSTexturedRoundedBezelStyle)
        self.controlsPanelButton.setButtonType_(NSButtonTypeToggle)
        
        # 設定提示
        controlsPanelTooltip = Glyphs.localize({
            'en': u'Show/hide controls panel',
            'zh-Hant': u'顯示/隱藏控制面板',
            'zh-Hans': u'显示/隐藏控制面板',
            'ja': u'コントロールパネルを表示/非表示',
            'ko': u'컨트롤 패널 표시/숨기기',
        })
        self.controlsPanelButton.setToolTip_(controlsPanelTooltip)
        
        # 設定按鈕狀態
        self.controlsPanelButton.setState_(1 if self.controlsPanelVisible else 0)
        
        # 創建容器視圖
        buttonView = NSView.alloc().initWithFrame_(NSMakeRect(0, 0, 30, 24))
        buttonView.addSubview_(self.controlsPanelButton)
        self.controlsPanelButton.setFrame_(NSMakeRect(0, 0, 30, 24))
        
        # 創建標題列附件控制器
        accessoryController = NSTitlebarAccessoryViewController.alloc().init()
        accessoryController.setView_(buttonView)
        accessoryController.setLayoutAttribute_(NSLayoutAttributeRight)
        
        # 添加到視窗
        panel.addTitlebarAccessoryViewController_(accessoryController)
    
    def _setup_controls_panel(self):
        """設定控制面板"""
        self.createControlsPanelWindow()
    
    def _register_notifications(self, panel):
        """註冊通知監聽"""
        notificationCenter = NSNotificationCenter.defaultCenter()
        
        # 視窗大小調整
        notificationCenter.addObserver_selector_name_object_(
            self, "windowDidResize:", NSWindowDidResizeNotification, panel
        )
        
        # 視窗移動
        notificationCenter.addObserver_selector_name_object_(
            self, "windowDidMove:", NSWindowDidMoveNotification, panel
        )
        
        # 視窗關閉
        notificationCenter.addObserver_selector_name_object_(
            self, "windowWillClose:", NSWindowWillCloseNotification, panel
        )
    
    def createControlsPanelWindow(self):
        """創建控制面板子視窗"""
        try:
            # 計算位置和大小
            mainFrame = self.window().frame()
            panelHeight = max(mainFrame.size.height, CONTROLS_PANEL_MIN_HEIGHT)
            panelX = mainFrame.origin.x + mainFrame.size.width + 10
            panelY = mainFrame.origin.y
            
            panelRect = NSMakeRect(panelX, panelY, CONTROLS_PANEL_WIDTH, panelHeight)
            
            # 創建面板
            self.controlsPanelWindow = NSPanel.alloc().initWithContentRect_styleMask_backing_defer_(
                panelRect,
                NSTitledWindowMask | NSClosableWindowMask,
                NSBackingStoreBuffered,
                False
            )
            
            # 設定面板屬性
            self._configure_controls_panel_window()
            
            # 創建控制面板視圖
            contentRect = NSMakeRect(0, 0, CONTROLS_PANEL_WIDTH, panelHeight)
            self.controlsPanelView = self.ControlsPanelView.alloc().initWithFrame_plugin_(
                contentRect, self.plugin
            )
            
            # 設定內容視圖
            self.controlsPanelWindow.setContentView_(self.controlsPanelView)
            
        except Exception as e:
            print(f"創建控制面板視窗錯誤: {e}")
            if DEBUG_MODE:
                print(traceback.format_exc())
    
    def _configure_controls_panel_window(self):
        """配置控制面板視窗屬性"""
        panel = self.controlsPanelWindow
        
        panel.setTitle_("Controls")
        panel.setLevel_(NSFloatingWindowLevel)
        panel.setReleasedWhenClosed_(False)
        panel.setHidesOnDeactivate_(False)
        panel.setFloatingPanel_(True)
        panel.setBackgroundColor_(NSColor.controlBackgroundColor())
        
        # 隱藏標題列按鈕
        panel.standardWindowButton_(NSWindowCloseButton).setHidden_(True)
        panel.standardWindowButton_(NSWindowMiniaturizeButton).setHidden_(True)
        panel.standardWindowButton_(NSWindowZoomButton).setHidden_(True)
        
        # 透明標題列
        panel.setTitlebarAppearsTransparent_(True)
        panel.setTitleVisibility_(1)  # NSWindowTitleHidden
    
    def showControlsPanel(self):
        """顯示控制面板"""
        try:
            if self.controlsPanelWindow:
                self.updateControlsPanelPosition()
                self.controlsPanelWindow.orderFront_(None)
                
                if self.controlsPanelView:
                    self.controlsPanelView.update_ui(self.plugin)
                
                self.controlsPanelVisible = True
                self.controlsPanelButton.setState_(1)
                
                Glyphs.defaults[CONTROLS_PANEL_VISIBLE_KEY] = True
                
        except Exception as e:
            debug_log(f"顯示控制面板錯誤: {e}")
    
    def hideControlsPanel(self):
        """隱藏控制面板"""
        try:
            if self.controlsPanelWindow:
                self.controlsPanelWindow.orderOut_(None)
                
                self.controlsPanelVisible = False
                self.controlsPanelButton.setState_(0)
                
                Glyphs.defaults[CONTROLS_PANEL_VISIBLE_KEY] = False
                
        except Exception as e:
            debug_log(f"隱藏控制面板錯誤: {e}")
    
    def updateControlsPanelPosition(self):
        """更新控制面板位置"""
        try:
            if self.controlsPanelWindow:
                mainFrame = self.window().frame()
                
                panelHeight = max(mainFrame.size.height, CONTROLS_PANEL_MIN_HEIGHT)
                panelX = mainFrame.origin.x + mainFrame.size.width + 10
                panelY = mainFrame.origin.y
                
                newPanelFrame = NSMakeRect(panelX, panelY, CONTROLS_PANEL_WIDTH, panelHeight)
                self.controlsPanelWindow.setFrame_display_(newPanelFrame, True)
                
                if self.controlsPanelView:
                    contentRect = NSMakeRect(0, 0, CONTROLS_PANEL_WIDTH, panelHeight)
                    self.controlsPanelView.setFrame_(contentRect)
                    self.controlsPanelView.setupUI()
                
        except Exception as e:
            debug_log(f"更新控制面板位置錯誤: {e}")
    
    def controlsPanelAction_(self, sender):
        """控制面板按鈕動作"""
        try:
            if self.controlsPanelVisible:
                self.hideControlsPanel()
            else:
                self.showControlsPanel()
                
        except Exception as e:
            debug_log(f"控制面板按鈕動作錯誤: {e}")
    
    def windowDidResize_(self, notification):
        """視窗大小調整處理（階段1.1基礎版）"""
        try:
            if notification.object() == self.window():
                frame = self.window().frame()
                contentSize = self.window().contentView().frame().size
                
                debug_log(f"[階段1.1] 視窗調整：{frame.size.width}x{frame.size.height}")
                
                # 調整預覽畫面
                if hasattr(self, 'previewView') and self.previewView:
                    self.previewView.setFrame_(NSMakeRect(0, 0, contentSize.width, contentSize.height))
                    
                    # 立即觸發重繪確保畫面即時更新
                    if hasattr(self.previewView, 'force_redraw'):
                        self.previewView.force_redraw()
                    else:
                        self.previewView.setNeedsDisplay_(True)
                    
                    debug_log(f"[階段1.1] 已調整預覽視圖尺寸並觸發重繪")
                
                # === 階段1.1：暫時停用控制面板更新 ===
                # if self.controlsPanelVisible:
                #     self.updateControlsPanelPosition()
                
                # 儲存視窗大小
                if hasattr(self, 'plugin'):
                    newSize = [frame.size.width, frame.size.height]
                    Glyphs.defaults[WINDOW_SIZE_KEY] = newSize
                
        except Exception as e:
            debug_log(f"[階段1.1] 處理視窗調整錯誤: {e}")
    
    def windowDidMove_(self, notification):
        """視窗移動處理"""
        try:
            if notification.object() == self.window():
                if self.controlsPanelVisible and self.controlsPanelWindow:
                    self.updateControlsPanelPosition()
                    
        except Exception as e:
            debug_log(f"處理視窗移動錯誤: {e}")
    
    def windowWillClose_(self, notification):
        """視窗關閉處理"""
        try:
            debug_log("主視窗即將關閉")
            
            # 保存狀態
            Glyphs.defaults[CONTROLS_PANEL_VISIBLE_KEY] = self.controlsPanelVisible
            
            # 關閉控制面板
            if self.controlsPanelWindow:
                self.controlsPanelWindow.orderOut_(None)
            
            # 保存偏好設定
            if hasattr(self, 'plugin'):
                self.plugin.savePreferences()
            
            # 移除通知觀察者
            NSNotificationCenter.defaultCenter().removeObserver_(self)
            
        except Exception as e:
            debug_log(f"處理視窗關閉錯誤: {e}")
    
    def request_main_redraw(self):
        """請求主預覽視圖重繪"""
        try:
            if hasattr(self, 'previewView') and self.previewView:
                # 使用強制重繪機制（如果存在）
                if hasattr(self.previewView, 'force_redraw'):
                    self.previewView.force_redraw()
                else:
                    self.previewView.setNeedsDisplay_(True)
        except Exception as e:
            debug_log(f"請求主預覽重繪錯誤: {e}")
    
    def request_controls_panel_ui_update(self):
        """請求控制面板UI更新"""
        try:
            if self.controlsPanelView and self.controlsPanelVisible:
                self.controlsPanelView.update_ui(self.plugin)
                debug_log("已更新控制面板 UI")
                    
        except Exception as e:
            debug_log(f"請求控制面板UI更新錯誤: {e}")
    
    def redraw(self):
        """重繪介面（向後相容）"""
        self.request_main_redraw()
    
    def redrawIgnoreLockState(self):
        """強制重繪"""
        self.request_main_redraw()
    
    def makeKeyAndOrderFront(self):
        """顯示並激活視窗（階段1.1基礎版）"""
        try:
            debug_log("[階段1.1] 初次開啟視窗")
            
            # 顯示主視窗
            self.window().makeKeyAndOrderFront_(None)
            
            # === 階段1.1：暫時停用控制面板 ===
            # if self.controlsPanelVisible:
            #     self.showControlsPanel()
            #     if self.controlsPanelView:
            #         self.controlsPanelView.update_ui(self.plugin)
            
            # 更新介面
            if hasattr(self, 'plugin'):
                self.plugin.updateInterface(None)
            
            # 強制重繪確保初次顯示
            if hasattr(self, 'previewView') and self.previewView:
                if hasattr(self.previewView, 'force_redraw'):
                    self.previewView.force_redraw()
                else:
                    self.previewView.setNeedsDisplay_(True)
                
                debug_log(f"[階段1.1] 已觸發預覽視圖重繪")
                
        except Exception as e:
            debug_log(f"[階段1.1] 顯示視窗錯誤: {e}")
    
    def dealloc(self):
        """析構函數"""
        try:
            NSNotificationCenter.defaultCenter().removeObserver_(self)
            
            if hasattr(self, 'controlsPanelWindow') and self.controlsPanelWindow:
                self.controlsPanelWindow.orderOut_(None)
                
        except:
            pass
        objc.super(NineBoxWindow, self).dealloc()