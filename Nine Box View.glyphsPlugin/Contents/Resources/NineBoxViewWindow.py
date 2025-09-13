# encoding: utf-8

"""
九宮格預覽外掛 - 視窗控制器
基於原版 NSWindowController 架構，適配平面座標系統
"""

from __future__ import division, print_function, unicode_literals
import objc
from GlyphsApp import Glyphs
from AppKit import (
    NSWindowController, NSPanel, NSButton, NSMakeRect, NSMakeSize, NSMakePoint,
    NSNotificationCenter, NSWindowWillCloseNotification,
    NSWindowDidResizeNotification, NSWindowDidMoveNotification,
    NSUserDefaultsDidChangeNotification,
    NSTitledWindowMask, NSClosableWindowMask, NSResizableWindowMask,
    NSMiniaturizableWindowMask, NSFloatingWindowLevel, NSFullSizeContentViewWindowMask,
    NSBackingStoreBuffered, NSTitlebarAccessoryViewController,
    NSView, NSLayoutAttributeRight, NSViewWidthSizable, NSViewHeightSizable,
    NSColor, NSButtonTypeToggle, NSFont,
    NSAttributedString, NSFontAttributeName, NSForegroundColorAttributeName,
    NSTexturedRoundedBezelStyle, NSWindowCloseButton,
    NSWindowMiniaturizeButton, NSWindowZoomButton
)
import traceback

# 匯入本地化模組
from NineBoxView.localization import localize

# 常數定義
MIN_WINDOW_SIZE = (200, 240)  # 最小視窗大小
DEFAULT_CONTROLS_PANEL_WIDTH = 150  # 控制面板預設寬度
CONTROLS_PANEL_SPACING = 10
SETTINGS_BUTTON_SIZE = 30
SETTINGS_BUTTON_HEIGHT = 24

class CustomControlsPanel(NSPanel):
    """自訂控制面板視窗，禁用快捷鍵關閉功能並限制調整大小行為"""
    
    def init(self):
        """初始化方法，確保所有必要屬性在使用前設定"""
        self = objc.super(CustomControlsPanel, self).init()
        if self:
            # 初始化關鍵屬性，防止記憶體存取錯誤
            self._fixed_x_position = None
            self._main_window_controller = None
        return self
    
    def initWithContentRect_styleMask_backing_defer_(self, contentRect, styleMask, backing, defer):
        """重寫初始化方法，確保屬性在 frame 操作前設定"""
        self = objc.super(CustomControlsPanel, self).initWithContentRect_styleMask_backing_defer_(
            contentRect, styleMask, backing, defer
        )
        if self:
            # 從 contentRect 提取 X 座標作為初始固定位置
            self._fixed_x_position = contentRect.origin.x if contentRect else None
            self._main_window_controller = None
        return self
    
    def performKeyEquivalent_(self, event):
        """攔截 Cmd+W 快捷鍵，防止獨立關閉控制面板"""
        key_code = event.keyCode()
        modifiers = event.modifierFlags()
        
        # Cmd+W
        if key_code == 13 and (modifiers & 0x100000):
            return True  # 阻止事件傳播
            
        return objc.super(CustomControlsPanel, self).performKeyEquivalent_(event)
    
    def cancelOperation_(self, sender):
        """攔截 Esc 鍵，防止意外關閉控制面板"""
        pass
    
    def windowWillResize_toSize_(self, window, proposedSize):
        """限制調整大小：只允許寬度調整，高度完全跟隨主視窗"""
        from AppKit import NSMakeSize
        currentFrame = window.frame()
        constrainedSize = NSMakeSize(
            max(proposedSize.width, DEFAULT_CONTROLS_PANEL_WIDTH),  # 最小寬度限制為預設值
            currentFrame.size.height       # 保持當前高度
        )
        return constrainedSize
    
    def windowDidEndLiveResize_(self, notification):
        """調整大小結束後的處理"""
        try:
            if hasattr(self, '_main_window_controller') and self._main_window_controller:
                # 取得新寬度
                newWidth = self.frame().size.width
                
                # 更新外掛的控制面板寬度設定
                if self._main_window_controller.plugin:
                    self._main_window_controller.plugin.controlsPanelWidth = int(newWidth)
                    self._main_window_controller.plugin.savePreferences()
        except Exception:
            print(traceback.format_exc())
    
    def constrainFrameRect_toScreen_(self, frameRect, screen):
        """限制框架位置：保持左側X座標固定"""
        try:
            # 安全檢查：確保屬性存在且為有效數值
            if (hasattr(self, '_fixed_x_position') and 
                self._fixed_x_position is not None and
                isinstance(self._fixed_x_position, (int, float))):
                frameRect.origin.x = self._fixed_x_position
        except Exception:
            # 記錄錯誤但不中斷執行
            print(traceback.format_exc())
        
        return objc.super(CustomControlsPanel, self).constrainFrameRect_toScreen_(frameRect, screen)

class NineBoxWindow(NSWindowController):
    """九宮格預覽視窗控制器
    
    基於原版 NSWindowController 架構，適配平面座標系統
    """
    
    def initWithPlugin_(self, plugin):
        """初始化視窗控制器
        
        Args:
            plugin: NineBoxViewController 實例
            
        Returns:
            self 或 None（失敗時）
        """
        try:
            # 動態匯入 UI 類別
            self._import_ui_classes()
            
            # 初始化狀態
            self._initialize_state(plugin)
            
            # 建立主視窗
            panel = self._create_main_window()
            if not panel:
                return None
            
            # 初始化父類
            self = objc.super(NineBoxWindow, self).init()
            if not self:
                return None
            
            # 設定視窗控制器
            self._setup_window_controller(panel)
            
            # 套用儲存的位置
            self._apply_saved_position(panel)
            
            return self
            
        except Exception:
            print(traceback.format_exc())
            return None
    
    @objc.python_method
    def _import_ui_classes(self):
        """動態匯入 UI 類別"""
        from NineBoxView.ui.preview_view import NineBoxPreviewView
        from NineBoxView.ui.controls_panel import ControlsPanelView
        
        self.NineBoxPreviewView = NineBoxPreviewView
        self.ControlsPanelView = ControlsPanelView
    
    @objc.python_method
    def _initialize_state(self, plugin):
        """初始化視窗控制器狀態"""
        self.plugin = plugin
        self.controlsPanelVisible = plugin.controlsPanelVisible
        self.previewView = None
        self.controlsPanelButton = None
        self.controlsPanelWindow = None
        self.controlsPanelView = None
    
    @objc.python_method
    def _create_main_window(self):
        """建立主視窗"""
        try:
            savedSize = self.plugin.windowSize
            windowRect = NSMakeRect(0, 0, savedSize[0], savedSize[1])
            styleMask = (NSTitledWindowMask | NSClosableWindowMask |
                        NSResizableWindowMask | NSMiniaturizableWindowMask | 
                        NSFullSizeContentViewWindowMask)
            
            panel = NSPanel.alloc().initWithContentRect_styleMask_backing_defer_(
                windowRect, styleMask, NSBackingStoreBuffered, False
            )
            
            # 設定視窗屬性
            panel.setTitle_(self.plugin.name)
            panel.setMinSize_(NSMakeSize(MIN_WINDOW_SIZE[0], MIN_WINDOW_SIZE[1]))
            panel.setLevel_(NSFloatingWindowLevel)
            panel.setReleasedWhenClosed_(False)
            panel.setTitlebarAppearsTransparent_(True)
            
            return panel
            
        except Exception:
            print(traceback.format_exc())
            return None
    
    @objc.python_method
    def _setup_window_controller(self, panel):
        """設定視窗控制器屬性和 UI"""
        self.setWindow_(panel)
        
        # 設定主視窗 UI
        self._setup_main_window_ui(panel)
        
        # 設定控制面板
        self._setup_controls_panel()
        
        # 註冊通知監聽
        self._register_notifications(panel)
        
        # 處理控制面板可見性
        if self.controlsPanelVisible:
            self.showControlsPanel()
    
    @objc.python_method
    def _setup_main_window_ui(self, panel):
        """設定主視窗UI"""
        contentView = panel.contentView()
        
        # 建立預覽視圖
        previewRect = NSMakeRect(0, 0, panel.frame().size.width, panel.frame().size.height)
        self.previewView = self.NineBoxPreviewView.alloc().initWithFrame_plugin_(previewRect, self.plugin)
        
        if self.previewView:
            # 設定自動調整大小
            self.previewView.setAutoresizingMask_(NSViewWidthSizable | NSViewHeightSizable)
            contentView.addSubview_(self.previewView)
            
            # 調整預覽視圖大小
            actualContentSize = contentView.frame().size
            self.previewView.setFrame_(NSMakeRect(0, 0, actualContentSize.width, actualContentSize.height))
            
        
        # 建立控制面板按鈕
        self._create_controls_panel_button(panel)
    
    @objc.python_method
    def _create_controls_panel_button(self, panel):
        """建立控制面板按鈕"""
        # 建立按鈕
        self.controlsPanelButton = NSButton.alloc().init()
        self.controlsPanelButton.setTitle_("⚙")
        self.controlsPanelButton.setTarget_(self)
        self.controlsPanelButton.setAction_("controlsPanelAction:")
        self.controlsPanelButton.setBezelStyle_(NSTexturedRoundedBezelStyle)
        self.controlsPanelButton.setBordered_(False)  # 移除外框  
        self.controlsPanelButton.setButtonType_(NSButtonTypeToggle)
        
        # 更新按鈕顏色
        self._update_settings_button_color()
        
        # 設定按鈕狀態
        state = 1 if self.controlsPanelVisible else 0
        self.controlsPanelButton.setState_(state)
        
        # 新增到標題列
        buttonView = NSView.alloc().initWithFrame_(
            NSMakeRect(0, 0, SETTINGS_BUTTON_SIZE, SETTINGS_BUTTON_HEIGHT)
        )
        buttonView.addSubview_(self.controlsPanelButton)
        self.controlsPanelButton.setFrame_(
            NSMakeRect(0, 0, SETTINGS_BUTTON_SIZE, SETTINGS_BUTTON_HEIGHT)
        )
        
        accessoryController = NSTitlebarAccessoryViewController.alloc().init()
        accessoryController.setView_(buttonView)
        accessoryController.setLayoutAttribute_(NSLayoutAttributeRight)
        
        panel.addTitlebarAccessoryViewController_(accessoryController)
    
    @objc.python_method
    def _update_settings_button_color(self):
        """根據 Glyphs 預覽區域背景色更新設定按鈕圖示顏色"""
        if not self.controlsPanelButton:
            return
        
        try:
            # 使用新的 tab 層級主題偵測
            from NineBoxView.core.theme_detector import get_current_theme_is_black
            is_preview_dark = get_current_theme_is_black()
            text_color = NSColor.whiteColor() if is_preview_dark else NSColor.blackColor()
            
            attributes = {
                NSForegroundColorAttributeName: text_color,
            }
            
            attributed_title = NSAttributedString.alloc().initWithString_attributes_("⚙", attributes)
            self.controlsPanelButton.setAttributedTitle_(attributed_title)
            
        except Exception:
            print(traceback.format_exc())

    @objc.python_method
    def _setup_controls_panel(self):
        """設定控制面板"""
        self._create_controls_panel_window()
    
    @objc.python_method
    def _create_controls_panel_window(self):
        """建立控制面板子視窗"""
        try:
            
            # 計算位置和大小
            mainFrame = self.window().frame()
            panelHeight = mainFrame.size.height
            panelX = mainFrame.origin.x + mainFrame.size.width + CONTROLS_PANEL_SPACING
            panelY = mainFrame.origin.y
            
            panelWidth = getattr(self.plugin, 'controlsPanelWidth', DEFAULT_CONTROLS_PANEL_WIDTH)
            panelRect = NSMakeRect(panelX, panelY, panelWidth, panelHeight)
            
            
            # 建立面板
            self.controlsPanelWindow = CustomControlsPanel.alloc().initWithContentRect_styleMask_backing_defer_(
                panelRect,
                NSTitledWindowMask | NSClosableWindowMask | NSMiniaturizableWindowMask | NSResizableWindowMask,
                NSBackingStoreBuffered,
                False
            )
            
            
            # 設定面板屬性
            self._configure_controls_panel_window()
            
            # 設定視窗委派和更新固定X座標（如果需要調整）
            self.controlsPanelWindow._main_window_controller = self
            self.controlsPanelWindow.setDelegate_(self.controlsPanelWindow)
            
            # 更新固定X座標（初始化時已設定，這裡僅在需要時更新）
            if self.controlsPanelWindow._fixed_x_position != panelX:
                self.controlsPanelWindow._fixed_x_position = panelX
            
            # 建立控制面板視圖
            contentRect = NSMakeRect(0, 0, panelWidth, panelHeight)
            self.controlsPanelView = self.ControlsPanelView.alloc().initWithFrame_plugin_(
                contentRect, self.plugin
            )
            
            # 設定內容視圖
            self.controlsPanelWindow.setContentView_(self.controlsPanelView)
            
            # 初始化時載入狀態（強制更新以確保偏好設定正確載入）
            if self.controlsPanelView and self.plugin:
                self.controlsPanelView.update_ui(self.plugin, update_lock_fields=True, force_update=True)
            
            
        except Exception:
            print(traceback.format_exc())
    
    @objc.python_method
    def _configure_controls_panel_window(self):
        """設定控制面板視窗屬性"""
        panel = self.controlsPanelWindow
        
        # 設定標題
        controls_panel_title = f'{self.plugin.name}{localize("window_control_panel_suffix")}'
        panel.setTitle_(controls_panel_title)
        panel.setReleasedWhenClosed_(False)
        panel.setBackgroundColor_(NSColor.controlBackgroundColor())
        
        # 隱藏標題列按鈕
        try:
            closeButton = panel.standardWindowButton_(NSWindowCloseButton)
            if closeButton:
                closeButton.setHidden_(True)
            
            miniaturizeButton = panel.standardWindowButton_(NSWindowMiniaturizeButton) 
            if miniaturizeButton:
                miniaturizeButton.setHidden_(True)
            
            zoomButton = panel.standardWindowButton_(NSWindowZoomButton)
            if zoomButton:
                zoomButton.setHidden_(True)
            
            # 隱藏標題列
            panel.setTitlebarAppearsTransparent_(True)
            panel.setTitleVisibility_(1)  # NSWindowTitleHidden
            panel.setTitle_("")
            
            # 調整內容視圖
            panel.setStyleMask_(panel.styleMask() | (1 << 15))  # NSFullSizeContentViewWindowMask
            
            
        except Exception:
            print(traceback.format_exc())
        # 設定視窗行為
        panel.setCollectionBehavior_(1 << 1 | 1 << 3)  # MoveToActiveSpace | Transient
        panel.setMovable_(False)
        
        # 確保建立子視窗關係
        self._ensure_child_window_relationship()
    
    @objc.python_method
    def _ensure_child_window_relationship(self):
        """確保控制面板與主視窗建立正確的子視窗關係"""
        try:
            # 基本檢查：確保兩個視窗都存在且有效
            if not (self.controlsPanelWindow and self.window()):
                return
            
            # 檢查視窗是否仍然有效（未被釋放）
            try:
                # 嘗試存取視窗屬性來驗證視窗有效性
                _ = self.controlsPanelWindow.frame()
                _ = self.window().frame()
            except Exception:
                # 視窗已被釋放，不建立關係
                return
                
            # 檢查是否已經是子視窗
            current_children = self.window().childWindows()
            if current_children and self.controlsPanelWindow in current_children:
                return
            
            # 建立子視窗關係（使用較安全的方法）
            try:
                self.window().addChildWindow_ordered_(self.controlsPanelWindow, 1)  # NSWindowAbove = 1
            except Exception:
                pass
                
        except Exception:
            print(traceback.format_exc())
    
    @objc.python_method
    def _apply_saved_position(self, panel):
        """套用儲存的視窗位置"""
        savedPosition = self.plugin.windowPosition
        if not savedPosition:
            return
            
        try:
            if len(savedPosition) >= 2:
                x, y = float(savedPosition[0]), float(savedPosition[1])
                panel.setFrameOrigin_(NSMakePoint(x, y))
        except Exception:
            print(traceback.format_exc())
    
    @objc.python_method
    def _save_controller_state(self):
        """通知控制器儲存狀態（純視窗管理層委派）"""
        try:
            if self.plugin and hasattr(self.plugin, 'savePreferences'):
                self.plugin.savePreferences()
        except Exception:
            print(traceback.format_exc())

    @objc.python_method
    def _register_notifications(self, panel):
        """註冊通知監聽"""
        notificationCenter = NSNotificationCenter.defaultCenter()
        
        # 建立監聽器註冊記錄，便於清理
        self._registered_observers = []
        
        # 視窗大小調整
        notificationCenter.addObserver_selector_name_object_(
            self, "windowDidResize:", NSWindowDidResizeNotification, panel
        )
        self._registered_observers.append(("windowDidResize:", NSWindowDidResizeNotification, panel))
        
        # 視窗移動
        notificationCenter.addObserver_selector_name_object_(
            self, "windowDidMove:", NSWindowDidMoveNotification, panel
        )
        self._registered_observers.append(("windowDidMove:", NSWindowDidMoveNotification, panel))
        
        # 視窗關閉
        notificationCenter.addObserver_selector_name_object_(
            self, "windowWillClose:", NSWindowWillCloseNotification, panel
        )
        self._registered_observers.append(("windowWillClose:", NSWindowWillCloseNotification, panel))
        
        # 監聽 Glyphs 預覽面板明暗模式切換（關鍵修復！）
        notificationCenter.addObserver_selector_name_object_(
            self, "_handleGlyphsPreviewModeChange:", NSUserDefaultsDidChangeNotification, None
        )
        self._registered_observers.append(("_handleGlyphsPreviewModeChange:", NSUserDefaultsDidChangeNotification, None))
        
        # 監聽 tab 切換事件（支援 tab 層級主題變更）
        if Glyphs.versionNumber >= 3:
            # Glyphs 3+ 支援更多通知事件
            notificationCenter.addObserver_selector_name_object_(
                self, "_handleTabChange:", "GSUpdateInterface", None
            )
            self._registered_observers.append(("_handleTabChange:", "GSUpdateInterface", None))
        
        # 整合系統主題 KVO 監聽（減法重構：統一而非新增）
        self._setup_system_theme_monitoring()
    
    @objc.python_method
    def _cleanup_all_observers(self):
        """安全地移除所有註冊的觀察者"""
        try:
            notificationCenter = NSNotificationCenter.defaultCenter()
            
            # 移除所有記錄的觀察者
            if hasattr(self, '_registered_observers'):
                for selector, name, obj in self._registered_observers:
                    try:
                        notificationCenter.removeObserver_name_object_(self, name, obj)
                    except Exception as e:
                        print(traceback.format_exc())
                
                # 清空記錄
                self._registered_observers = []
            
            # 通用移除（防止遺漏）
            try:
                notificationCenter.removeObserver_(self)
            except Exception as e:
                print(traceback.format_exc())
            
            # 清理系統主題監聽器
            if hasattr(self, '_system_theme_monitor') and self._system_theme_monitor:
                try:
                    self._system_theme_monitor.remove_theme_change_callback(
                        self._handle_system_theme_change_callback
                    )
                    self._system_theme_monitor = None
                except Exception as e:
                    print(traceback.format_exc())
                    
        except Exception as e:
            print(traceback.format_exc())
    
    def _setup_system_theme_monitoring(self):
        """設定系統主題 KVO 監聽（減法重構版）"""
        try:
            from NineBoxView.core.theme_detector import get_system_theme_monitor
            
            # 取得系統主題監聽器並註冊回呼
            system_monitor = get_system_theme_monitor()
            system_monitor.add_theme_change_callback(self._handle_system_theme_change_callback)
            
            # 儲存參考以便清理
            self._system_theme_monitor = system_monitor
            
        except Exception:
            print(traceback.format_exc())
    
    def _handle_system_theme_change_callback(self):
        """系統主題變更回呼（KVO 觸發）"""
        try:
            # 更新控制面板按鈕顏色
            self._update_settings_button_color()
            
            # 通知預覽視圖主題已變更
            if hasattr(self, 'previewView') and self.previewView:
                self.previewView.update()
            
            # 觸發官方重繪
            Glyphs.redraw()
            
        except Exception:
            print(traceback.format_exc())
    
    def controlsPanelAction_(self, sender):
        """控制面板按鈕動作"""
        if self.controlsPanelVisible:
            self.hideControlsPanel()
        else:
            if not self.controlsPanelWindow:
                self._setup_controls_panel()
            self.showControlsPanel()
    
    @objc.python_method
    def showControlsPanel(self):
        """顯示控制面板"""
        try:
            if self.controlsPanelWindow:
                self._update_controls_panel_position()
                
                # 確保子視窗關係正確
                self._ensure_child_window_relationship()
                
                # 顯示控制面板
                self.controlsPanelWindow.orderFront_(None)
                
                if self.controlsPanelView:
                    self.controlsPanelView.update_ui(self.plugin, update_lock_fields=True, force_update=True)
                
                self.controlsPanelVisible = True
                self.controlsPanelButton.setState_(1)
                
                # 通知控制器更新狀態
                self.plugin.controlsPanelVisible = True
                self._save_controller_state()
                
                
        except Exception:
            print(traceback.format_exc())
    
    @objc.python_method
    def hideControlsPanel(self):
        """隱藏控制面板"""
        if not self.controlsPanelWindow:
            return
            
        self.controlsPanelWindow.orderOut_(None)
        self.controlsPanelVisible = False
        self.controlsPanelButton.setState_(0)
        
        # 通知控制器更新狀態
        self.plugin.controlsPanelVisible = False
        self._save_controller_state()
        
    
    @objc.python_method
    def _update_controls_panel_position(self):
        """更新控制面板位置和高度"""
        try:
            if self.controlsPanelWindow and self.controlsPanelView:
                # 取得主視窗框架
                mainFrame = self.window().frame()
                
                # 計算控制面板高度（完全跟隨主視窗高度）
                panelHeight = mainFrame.size.height
                
                # 計算控制面板位置（靠右對齊主視窗）
                panelX = mainFrame.origin.x + mainFrame.size.width + CONTROLS_PANEL_SPACING
                panelY = mainFrame.origin.y
                
                # 使用動態寬度（用戶調整的寬度或預設寬度）
                panelWidth = getattr(self.plugin, 'controlsPanelWidth', DEFAULT_CONTROLS_PANEL_WIDTH)
                
                newFrame = NSMakeRect(panelX, panelY, panelWidth, panelHeight)
                
                # 更新固定X座標（安全檢查）
                if hasattr(self.controlsPanelWindow, '_fixed_x_position'):
                    self.controlsPanelWindow._fixed_x_position = panelX
                
                # 更新視窗框架
                self.controlsPanelWindow.setFrame_display_animate_(newFrame, True, False)
                
                # 更新內容視圖大小
                self.controlsPanelView.setFrame_(NSMakeRect(0, 0, panelWidth, panelHeight))
                
                
        except Exception:
            print(traceback.format_exc())

    def windowDidResize_(self, notification):
        """視窗大小調整處理"""
        try:
            if notification.object() == self.window():
                frame = self.window().frame()
                
                # 更新控制面板位置和高度
                if self.controlsPanelVisible and self.controlsPanelWindow:
                    self._update_controls_panel_position()
                    self._ensure_child_window_relationship()
                
                # 通知控制器儲存視窗大小
                newSize = [frame.size.width, frame.size.height]
                self.plugin.windowSize = newSize
                self._save_controller_state()
                
                
        except Exception:
            print(traceback.format_exc())

    def windowDidMove_(self, notification):
        """視窗移動處理"""
        try:
            if notification.object() == self.window():
                mainFrame = self.window().frame()
                
                # 通知控制器儲存視窗位置
                x = float(mainFrame.origin.x)
                y = float(mainFrame.origin.y)
                self.plugin.windowPosition = [x, y]
                self._save_controller_state()
                
                if self.controlsPanelVisible and self.controlsPanelWindow:
                    self._update_controls_panel_position()
                    self._ensure_child_window_relationship()
                
                
        except Exception:
            print(traceback.format_exc())

    def windowWillClose_(self, notification):
        """視窗關閉處理 - 安全的資源清理順序"""
        try:
            # 通知控制器儲存狀態
            if hasattr(self, 'plugin') and self.plugin:
                self.plugin.controlsPanelVisible = self.controlsPanelVisible
            
            # 1. 先安全地移除所有觀察者（避免在清理過程中觸發額外事件）
            self._cleanup_all_observers()
            
            # 2. 安全釋放控制面板資源（按照正確順序）
            if hasattr(self, 'controlsPanelWindow') and self.controlsPanelWindow:
                try:
                    # 先移除子視窗關係
                    if self.window():
                        try:
                            self.window().removeChildWindow_(self.controlsPanelWindow)
                        except Exception:
                            pass  # 如果關係不存在，忽略錯誤
                    
                    # 隱藏控制面板
                    self.controlsPanelWindow.orderOut_(None)
                    
                    # 清理控制面板視圖
                    if hasattr(self, 'controlsPanelView') and self.controlsPanelView:
                        self.controlsPanelView = None
                    
                    # 關閉並清理控制面板視窗
                    self.controlsPanelWindow.close()
                    self.controlsPanelWindow = None
                    
                except Exception as e:
                    print(traceback.format_exc())
            
            # 3. 通知控制器儲存偏好設定
            try:
                self._save_controller_state()
            except Exception as e:
                print(traceback.format_exc())
            
            # 4. 通知 plugin 層清除視窗引用（最後執行）
            try:
                if hasattr(self, 'plugin') and self.plugin:
                    parent_plugin = getattr(self.plugin, '_parent_plugin', None)
                    if parent_plugin and hasattr(parent_plugin, 'cleanup_window_controller'):
                        parent_plugin.cleanup_window_controller()
            except Exception as e:
                print(traceback.format_exc())
            
        except Exception:
            print(traceback.format_exc())

    def makeKeyAndOrderFront(self):
        """顯示並啟動視窗"""
        try:
            
            # 設定視窗位置
            if self.plugin.windowPosition:
                try:
                    x, y = self.plugin.windowPosition[:2]
                    self.window().setFrameOrigin_(NSMakePoint(x, y))
                except Exception:
                    print(traceback.format_exc())

            # 顯示主視窗
            self.window().makeKeyAndOrderFront_(None)
            
            # 檢查並重建控制面板
            if self.controlsPanelVisible:
                if not self.controlsPanelWindow:
                    self._setup_controls_panel()
                self._ensure_child_window_relationship()
                if self.controlsPanelWindow:
                    self.controlsPanelWindow.orderFront_(None)
                    if self.controlsPanelView:
                        self.controlsPanelView.update_ui(self.plugin, update_lock_fields=True, force_update=True)
            
            # 委派給控制器處理業務邏輯
            if hasattr(self.plugin, 'show_window'):
                self.plugin.show_window(window_controller=self)
            
            # 工具視窗開啟時主動執行視覺標注
            try:
                from NineBoxView.core.input_recognition import VisualFeedbackService
                VisualFeedbackService.apply_feedback_to_all_inputs(self.plugin)
            except Exception:
                print(traceback.format_exc())

            # 設定初始資料到預覽視圖
            if self.previewView:
                new_arrangement = self.plugin.displayArrangement()
                self.previewView.currentArrangement = new_arrangement
                # 立即更新預覽視圖
                self.previewView.update()
            
                
        except Exception:
            print(traceback.format_exc())


    def _handleGlyphsPreviewModeChange_(self, notification):
        """處理 Glyphs 預覽面板明暗模式變更通知（關鍵修復）
        
        遵循官方風格：響應主題變更事件
        """
        try:
            # 通知預覽視圖主題已變更，觸發重繪
            if hasattr(self, 'previewView') and self.previewView:
                # 清除新主題偵測器的快取
                from NineBoxView.core.theme_detector import clear_theme_cache
                clear_theme_cache()
                
                # 觸發預覽視圖重繪
                self.previewView.update()  # 使用官方標準方法
            
            # 更新設定按鈕顏色（修復 Glyphs 預覽模式變更時按鈕不重繪的問題）
            self._update_settings_button_color()
            
            # 觸發官方重繪
            Glyphs.redraw()
            
        except Exception:
            print(traceback.format_exc())

    def _handleTabChange_(self, notification):
        """處理 tab 切換事件（支援 tab 層級主題變更偵測）"""
        try:
            # tab 切換時，清除主題偵測快取以確保重新偵測
            from NineBoxView.core.theme_detector import clear_theme_cache
            clear_theme_cache()
            
            # 更新控制面板按鈕顏色（可能會因 tab 的主題不同而改變）
            self._update_settings_button_color()

            # 通知預覽視圖 tab 已變更
            if hasattr(self, 'previewView') and self.previewView:
                self.previewView.update()
            
        except Exception:
            print(traceback.format_exc())
        
        # 避免未使用參數警告
        _ = notification
        
    def dealloc(self):
        """解構式，確保完整清理資源"""
        try:
            # 使用統一的觀察者清理方法
            self._cleanup_all_observers()
            
            # 確保控制面板完全清理
            if hasattr(self, 'controlsPanelWindow') and self.controlsPanelWindow:
                try:
                    # 移除子視窗關係
                    if self.window():
                        try:
                            self.window().removeChildWindow_(self.controlsPanelWindow)
                        except Exception:
                            pass
                    
                    # 隱藏並關閉
                    self.controlsPanelWindow.orderOut_(None)
                    self.controlsPanelWindow.close()
                    
                except Exception:
                    pass
                
        except Exception:
            pass
            
        objc.super(NineBoxWindow, self).dealloc()