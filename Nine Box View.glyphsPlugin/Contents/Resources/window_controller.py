# encoding: utf-8
"""
九宮格預覽外掛 - 視窗控制器（最佳化版）
Nine Box Preview Plugin - Window Controller (Optimized)
"""

from __future__ import division, print_function, unicode_literals
import traceback
import objc
from GlyphsApp import Glyphs
from AppKit import (
    NSWindowController, NSPanel, NSButton, NSMakeRect, NSMakeSize, NSMakePoint,
    NSWindow, NSNotificationCenter, NSWindowWillCloseNotification,
    NSWindowDidResizeNotification, NSWindowDidMoveNotification,
    NSTitledWindowMask, NSClosableWindowMask, NSResizableWindowMask,
    NSMiniaturizableWindowMask, NSFloatingWindowLevel, NSFullSizeContentViewWindowMask,
    NSBackingStoreBuffered, NSTitlebarAccessoryViewController,
    NSView, NSViewMaxYMargin, NSLayoutAttributeRight,
    NSColor, NSButtonTypeToggle, NSButtonTypeMomentaryPushIn, NSFont,
    NSAttributedString, NSFontAttributeName, NSForegroundColorAttributeName,
    NSBezelStyleRounded, NSTexturedRoundedBezelStyle,
    NSWindowCloseButton,
    NSWindowMiniaturizeButton, NSWindowZoomButton, NSUserDefaults
)
from Foundation import NSObject, NSUserDefaultsDidChangeNotification, NSTimer

from constants import (
    WINDOW_SIZE_KEY, DEFAULT_WINDOW_SIZE, MIN_WINDOW_SIZE,
    CONTROLS_PANEL_WIDTH, CONTROLS_PANEL_MIN_HEIGHT, CONTROLS_PANEL_SPACING,
    CONTROLS_PANEL_VISIBLE_KEY, DEBUG_MODE
)
from utils import debug_log, error_log


class NineBoxWindow(NSWindowController):
    """
    九宮格預覽視窗控制器（最佳化版）
    Nine Box Window Controller (Optimized)
    """
    
    def initWithPlugin_(self, plugin):
        """初始化視窗控制器（階段1.2：加入控制面板）"""
        try:
            # 動態匯入以避免反覆依賴
            from preview_view import NineBoxPreviewView
            from controls_panel_view import ControlsPanelView
            self.NineBoxPreviewView = NineBoxPreviewView
            self.ControlsPanelView = ControlsPanelView
            # 不再需要 NSArray，因為我們統一使用 Python list
            
            # 確保偏好設定已載入 (由 NineBoxView.toggleWindow_ 處理)
            # plugin.loadPreferences() # Removed: Preferences should be loaded by the caller (NineBoxView)
            debug_log(f"WC initWithPlugin_: plugin.controlsPanelVisible BEFORE assignment = {plugin.controlsPanelVisible} (type: {type(plugin.controlsPanelVisible)})")
            self.controlsPanelVisible = plugin.controlsPanelVisible # plugin.loadPreferences() 已經載入
            debug_log(f"WC initWithPlugin_: self.controlsPanelVisible AFTER assignment = {self.controlsPanelVisible} (type: {type(self.controlsPanelVisible)})")
            
            # 載入視窗大小
            savedSize = plugin.windowSize
            
            # 載入視窗位置
            savedPosition = plugin.windowPosition # plugin.loadPreferences() 已經載入
            debug_log(f"window_controller.initWithPlugin_: Received savedPosition from plugin: {savedPosition} (type: {type(savedPosition)})")
            
            # 建立主視窗
            windowRect = NSMakeRect(0, 0, savedSize[0], savedSize[1])
            styleMask = (NSTitledWindowMask | NSClosableWindowMask |
                        NSResizableWindowMask | NSMiniaturizableWindowMask | NSFullSizeContentViewWindowMask)
            
            panel = NSPanel.alloc().initWithContentRect_styleMask_backing_defer_(
                windowRect, styleMask, NSBackingStoreBuffered, False
            )
            
            panel.setTitle_(plugin.name)
            panel.setMinSize_(NSMakeSize(MIN_WINDOW_SIZE[0], MIN_WINDOW_SIZE[1]))
            panel.setLevel_(NSFloatingWindowLevel)
            panel.setReleasedWhenClosed_(False)
            
            # 設定標題列透明以移除背景bar
            panel.setTitlebarAppearsTransparent_(True)
            
            # 初始化父類別
            self = objc.super(NineBoxWindow, self).init()
            
            if self:
                # 設定屬性
                self.setWindow_(panel)
                self.plugin = plugin
                self.previewView = None
                
                # 控制面板相關屬性
                self.controlsPanelButton = None
                self.controlsPanelWindow = None
                self.controlsPanelView = None
                
                # 初始化UI（僅設定主視窗）
                self._setup_main_window_ui(panel)
                
                # 初始化控制面板
                self._setup_controls_panel()
                
                self._register_notifications(panel)
                
                # 根據偏好設定顯示控制面板
                if self.controlsPanelVisible: # 根據記錄，重置後此處為 False
                    self.showControlsPanel()
                else:
                    # 明確隱藏控制面板，因為子視窗預設會隨父視窗顯示
                    if self.controlsPanelWindow:
                        self.controlsPanelWindow.orderOut_(None)
                        debug_log("WC initWithPlugin_: Explicitly ordered out controlsPanelWindow as controlsPanelVisible is False.")
                    
                # 設定視窗位置
                debug_log(f"window_controller.initWithPlugin_: Checking savedPosition '{savedPosition}' before applying.")
                if savedPosition:
                    # 處理 NSArray、list 或 tuple
                    try:
                        if len(savedPosition) >= 2:
                            x = float(savedPosition[0])
                            y = float(savedPosition[1])
                            debug_log(f"window_controller.initWithPlugin_: Attempting to set panel origin to ({x}, {y})")
                            panel.setFrameOrigin_(NSMakePoint(x, y))
                            debug_log(f"window_controller.initWithPlugin_: Panel origin set to {panel.frame().origin.x}, {panel.frame().origin.y}")
                        else:
                            debug_log(f"window_controller.initWithPlugin_: savedPosition 長度不足: {len(savedPosition)}")
                    except (ValueError, TypeError, IndexError) as e:
                        debug_log(f"window_controller.initWithPlugin_: Error setting panel origin: {e}. savedPosition was: {savedPosition}")
                else:
                    debug_log(f"window_controller.initWithPlugin_: Not applying savedPosition. Value: {savedPosition}")

                debug_log("window_controller.initWithPlugin_: 主視窗和控制面板初始化完成")
            
            return self
            
        except Exception as e:
            error_log("window_controller.initWithPlugin_: 初始化視窗控制器錯誤", e)
            return None
    
    def _setup_main_window_ui(self, panel):
        """設定主視窗UI（階段1.2：加入控制面板按鈕）"""
        contentView = panel.contentView()
        
        # 建立預覽畫面
        previewRect = NSMakeRect(0, 0, panel.frame().size.width, panel.frame().size.height)
        self.previewView = self.NineBoxPreviewView.alloc().initWithFrame_plugin_(previewRect, self.plugin)
        contentView.addSubview_(self.previewView)
        
        # 調整預覽畫面大小
        actualContentSize = contentView.frame().size
        self.previewView.setFrame_(NSMakeRect(0, 0, actualContentSize.width, actualContentSize.height))
        self.previewView.setNeedsDisplay_(True)
        
        # 建立控制面板按鈕
        self._create_controls_panel_button(panel)
        
        debug_log(f"[階段1.2] 預覽畫面和控制按鈕初始化完成，尺寸：{actualContentSize.width}x{actualContentSize.height}")
    
    def _create_controls_panel_button(self, panel):
        """建立控制面板按鈕"""
        self.controlsPanelButton = NSButton.alloc().init()
        self.controlsPanelButton.setTitle_("⚙")
        self.controlsPanelButton.setTarget_(self)
        self.controlsPanelButton.setAction_("controlsPanelAction:")
        self.controlsPanelButton.setBezelStyle_(NSTexturedRoundedBezelStyle)
        self.controlsPanelButton.setButtonType_(NSButtonTypeToggle)
        
        # 設定按鈕圖示顏色，使其能隨 Glyphs 預覽主題自動調整
        self._update_settings_button_color()
        
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
        
        # 建立容器畫面
        buttonView = NSView.alloc().initWithFrame_(NSMakeRect(0, 0, 30, 24))
        buttonView.addSubview_(self.controlsPanelButton)
        self.controlsPanelButton.setFrame_(NSMakeRect(0, 0, 30, 24))
        
        # 建立標題列附件控制器
        accessoryController = NSTitlebarAccessoryViewController.alloc().init()
        accessoryController.setView_(buttonView)
        accessoryController.setLayoutAttribute_(NSLayoutAttributeRight)
        
        # 新增到視窗
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
        
        # 監聽用戶偏好設定變更（用於更新按鈕顏色以配對 Glyphs 預覽主題）
        notificationCenter.addObserver_selector_name_object_(
            self, "_handleUserDefaultsChange:", NSUserDefaultsDidChangeNotification, None
        )
    
    def createControlsPanelWindow(self):
        """建立控制面板子視窗"""
        try:
            # 計算位置和大小
            mainFrame = self.window().frame()
            panelHeight = max(mainFrame.size.height, CONTROLS_PANEL_MIN_HEIGHT)
            panelX = mainFrame.origin.x + mainFrame.size.width + CONTROLS_PANEL_SPACING
            panelY = mainFrame.origin.y
            
            panelRect = NSMakeRect(panelX, panelY, CONTROLS_PANEL_WIDTH, panelHeight)
            
            # 建立面板
            self.controlsPanelWindow = NSPanel.alloc().initWithContentRect_styleMask_backing_defer_(
                panelRect,
                NSTitledWindowMask | NSClosableWindowMask,
                NSBackingStoreBuffered,
                False
            )
            
            # 設定面板屬性
            self._configure_controls_panel_window()
            
            # 建立控制面板畫面
            contentRect = NSMakeRect(0, 0, CONTROLS_PANEL_WIDTH, panelHeight)
            self.controlsPanelView = self.ControlsPanelView.alloc().initWithFrame_plugin_(
                contentRect, self.plugin
            )
            
            # 設定內容畫面
            self.controlsPanelWindow.setContentView_(self.controlsPanelView)
            
            # === 階段2.2：初始化時載入已儲存的鎖定字符 ===
            if self.controlsPanelView and self.plugin:
                self.controlsPanelView.update_ui(self.plugin)
                debug_log("[階段2.2] 控制面板初始化後載入已儲存的資料")
            
        except Exception as e:
            error_log("建立控制面板視窗錯誤", e)
    
    def _configure_controls_panel_window(self):
        """設定控制面板視窗屬性（統一子視窗模式）"""
        panel = self.controlsPanelWindow
        
        panel.setTitle_("Controls")
        # 完全移除舊的浮動視窗模式，統一使用子視窗模式
        panel.setReleasedWhenClosed_(False)
        
        panel.setBackgroundColor_(NSColor.controlBackgroundColor())
        
        # 隱藏標題列按鈕
        panel.standardWindowButton_(NSWindowCloseButton).setHidden_(True)
        panel.standardWindowButton_(NSWindowMiniaturizeButton).setHidden_(True)
        panel.standardWindowButton_(NSWindowZoomButton).setHidden_(True)
        
        # 透明標題列
        panel.setTitlebarAppearsTransparent_(True)
        panel.setTitleVisibility_(1)  # NSWindowTitleHidden
        
        # 設定視窗行為，使其與主視窗一起移動和管理焦點
        # NSWindowCollectionBehaviorMoveToActiveSpace = 1 << 1
        # NSWindowCollectionBehaviorTransient = 1 << 3
        panel.setCollectionBehavior_(1 << 1 | 1 << 3)
        
        # 確保建立子視窗關係（核心改進）
        self._ensure_child_window_relationship()
    
    def showControlsPanel(self):
        """顯示控制面板（統一子視窗模式）"""
        try:
            if self.controlsPanelWindow:
                self.updateControlsPanelPosition()
                
                # 確保子視窗關係正確（核心改進）
                self._ensure_child_window_relationship()
                
                # 顯示控制面板（作為子視窗會自動跟隨主視窗）
                self.controlsPanelWindow.orderFront_(None)
                
                if self.controlsPanelView:
                    self.controlsPanelView.update_ui(self.plugin)
                
                self.controlsPanelVisible = True
                self.controlsPanelButton.setState_(1)
                
                # 更新外掛程式對象屬性
                if hasattr(self, 'plugin'):
                    self.plugin.controlsPanelVisible = True
                
                # Glyphs.defaults[CONTROLS_PANEL_VISIBLE_KEY] = True # 由 plugin.savePreferences() 處理
                self.plugin.savePreferences() # 即時儲存狀態
                debug_log("控制面板已顯示，子視窗關係已確保")
                
        except Exception as e:
            error_log("顯示控制面板錯誤", e)
    
    def hideControlsPanel(self):
        """隱藏控制面板"""
        try:
            if self.controlsPanelWindow:
                self.controlsPanelWindow.orderOut_(None)
                
                self.controlsPanelVisible = False
                self.controlsPanelButton.setState_(0)
                
                # 更新外掛程式對象屬性
                if hasattr(self, 'plugin'):
                    self.plugin.controlsPanelVisible = False
                
                # Glyphs.defaults[CONTROLS_PANEL_VISIBLE_KEY] = False # 由 plugin.savePreferences() 處理
                self.plugin.savePreferences() # 即時儲存狀態
                
        except Exception as e:
            error_log("隱藏控制面板錯誤", e)
    
    def updateControlsPanelPosition(self):
        """更新控制面板位置（階段1.3：考慮最小高度）"""
        try:
            if self.controlsPanelWindow and self.controlsPanelView:
                # 取得主視窗框架
                mainFrame = self.window().frame()
                
                # 計算控制面板高度（保持與主視窗相同高度，但不低於最小高度）
                panelHeight = max(mainFrame.size.height, CONTROLS_PANEL_MIN_HEIGHT)
                
                # 計算控制面板位置（靠右對齊主視窗）
                panelX = mainFrame.origin.x + mainFrame.size.width + CONTROLS_PANEL_SPACING
                panelY = mainFrame.origin.y
                
                # 設定控制面板位置和大小
                panelFrame = self.controlsPanelWindow.frame()
                newFrame = NSMakeRect(
                    panelX, panelY, 
                    CONTROLS_PANEL_WIDTH, panelHeight
                )
                
                # 僅在需要時更新
                if (panelFrame.size.width != newFrame.size.width or
                    panelFrame.size.height != newFrame.size.height or
                    panelFrame.origin.x != newFrame.origin.x or
                    panelFrame.origin.y != newFrame.origin.y):
                    self.controlsPanelWindow.setFrame_display_animate_(newFrame, True, False) # 修改此處，將動畫關閉
                    
                    # 同時更新內容畫面大小
                    self.controlsPanelView.setFrame_(NSMakeRect(
                        0, 0, CONTROLS_PANEL_WIDTH, panelHeight
                    ))
                    
                    debug_log(f"[階段1.3] 更新控制面板位置：({panelX}, {panelY}) 大小：{CONTROLS_PANEL_WIDTH}x{panelHeight}")
                
        except Exception as e:
            error_log("[階段1.3] 更新控制面板位置錯誤", e)
    
    def controlsPanelAction_(self, sender):
        """控制面板按鈕動作（統一子視窗模式）"""
        try:
            if self.controlsPanelVisible:
                self.hideControlsPanel()
            else:
                # 確保重建並正確建立子視窗關係
                if not self.controlsPanelWindow:
                    self._setup_controls_panel()
                self.showControlsPanel()
                
        except Exception as e:
            error_log("控制面板按鈕動作錯誤", e)
    
    def windowDidResize_(self, notification):
        """視窗大小調整處理（階段1.3：最佳化版）"""
        try:
            if notification.object() == self.window():
                frame = self.window().frame()
                contentView = self.window().contentView()
                contentSize = contentView.frame().size
                
                debug_log(f"[階段1.3] 視窗調整：{frame.size.width}x{frame.size.height}，內容區域：{contentSize.width}x{contentSize.height}")
                
                # 調整預覽畫面 - 確保完全填滿內容區域（官方模式）
                if hasattr(self, 'previewView') and self.previewView:
                    # 使用內容畫面的實際邊界
                    newFrame = contentView.bounds()
                    self.previewView.setFrame_(newFrame)
                    
                    # 官方模式：框架變更會自動觸發重繪
                    debug_log(f"[官方模式] 已調整預覽畫面框架：{newFrame.size.width}x{newFrame.size.height} at ({newFrame.origin.x}, {newFrame.origin.y})")
                
                # 更新控制面板位置和大小
                if self.controlsPanelVisible and self.controlsPanelWindow:
                    self.updateControlsPanelPosition()
                    # 確保子視窗關係（核心改進）
                    self._ensure_child_window_relationship()
                    debug_log("已更新控制面板位置和大小，確保子視窗關係")
                
                # 儲存視窗大小
                if hasattr(self, 'plugin'):
                    newSize = [frame.size.width, frame.size.height]
                    self.plugin.windowSize = newSize
                    self.plugin.savePreferences() # 即時儲存狀態
                    debug_log(f"[階段1.3] 已更新外掛程式 windowSize 屬性並儲存：{newSize}")
                
        except Exception as e:
            error_log("[階段1.3] 處理視窗調整錯誤", e)
    
    def windowDidMove_(self, notification):
        """視窗移動處理（統一子視窗模式）"""
        try:
            if notification.object() == self.window():
                mainFrame = self.window().frame()
                current_origin_x = mainFrame.origin.x
                current_origin_y = mainFrame.origin.y
                
                # 儲存視窗位置
                if hasattr(self, 'plugin'):
                    try:
                        x = float(current_origin_x)
                        y = float(current_origin_y)
                        new_position_to_store = [x, y]
                        self.plugin.windowPosition = new_position_to_store
                        self.plugin.savePreferences() # 即時儲存狀態
                        debug_log(f"window_controller.windowDidMove_: Updated plugin.windowPosition and saved: {self.plugin.windowPosition}")                        
                        debug_log(f"window_controller.windowDidMove_: Saved windowPosition to Glyphs.defaults: {Glyphs.defaults.get(self.plugin.WINDOW_POSITION_KEY if hasattr(self.plugin, 'WINDOW_POSITION_KEY') else 'UNKNOWN_KEY')}")
                    except Exception as e:
                        debug_log(f"window_controller.windowDidMove_: Error saving windowPosition to Glyphs.defaults: {e}")
                
                if self.controlsPanelVisible and self.controlsPanelWindow:
                    self.updateControlsPanelPosition()
                    # 確保子視窗關係（核心改進）
                    self._ensure_child_window_relationship()
                    
        except Exception as e:
            error_log("window_controller.windowDidMove_: Error in windowDidMove", e)
    
    def windowWillClose_(self, notification):
        """視窗關閉處理（階段1.3：完整資源釋放）"""
        try:
            debug_log("[階段1.3] 主視窗即將關閉")
            
            # === 保存最終顯示狀態 ===
            if hasattr(self, 'plugin') and self.plugin:
                # 保存當前排列為最終狀態
                if hasattr(self.plugin, 'currentArrangement') and self.plugin.currentArrangement:
                    self.plugin.finalArrangement = list(self.plugin.currentArrangement)
                    debug_log(f"[關閉保存] 保存最終狀態: {self.plugin.finalArrangement}")
            
            # 儲存狀態到外掛程式對象
            if hasattr(self, 'plugin'):
                self.plugin.controlsPanelVisible = self.controlsPanelVisible
                # Glyphs.defaults[CONTROLS_PANEL_VISIBLE_KEY] = self.controlsPanelVisible # 由下面的 savePreferences 處理
            
            # 完整釋放控制面板資源
            if self.controlsPanelWindow:
                debug_log("[階段1.3] 釋放控制面板資源")
                # 先從主視窗移除子視窗關係
                self.window().removeChildWindow_(self.controlsPanelWindow)
                self.controlsPanelWindow.orderOut_(None)
                if self.controlsPanelView:
                    self.controlsPanelView = None
                self.controlsPanelWindow.close()
                self.controlsPanelWindow = None
            
            # 儲存偏好設定
            if hasattr(self, 'plugin'):
                self.plugin.savePreferences()
            
            # 移除通知觀察者
            NSNotificationCenter.defaultCenter().removeObserver_(self)
            
            # 清除視窗控制器引用
            if hasattr(self, 'plugin') and hasattr(self.plugin, 'windowController'):
                self.plugin.windowController = None
            
        except Exception as e:
            error_log("[階段1.3] 處理視窗關閉錯誤", e)
    
    def update(self):
        """標準更新方法（遵循官方 CanvasView 模式）- 增強型"""
        try:
            if hasattr(self, 'previewView') and self.previewView:
                # 更新屬性設定器 (從 plugin 同步)
                if hasattr(self, 'plugin'):
                    if hasattr(self.plugin, 'currentArrangement'):
                        self.previewView.currentArrangement = self.plugin.currentArrangement
                    if hasattr(self.plugin, 'zoomFactor'):
                        self.previewView.zoomFactor = self.plugin.zoomFactor
                
                # 調用官方更新方法
                self.previewView.update()
                
                # 強制立即重繪 (確保即時反應)
                self.previewView.setNeedsDisplay_(True)
                debug_log("window_controller.update: 已觸發強制重繪")
        except Exception as e:
            error_log("更新主預覽錯誤", e)
    
    def request_controls_panel_ui_update(self, update_lock_fields=True):
        """請求控制面板UI更新
        
        Args:
            update_lock_fields: 是否更新鎖定輸入框（預設True）
        """
        try:
            if self.controlsPanelView and self.controlsPanelVisible:
                self.controlsPanelView.update_ui(self.plugin, update_lock_fields)
                debug_log(f"已更新控制面板 UI，update_lock_fields={update_lock_fields}")
                    
        except Exception as e:
            error_log("請求控制面板UI更新錯誤", e)
    
    def makeKeyAndOrderFront(self):
        """顯示並激活視窗（完整初始化版本）"""
        try:
            debug_log("[makeKeyAndOrderFront] 開始完整初始化")
            
            if hasattr(self, 'plugin'):
                # 確保偏好設定已載入 (由 NineBoxView.toggleWindow_ 處理)
                # self.plugin.loadPreferences() # Removed: Preferences should be loaded by the caller (NineBoxView)
                debug_log(f"[初始化] 載入的偏好設定:")
                debug_log(f"  - lastInput: '{getattr(self.plugin, 'lastInput', '')}'") 
                debug_log(f"  - selectedChars: {getattr(self.plugin, 'selectedChars', [])}")
                debug_log(f"  - lockedChars: {getattr(self.plugin, 'lockedChars', {})}")
                debug_log(f"  - currentArrangement: {getattr(self.plugin, 'currentArrangement', [])}")
                debug_log(f"  - isInClearMode: {getattr(self.plugin, 'isInClearMode', False)}")
            
            # 設定視窗位置
            position_to_apply = None
            plugin_has_pos_attr = hasattr(self, 'plugin') and hasattr(self.plugin, 'windowPosition')
            current_plugin_pos = self.plugin.windowPosition if plugin_has_pos_attr else None
            
            if plugin_has_pos_attr and current_plugin_pos:
                try:
                    if len(current_plugin_pos) >= 2:
                        position_to_apply = current_plugin_pos
                        debug_log(f"[初始化] 將套用視窗位置: {position_to_apply}")
                except (TypeError, AttributeError):
                    debug_log(f"[初始化] 無效的位置類型: {type(current_plugin_pos)}")
            
            if position_to_apply:
                try:
                    x = float(position_to_apply[0])
                    y = float(position_to_apply[1])
                    self.window().setFrameOrigin_(NSMakePoint(x, y))
                    debug_log(f"[初始化] 視窗位置已設定為 ({x}, {y})")
                except (ValueError, TypeError) as e:
                    debug_log(f"[初始化] 設定視窗位置錯誤: {e}")
            
            # 顯示主視窗
            self.window().makeKeyAndOrderFront_(None)
            
            # 檢查並重建控制面板
            self.rebuildControlsPanelIfNeeded()
            
            # === 智慧初始化：尊重已載入的排列狀態 ===
            if hasattr(self, 'plugin'):
                # 先確保控制面板 UI 顯示正確的載入值
                if self.controlsPanelView:
                    debug_log("[初始化] 更新控制面板 UI")
                    self.controlsPanelView.update_ui(self.plugin, update_lock_fields=True)
                
                # 檢查是否有載入的 lastInput
                if hasattr(self.plugin, 'lastInput') and self.plugin.lastInput:
                    debug_log(f"[初始化] 處理載入的 lastInput: '{self.plugin.lastInput}'")
                    # 解析 lastInput 以更新 selectedChars
                    if hasattr(self.plugin, 'parse_input_text'):
                        parsed_chars = self.plugin.parse_input_text(self.plugin.lastInput)
                        if parsed_chars:
                            self.plugin.selectedChars = parsed_chars
                            debug_log(f"[初始化] 解析後的 selectedChars: {self.plugin.selectedChars}")
                
                # 檢查是否有有效的載入排列
                has_valid_arrangement = (hasattr(self.plugin, 'currentArrangement') and 
                                        self.plugin.currentArrangement and 
                                        any(item is not None for item in self.plugin.currentArrangement))
                
                if has_valid_arrangement:
                    debug_log(f"[初始化] 使用載入的排列: {self.plugin.currentArrangement}")
                    # 不重新生成，直接使用載入的排列
                    debug_log("[初始化] 跳過重新生成，保持載入的排列狀態")
                else:
                    debug_log("[初始化] 沒有有效的載入排列，生成新排列")
                    # 只有在沒有有效排列時才生成新的
                    if hasattr(self.plugin, 'event_handlers') and hasattr(self.plugin.event_handlers, 'generate_new_arrangement'):
                        debug_log("[初始化] 執行新排列生成")
                        
                        # 設定一個標記來表示這是初始化
                        self.plugin._is_initializing = True
                        
                        # 生成新排列
                        self.plugin.event_handlers.generate_new_arrangement()
                        
                        # 清除標記
                        self.plugin._is_initializing = False
                        
                        debug_log(f"[初始化] 生成的新排列: {self.plugin.currentArrangement}")
                
                # 更新介面
                self.plugin.updateInterface(None)
            
            # 官方模式：設定初始資料到 preview view
            if hasattr(self, 'previewView') and self.previewView:
                # 同步 plugin 的資料到 preview view 的屬性設定器
                if hasattr(self.plugin, 'currentArrangement'):
                    self.previewView.currentArrangement = self.plugin.currentArrangement
                if hasattr(self.plugin, 'zoomFactor'):
                    self.previewView.zoomFactor = self.plugin.zoomFactor
                
                # 強制立即重繪
                self.previewView.setNeedsDisplay_(True)
                
                debug_log("[官方模式] 已同步資料到預覽畫面的屬性設定器並強制重繪")
            
            # 設定一個簡短的延遲，然後再次強制重繪
            # 這有助於解決某些情況下初始化後畫面仍未更新的問題
            NSTimer.scheduledTimerWithTimeInterval_target_selector_userInfo_repeats_(
                0.1, self, "delayedForceRedraw:", None, False
            )
            
            debug_log("[初始化] 完成")
                
        except Exception as e:
            error_log("[makeKeyAndOrderFront] 初始化錯誤", e)
    
            
    def _update_settings_button_color(self):
        """根據 Glyphs 預覽區域的背景色更新設定按鈕的圖示顏色"""
        if not self.controlsPanelButton:
            return
        
        try:
            is_preview_dark = NSUserDefaults.standardUserDefaults().boolForKey_("GSPreview_Black")
            
            text_color = None
            if is_preview_dark:
                # 預覽區為暗色，按鈕圖示應為亮色
                text_color = NSColor.whiteColor()
            else:
                # 預覽區為亮色，按鈕圖示應為暗色
                text_color = NSColor.blackColor()

            # 為 "⚙" 符號設定合適的字型大小
            symbol_font = NSFont.systemFontOfSize_(15.0) # 您可以微調此大小

            attributes = {
                NSForegroundColorAttributeName: text_color,
                NSFontAttributeName: symbol_font
            }
            
            attributed_title = NSAttributedString.alloc().initWithString_attributes_("⚙", attributes)
            self.controlsPanelButton.setAttributedTitle_(attributed_title)
            debug_log(f"設定按鈕圖示顏色已更新 (attributed title)。預覽區暗色: {is_preview_dark}, 顏色: {text_color.description() if text_color else 'None'}")
        except Exception as e:
            error_log("更新設定按鈕圖示顏色時發生錯誤 (attributed title)", e)

    def _handleUserDefaultsChange_(self, notification):
        """處理用戶偏好設定變更通知"""
        self._update_settings_button_color()
    
    def delayedForceRedraw_(self, timer):
        """延遲強制重繪（解決初始化問題）"""
        try:
            if hasattr(self, 'previewView') and self.previewView:
                # 再次確保同步最新數據
                if hasattr(self, 'plugin'):
                    if hasattr(self.plugin, 'currentArrangement'):
                        self.previewView.currentArrangement = self.plugin.currentArrangement
                    if hasattr(self.plugin, 'zoomFactor'):
                        self.previewView.zoomFactor = self.plugin.zoomFactor
                
                # 強制重繪
                self.previewView.setNeedsDisplay_(True)
                debug_log("delayedForceRedraw_: 執行延遲強制重繪")
        except Exception as e:
            error_log("延遲強制重繪時發生錯誤", e)
    
    def dealloc(self):
        """解構式"""
        try:
            NSNotificationCenter.defaultCenter().removeObserver_(self)
            
            if hasattr(self, 'controlsPanelWindow') and self.controlsPanelWindow:
                self.controlsPanelWindow.orderOut_(None)
                
        except:
            pass
        objc.super(NineBoxWindow, self).dealloc()
    
    def _ensure_child_window_relationship(self):
        """確保控制面板與主視窗建立正確的子視窗關係"""
        try:
            if self.controlsPanelWindow and self.window():
                # 先移除現有的子視窗關係（如果存在）
                try:
                    self.window().removeChildWindow_(self.controlsPanelWindow)
                except:
                    # 如果沒有現有關係，忽略錯誤
                    pass
                
                # 重新建立子視窗關係
                self.window().addChildWindow_ordered_(self.controlsPanelWindow, 1)  # NSWindowAbove = 1
                debug_log("已確保控制面板與主視窗的子視窗關係")
                
        except Exception as e:
            error_log("建立子視窗關係錯誤", e)
    
    def rebuildControlsPanelIfNeeded(self):
        """如需要重建控制面板，確保子視窗關係正確"""
        try:
            if self.controlsPanelVisible:
                # 檢查是否需要重建
                needs_rebuild = (not self.controlsPanelWindow or 
                               not self.controlsPanelWindow.isVisible())
                
                if needs_rebuild:
                    debug_log("重建控制面板窗口")
                    self._setup_controls_panel()
                
                # 確保子視窗關係
                self._ensure_child_window_relationship()
                
                # 顯示控制面板
                if self.controlsPanelWindow:
                    self.controlsPanelWindow.orderFront_(None)
                    if self.controlsPanelView:
                        self.controlsPanelView.update_ui(self.plugin)
                        
        except Exception as e:
            error_log("重建控制面板錯誤", e)
