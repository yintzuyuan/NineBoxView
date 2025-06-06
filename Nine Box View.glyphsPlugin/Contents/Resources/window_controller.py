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
    NSWindowController, NSPanel, NSButton, NSMakeRect, NSMakeSize, NSMakePoint,
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
    CONTROLS_PANEL_WIDTH, CONTROLS_PANEL_MIN_HEIGHT, CONTROLS_PANEL_SPACING,
    CONTROLS_PANEL_VISIBLE_KEY, DEBUG_MODE
)
from utils import debug_log, error_log


class NineBoxWindow(NSWindowController):
    """
    九宮格預覽視窗控制器（優化版）
    Nine Box Window Controller (Optimized)
    """
    
    def initWithPlugin_(self, plugin):
        """初始化視窗控制器（階段1.2：加入控制面板）"""
        try:
            # 動態導入以避免循環依賴
            from preview_view import NineBoxPreviewView
            from controls_panel_view import ControlsPanelView
            self.NineBoxPreviewView = NineBoxPreviewView
            self.ControlsPanelView = ControlsPanelView
            # 不再需要 NSArray，因為我們統一使用 Python list
            
            # 確保偏好設定已載入
            plugin.loadPreferences()
            
            # 載入視窗大小
            savedSize = Glyphs.defaults.get(WINDOW_SIZE_KEY, DEFAULT_WINDOW_SIZE)
            
            # 載入視窗位置
            savedPosition = plugin.windowPosition
            debug_log(f"window_controller.initWithPlugin_: Received savedPosition from plugin: {savedPosition} (type: {type(savedPosition)})")
            
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
                
                # 控制面板相關屬性
                self.controlsPanelButton = None
                self.controlsPanelWindow = None
                self.controlsPanelView = None
                
                # 載入控制面板狀態偏好設定
                self.controlsPanelVisible = Glyphs.defaults.get(CONTROLS_PANEL_VISIBLE_KEY, True)
                
                # 初始化UI（僅設定主視窗）
                self._setup_main_window_ui(panel)
                
                # 初始化控制面板
                self._setup_controls_panel()
                
                self._register_notifications(panel)
                
                # 根據偏好設定顯示控制面板
                if self.controlsPanelVisible:
                    self.showControlsPanel()
                    
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
        
        debug_log(f"[階段1.2] 預覽視圖和控制按鈕初始化完成，尺寸：{actualContentSize.width}x{actualContentSize.height}")
    
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
            panelX = mainFrame.origin.x + mainFrame.size.width + CONTROLS_PANEL_SPACING
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
            
            # === 階段2.2：初始化時載入已儲存的鎖定字符 ===
            if self.controlsPanelView and self.plugin:
                self.controlsPanelView.update_ui(self.plugin)
                debug_log("[階段2.2] 控制面板初始化後載入已儲存的資料")
            
        except Exception as e:
            error_log("創建控制面板視窗錯誤", e)
    
    def _configure_controls_panel_window(self):
        """配置控制面板視窗屬性"""
        panel = self.controlsPanelWindow
        
        panel.setTitle_("Controls")
        panel.setLevel_(NSFloatingWindowLevel)
        panel.setReleasedWhenClosed_(False)
        
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
                
                # === 修正：使用 orderBack_ 確保控制面板顯示在主視窗之下 ===
                self.controlsPanelWindow.orderBack_(None)  # 在背景顯示，避免陰影干擾主視窗
                
                if self.controlsPanelView:
                    self.controlsPanelView.update_ui(self.plugin)
                
                self.controlsPanelVisible = True
                self.controlsPanelButton.setState_(1)
                
                # 更新插件對象屬性
                if hasattr(self, 'plugin'):
                    self.plugin.controlsPanelVisible = True
                
                Glyphs.defaults[CONTROLS_PANEL_VISIBLE_KEY] = True
                
        except Exception as e:
            error_log("顯示控制面板錯誤", e)
    
    def hideControlsPanel(self):
        """隱藏控制面板"""
        try:
            if self.controlsPanelWindow:
                self.controlsPanelWindow.orderOut_(None)
                
                self.controlsPanelVisible = False
                self.controlsPanelButton.setState_(0)
                
                # 更新插件對象屬性
                if hasattr(self, 'plugin'):
                    self.plugin.controlsPanelVisible = False
                
                Glyphs.defaults[CONTROLS_PANEL_VISIBLE_KEY] = False
                
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
                    self.controlsPanelWindow.setFrame_display_animate_(newFrame, True, True)
                    
                    # 同時更新內容視圖大小
                    self.controlsPanelView.setFrame_(NSMakeRect(
                        0, 0, CONTROLS_PANEL_WIDTH, panelHeight
                    ))
                    
                    debug_log(f"[階段1.3] 更新控制面板位置：({panelX}, {panelY}) 大小：{CONTROLS_PANEL_WIDTH}x{panelHeight}")
                
        except Exception as e:
            error_log("[階段1.3] 更新控制面板位置錯誤", e)
    
    def controlsPanelAction_(self, sender):
        """控制面板按鈕動作"""
        try:
            if self.controlsPanelVisible:
                self.hideControlsPanel()
            else:
                self.showControlsPanel()
                
        except Exception as e:
            error_log("控制面板按鈕動作錯誤", e)
    
    def windowDidResize_(self, notification):
        """視窗大小調整處理（階段1.3：優化版）"""
        try:
            if notification.object() == self.window():
                frame = self.window().frame()
                contentView = self.window().contentView()
                contentSize = contentView.frame().size
                
                debug_log(f"[階段1.3] 視窗調整：{frame.size.width}x{frame.size.height}，內容區域：{contentSize.width}x{contentSize.height}")
                
                # 調整預覽畫面 - 確保完全填滿內容區域
                if hasattr(self, 'previewView') and self.previewView:
                    # 使用內容視圖的實際邊界
                    newFrame = contentView.bounds()
                    self.previewView.setFrame_(newFrame)
                    
                    # 立即觸發重繪確保畫面即時更新
                    if hasattr(self.previewView, 'force_redraw'):
                        self.previewView.force_redraw()
                    else:
                        self.previewView.setNeedsDisplay_(True)
                    
                    debug_log(f"[階段1.3] 已調整預覽視圖框架：{newFrame.size.width}x{newFrame.size.height} at ({newFrame.origin.x}, {newFrame.origin.y})")
                
                # 更新控制面板位置和大小
                if self.controlsPanelVisible and self.controlsPanelWindow:
                    self.updateControlsPanelPosition()
                    debug_log("[階段1.3] 已更新控制面板位置和大小")
                
                # 儲存視窗大小
                if hasattr(self, 'plugin'):
                    newSize = [frame.size.width, frame.size.height]
                    Glyphs.defaults[WINDOW_SIZE_KEY] = newSize
                    debug_log(f"[階段1.3] 已儲存視窗大小偏好設定：{newSize}")
                
        except Exception as e:
            error_log("[階段1.3] 處理視窗調整錯誤", e)
    
    def windowDidMove_(self, notification):
        """視窗移動處理（階段1.3：優化版）"""
        try:
            if notification.object() == self.window():
                mainFrame = self.window().frame()
                current_origin_x = mainFrame.origin.x
                current_origin_y = mainFrame.origin.y
                # debug_log(f"window_controller.windowDidMove_: Detected move. Main window origin: ({current_origin_x}, {current_origin_y})") # 可選的更詳細日誌
                
                # 儲存視窗位置
                if hasattr(self, 'plugin'):
                    try:
                        x = float(current_origin_x)
                        y = float(current_origin_y)
                        new_position_to_store = [x, y]
                        self.plugin.windowPosition = new_position_to_store
                        
                        key_to_save_pos = self.plugin.WINDOW_POSITION_KEY
                        Glyphs.defaults[key_to_save_pos] = new_position_to_store
                        debug_log(f"window_controller.windowDidMove_: Saved windowPosition to Glyphs.defaults: {Glyphs.defaults.get(key_to_save_pos)}")
                    except Exception as e:
                        debug_log(f"window_controller.windowDidMove_: Error saving windowPosition to Glyphs.defaults: {e}")
                
                if self.controlsPanelVisible and self.controlsPanelWindow:
                    self.updateControlsPanelPosition()
                    
                    if self.controlsPanelWindow.isVisible():
                        # === 修正：確保控制面板始終在主視窗之下 ===
                        self.controlsPanelWindow.orderBack_(None)  # 確保在背景顯示
                    
                    # debug_log("window_controller.windowDidMove_: Updated controls panel position and ensured visibility.") # 可選的更詳細日誌
                    
        except Exception as e:
            error_log("window_controller.windowDidMove_: Error in windowDidMove", e)
    
    def windowWillClose_(self, notification):
        """視窗關閉處理（階段1.3：完整資源釋放）"""
        try:
            debug_log("[階段1.3] 主視窗即將關閉")
            
            # 保存狀態到插件對象
            if hasattr(self, 'plugin'):
                self.plugin.controlsPanelVisible = self.controlsPanelVisible
                Glyphs.defaults[CONTROLS_PANEL_VISIBLE_KEY] = self.controlsPanelVisible
            
            # 完整釋放控制面板資源
            if self.controlsPanelWindow:
                debug_log("[階段1.3] 釋放控制面板資源")
                self.controlsPanelWindow.orderOut_(None)
                if self.controlsPanelView:
                    self.controlsPanelView = None
                self.controlsPanelWindow.close()
                self.controlsPanelWindow = None
            
            # 保存偏好設定
            if hasattr(self, 'plugin'):
                self.plugin.savePreferences()
            
            # 移除通知觀察者
            NSNotificationCenter.defaultCenter().removeObserver_(self)
            
            # 清除窗口控制器引用
            if hasattr(self, 'plugin') and hasattr(self.plugin, 'windowController'):
                self.plugin.windowController = None
            
        except Exception as e:
            error_log("[階段1.3] 處理視窗關閉錯誤", e)
    
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
            error_log("請求主預覽重繪錯誤", e)
    
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
    
    def redraw(self):
        """重繪介面（向後相容）"""
        self.request_main_redraw()
    
    def redrawIgnoreLockState(self):
        """強制重繪"""
        self.request_main_redraw()
    
    def makeKeyAndOrderFront(self):
        """顯示並激活視窗（階段1.3：視窗重建機制）"""
        try:
            debug_log("window_controller.makeKeyAndOrderFront: Starting.")
            # 如果有記錄的位置，先設定
            position_to_apply = None
            plugin_has_pos_attr = hasattr(self, 'plugin') and hasattr(self.plugin, 'windowPosition')
            current_plugin_pos = self.plugin.windowPosition if plugin_has_pos_attr else None
            debug_log(f"window_controller.makeKeyAndOrderFront: Checking plugin.windowPosition: {current_plugin_pos} (type: {type(current_plugin_pos)})")

            if plugin_has_pos_attr and current_plugin_pos:
                # 處理 NSArray、list 或 tuple
                try:
                    if len(current_plugin_pos) >= 2:
                        position_to_apply = current_plugin_pos
                        debug_log(f"window_controller.makeKeyAndOrderFront: Will apply position from plugin.windowPosition: {position_to_apply}")
                    else:
                        debug_log(f"window_controller.makeKeyAndOrderFront: Position 長度不足: {len(current_plugin_pos)}")
                except (TypeError, AttributeError):
                    debug_log(f"window_controller.makeKeyAndOrderFront: Invalid position type: {type(current_plugin_pos)}. Value: {current_plugin_pos}")
            else:
                debug_log(f"window_controller.makeKeyAndOrderFront: No position in plugin.windowPosition. Value: {current_plugin_pos}")

            if position_to_apply:
                try:
                    x = float(position_to_apply[0])
                    y = float(position_to_apply[1])
                    debug_log(f"window_controller.makeKeyAndOrderFront: Attempting to set window origin to ({x}, {y})")
                    self.window().setFrameOrigin_(NSMakePoint(x, y))
                    debug_log(f"window_controller.makeKeyAndOrderFront: Window origin set to {self.window().frame().origin.x}, {self.window().frame().origin.y}")
                except (ValueError, TypeError) as e:
                    debug_log(f"window_controller.makeKeyAndOrderFront: Error setting window origin: {e}. position_to_apply was: {position_to_apply}")
            
            # 顯示主視窗
            self.window().makeKeyAndOrderFront_(None)
            
            # 檢查並重建控制面板（如果需要）
            if self.controlsPanelVisible:
                if not self.controlsPanelWindow or not self.controlsPanelWindow.isVisible():
                    debug_log("window_controller.makeKeyAndOrderFront: Rebuilding controls panel.")
                    self._setup_controls_panel()
                
                self.showControlsPanel()
                if self.controlsPanelView:
                    self.controlsPanelView.update_ui(self.plugin)
            
            # 更新介面
            if hasattr(self, 'plugin'):
                self.plugin.updateInterface(None)
            
            # 強制重繪確保初次顯示
            if hasattr(self, 'previewView') and self.previewView:
                from Foundation import NSObject, NSTimer
                NSTimer.scheduledTimerWithTimeInterval_target_selector_userInfo_repeats_(
                    0.1, self, "delayedForceRedraw:", None, False
                )
                # debug_log("window_controller.makeKeyAndOrderFront: Scheduled delayed redraw.") # 可選的更詳細日誌
                
        except Exception as e:
            error_log("window_controller.makeKeyAndOrderFront: Error", e)
    
    def delayedForceRedraw_(self, timer):
        """延遲強制重繪（階段1.3）"""
        try:
            if hasattr(self, 'previewView') and self.previewView:
                if hasattr(self.previewView, 'force_redraw'):
                    self.previewView.force_redraw()
                else:
                    self.previewView.setNeedsDisplay_(True)
                debug_log("[階段1.3] 完成延遲重繪")
        except Exception as e:
            error_log("[階段1.3] 延遲重繪錯誤", e)
    
    def dealloc(self):
        """析構函數"""
        try:
            NSNotificationCenter.defaultCenter().removeObserver_(self)
            
            if hasattr(self, 'controlsPanelWindow') and self.controlsPanelWindow:
                self.controlsPanelWindow.orderOut_(None)
                
        except:
            pass
        objc.super(NineBoxWindow, self).dealloc()