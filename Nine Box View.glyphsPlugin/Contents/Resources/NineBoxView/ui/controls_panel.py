# encoding: utf-8

"""
九宮格預覽外掛 - 控制面板元件
基於原版 ControlsPanelView 的完整復刻，適配平面座標系統
"""

from __future__ import division, print_function, unicode_literals
import traceback
import objc
from AppKit import NSView, NSViewWidthSizable, NSViewHeightSizable, NSColor, NSMakeRect
from Foundation import NSNotificationCenter, NSUserDefaultsDidChangeNotification

class ControlsPanelView(NSView):
    """
    控制面板視圖類別
    基於原版架構，整合搜尋面板和鎖定面板
    """
    
    def initWithFrame_plugin_(self, frame, plugin):
        """初始化控制面板視圖"""
        try:
            self = objc.super(ControlsPanelView, self).initWithFrame_(frame)
            if self:
                self.plugin = plugin
                
                # 執行標記系統（避免重複執行）
                self._ui_update_in_progress = False
                self._last_update_state = None
                
                # 子面板
                self.searchPanel = None
                self.lockFieldsPanel = None
                
                # 從 plugin 物件讀取鎖定欄位狀態
                self.isLockFieldsActive = getattr(plugin, 'isLockFieldsActive', True)
                
                # 設定視圖屬性
                self.setAutoresizingMask_(NSViewWidthSizable | NSViewHeightSizable)
                
                # 建立UI元件
                self.setupUI()
                
                # 註冊通知
                self._register_notifications()
                
                
        except Exception:
            print(traceback.format_exc())
            return None
            
        return self
    
    # ==========================================================================
    # 統一重繪介面（官方標準）
    # ==========================================================================
    
    def _trigger_redraw(self):
        """統一重繪方法（官方標準）"""
        self.setNeedsDisplay_(True)
    
    def update(self):
        """手動更新介面（官方標準）"""
        self._trigger_redraw()
    
    def setupUI(self):
        """設定使用者介面元件"""
        try:
            # 清除現有子視圖
            for subview in self.subviews():
                subview.removeFromSuperview()
            
            # 動態匯入避免循環依賴
            tempRect = NSMakeRect(0, 0, 100, 100)
            
            # 建立搜尋面板
            from NineBoxView.ui.search_panel import SearchPanel
            self.searchPanel = SearchPanel.alloc().initWithFrame_plugin_(tempRect, self.plugin)
            self.addSubview_(self.searchPanel)
            
            # 建立鎖定欄位面板
            from NineBoxView.ui.lock_fields_panel import LockFieldsPanel
            self.lockFieldsPanel = LockFieldsPanel.alloc().initWithFrame_plugin_(tempRect, self.plugin)
            self.addSubview_(self.lockFieldsPanel)
            
            # 同步鎖頭狀態
            if self.lockFieldsPanel:
                if hasattr(self.lockFieldsPanel, 'set_lock_state'):
                    self.lockFieldsPanel.set_lock_state(self.isLockFieldsActive)
            
            # 統一呼叫佈局方法進行初始佈局
            self.layoutUI()
            
            # 更新內容
            self._update_content()
            
        except Exception:
            print(traceback.format_exc())
    
    def setFrame_(self, frame):
        """覆寫 setFrame_ 方法"""
        try:
            oldFrame = self.frame()
            
            # 呼叫父類別方法
            objc.super(ControlsPanelView, self).setFrame_(frame)
            
            # 如果框架大小改變，重新佈局 UI
            if (oldFrame.size.width != frame.size.width or 
                oldFrame.size.height != frame.size.height):
                
                # 重新佈局 UI
                self.layoutUI()
                
                # 觸發重繪
                self._trigger_redraw()  # 使用統一重繪方法
                
        except Exception:
            print(traceback.format_exc())
    
    def layoutUI(self):
        """統一的 UI 佈局方法 - 所有佈局計算的唯一來源"""
        try:
            # 鎖定面板常數（稍後會從專門的常數檔案匯入）
            LOCK_FIELD_HEIGHT = 30
            LOCK_FIELDS_INTERNAL_GRID_SPACING = 5
            LOCK_FIELDS_CLEAR_BUTTON_HEIGHT = 30
            LOCK_FIELDS_SPACING_ABOVE_BUTTON = 10
            
            bounds = self.bounds()
            top_margin = 10
            bottom_margin = 5
            margin = 10  # 左右
            spacing = 0  # 移除間距，讓搜尋框底部填補水平線位置

            # 計算鎖定欄位面板的高度（3x3網格 + 清除按鈕）
            lock_panel_height = (3 * LOCK_FIELD_HEIGHT + 2 * LOCK_FIELDS_INTERNAL_GRID_SPACING) + LOCK_FIELDS_CLEAR_BUTTON_HEIGHT + LOCK_FIELDS_SPACING_ABOVE_BUTTON

            # 容器可用寬度
            container_content_width = bounds.size.width - 2 * margin

            # 計算搜尋面板尺寸（頂部，動態高度）
            search_panel_y = bottom_margin + lock_panel_height + spacing
            search_panel_height = bounds.size.height - search_panel_y - top_margin
            search_panel_height = max(search_panel_height, 50)  # 最小高度
            search_panel_frame_width = container_content_width

            # 設定搜尋面板位置和大小
            if self.searchPanel:
                searchRect = NSMakeRect(0, search_panel_y,
                                       bounds.size.width, search_panel_height)
                self.searchPanel.setFrame_(searchRect)

            # 計算鎖定欄位面板尺寸（底部，固定高度）
            lock_panel_target_width = search_panel_frame_width
            lock_panel_x = margin + (container_content_width - lock_panel_target_width) / 2.0

            # 設定鎖定欄位面板位置和大小
            if self.lockFieldsPanel:
                lockRect = NSMakeRect(lock_panel_x, bottom_margin,
                                     lock_panel_target_width, lock_panel_height)
                self.lockFieldsPanel.setFrame_(lockRect)

            
        except Exception:
            print(traceback.format_exc())
    
    def _update_content(self):
        """更新UI內容 - 統一入口"""
        try:
            if hasattr(self.plugin, 'lastInput') and self.searchPanel:
                self.searchPanel.update_content(self.plugin)
            
            if self.lockFieldsPanel:
                if hasattr(self.lockFieldsPanel, 'updatePanelUI_'):
                    self.lockFieldsPanel.updatePanelUI_(self.plugin)
                    
        except Exception:
            print(traceback.format_exc())
    
    def update_ui(self, plugin_state, update_lock_fields=True, force_update=False):
        """根據外掛狀態更新UI元素（減法重構：去重執行）
        
        Args:
            plugin_state: 外掛狀態物件
            update_lock_fields: 是否更新鎖定輸入框（預設True）
            force_update: 是否強制更新（用於初始化，預設False）
        """
        try:
            # 減法重構：避免重複執行相同的UI更新
            if self._ui_update_in_progress:
                return
            
            # 狀態檢查：如果狀態未變更且不是強制更新，則跳過
            current_state = (plugin_state.lastInput if hasattr(plugin_state, 'lastInput') else None, update_lock_fields)
            if not force_update and self._last_update_state == current_state and not update_lock_fields:
                return
            
            self._ui_update_in_progress = True
            self._last_update_state = current_state
            
            
            # 更新搜尋面板
            if self.searchPanel:
                self.searchPanel.update_content(plugin_state)
            
            # 更新鎖定欄位面板
            if update_lock_fields and self.lockFieldsPanel:
                if hasattr(self.lockFieldsPanel, 'updatePanelUI_'):
                    self.lockFieldsPanel.updatePanelUI_(plugin_state)
            elif not update_lock_fields:
                pass
            
            # 使用新的視窗通訊介面觸發重繪
            if hasattr(self.plugin, 'trigger_preview_redraw'):
                self.plugin.trigger_preview_redraw()
            
        except Exception:
            print(traceback.format_exc())
        finally:
            # 確保執行標記被重置
            self._ui_update_in_progress = False
    
    def updatePanelUI_(self, plugin, update_lock_fields=False):
        """更新 UI 狀態（向後相容方法）"""
        # 直接委派給統一方法
        self.update_ui(plugin, update_lock_fields)
    
    def _register_notifications(self):
        """註冊通知"""
        try:
            # 主題變更通知（簡化版本）
            center = NSNotificationCenter.defaultCenter()
            center.addObserver_selector_name_object_(
                self, 'themeChanged:', NSUserDefaultsDidChangeNotification, None
            )
        except Exception:
            print(traceback.format_exc())
    
    def themeChanged_(self, notification):
        """主題變更處理"""
        try:
            self.setNeedsDisplay_(True)
        except Exception:
            print(traceback.format_exc())
    
    def drawRect_(self, rect):
        """繪製背景 - 使用原生色彩 API"""
        try:
            backgroundColor = NSColor.windowBackgroundColor()
            backgroundColor.set()
            from AppKit import NSRectFill
            NSRectFill(rect)
            
        except Exception:
            print(traceback.format_exc())
    
    def dealloc(self):
        """解構式 - 清理通知"""
        try:
            NSNotificationCenter.defaultCenter().removeObserver_(self)
        except Exception:
            try:
                print(traceback.format_exc())
            except:
                pass
        
        objc.super(ControlsPanelView, self).dealloc()