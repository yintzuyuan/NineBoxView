# encoding: utf-8
"""
九宮格預覽外掛 - 控制面板視圖（重構版）
Nine Box Preview Plugin - Controls Panel View (Refactored)
"""

from __future__ import division, print_function, unicode_literals
import traceback
import objc
from GlyphsApp import Glyphs
from AppKit import (
    NSView, NSColor, NSRectFill, NSApp,
    NSNotificationCenter, NSUserDefaultsDidChangeNotification,
    NSViewWidthSizable, NSViewHeightSizable, NSViewMaxYMargin,
    NSMakeRect
)
from Foundation import NSObject

from constants import DEBUG_MODE
from utils import debug_log, error_log
from search_panel import SearchPanel
from lock_fields_panel import LockFieldsPanel


class ControlsPanelView(NSView):
    """
    控制面板視圖類別（重構版）
    Controls Panel View class (Refactored)
    """
    
    def initWithFrame_plugin_(self, frame, plugin):
        """初始化控制面板視圖"""
        try:
            self = objc.super(ControlsPanelView, self).initWithFrame_(frame)
            if self:
                self.plugin = plugin
                
                # 子面板
                self.searchPanel = None
                self.lockFieldsPanel = None
                
                # 從 plugin 對象讀取鎖頭狀態
                self.isInClearMode = getattr(plugin, 'isInClearMode', False)
                debug_log(f"ControlsPanelView 初始化鎖頭狀態：{'🔓 解鎖' if self.isInClearMode else '🔒 上鎖'}")
                
                # 設定視圖屬性
                self.setAutoresizingMask_(NSViewWidthSizable | NSViewHeightSizable)
                
                # 創建UI元件
                self.setupUI()
                
                # 監聽主題變更
                NSNotificationCenter.defaultCenter().addObserver_selector_name_object_(
                    self,
                    "themeChanged:",
                    NSUserDefaultsDidChangeNotification,
                    None
                )
                
                debug_log("控制面板視圖初始化完成")
                
            return self
        except Exception as e:
            error_log("初始化控制面板視圖錯誤", e)
            return None
    
    def setupUI(self):
        """設定使用者介面元件"""
        try:
            # 清除現有子視圖
            for subview in self.subviews():
                subview.removeFromSuperview()
            
            # 獲取視圖尺寸
            bounds = self.bounds()
            
            # 計算佈局
            margin = 10
            spacing = 12
            
            # 計算鎖定欄位面板的高度（3x3網格 + 清除按鈕）
            lock_field_height = 30
            grid_spacing = 4
            button_height = 22
            lock_panel_height = (3 * lock_field_height + 2 * grid_spacing) + button_height + 8
            
            # 創建搜尋面板（頂部，動態高度）
            search_panel_y = margin + lock_panel_height + spacing
            search_panel_height = bounds.size.height - search_panel_y - margin
            search_panel_height = max(search_panel_height, 50)  # 最小高度
            
            searchRect = NSMakeRect(margin, search_panel_y, 
                                   bounds.size.width - 2 * margin, search_panel_height)
            self.searchPanel = SearchPanel.alloc().initWithFrame_plugin_(searchRect, self.plugin)
            self.addSubview_(self.searchPanel)
            
            # 創建鎖定欄位面板（底部，固定高度）
            lockRect = NSMakeRect(margin, margin, 
                                 bounds.size.width - 2 * margin, lock_panel_height)
            self.lockFieldsPanel = LockFieldsPanel.alloc().initWithFrame_plugin_(lockRect, self.plugin)
            self.addSubview_(self.lockFieldsPanel)
            
            # 同步鎖頭狀態
            if self.lockFieldsPanel:
                self.lockFieldsPanel.set_lock_state(self.isInClearMode)
            
            # 更新內容
            self._update_content()
            
        except Exception as e:
            error_log("設定UI時發生錯誤", e)
    
    def setFrame_(self, frame):
        """覆寫 setFrame_ 方法"""
        oldFrame = self.frame()
        
        # 呼叫父類方法
        objc.super(ControlsPanelView, self).setFrame_(frame)
        
        # 如果框架大小改變，重新佈局 UI
        if (oldFrame.size.width != frame.size.width or 
            oldFrame.size.height != frame.size.height):
            debug_log(f"控制面板框架變更：{oldFrame.size.width}x{oldFrame.size.height} -> {frame.size.width}x{frame.size.height}")
            
            # 重新佈局 UI
            self.layoutUI()
            
            # 觸發重繪
            self.setNeedsDisplay_(True)
    
    def layoutUI(self):
        """重新佈局 UI 元件"""
        try:
            bounds = self.bounds()
            margin = 10
            spacing = 12
            
            # 計算鎖定欄位面板的高度
            lock_field_height = 30
            grid_spacing = 4
            button_height = 22
            lock_panel_height = (3 * lock_field_height + 2 * grid_spacing) + button_height + 8
            
            # 調整搜尋面板位置和大小（頂部，動態高度）
            if self.searchPanel:
                search_panel_y = margin + lock_panel_height + spacing
                search_panel_height = bounds.size.height - search_panel_y - margin
                search_panel_height = max(search_panel_height, 50)  # 最小高度
                
                searchRect = NSMakeRect(margin, search_panel_y, 
                                       bounds.size.width - 2 * margin, search_panel_height)
                self.searchPanel.setFrame_(searchRect)
            
            # 調整鎖定欄位面板位置（底部，固定高度）
            if self.lockFieldsPanel:
                lockRect = NSMakeRect(margin, margin, 
                                     bounds.size.width - 2 * margin, lock_panel_height)
                self.lockFieldsPanel.setFrame_(lockRect)
            
            debug_log("完成 UI 佈局調整")
            
        except Exception as e:
            error_log("重新佈局 UI 錯誤", e)
    
    def _update_content(self):
        """更新UI內容"""
        if hasattr(self.plugin, 'lastInput') and self.searchPanel:
            self.searchPanel.update_content(self.plugin)
        
        if hasattr(self.plugin, 'lockedChars') and self.lockFieldsPanel:
            self.lockFieldsPanel.update_lock_fields(self.plugin)
    
    def update_ui(self, plugin_state, update_lock_fields=True):
        """根據外掛狀態更新UI元素
        
        Args:
            plugin_state: 外掛狀態物件
            update_lock_fields: 是否更新鎖定輸入框（預設True）
        """
        try:
            debug_log(f"更新控制面板 UI，update_lock_fields={update_lock_fields}")
            
            # 更新搜尋面板
            if self.searchPanel:
                self.searchPanel.update_content(plugin_state)
            
            # 更新鎖定欄位面板
            if update_lock_fields and self.lockFieldsPanel:
                self.lockFieldsPanel.update_lock_fields(plugin_state)
            elif not update_lock_fields:
                debug_log("跳過鎖定輸入框更新，保持用戶輸入")
            
            # 觸發重繪
            self.setNeedsDisplay_(True)
            
        except Exception as e:
            error_log("更新UI錯誤", e)
    
    def themeChanged_(self, notification):
        """主題變更處理"""
        try:
            self.setNeedsDisplay_(True)
        except Exception as e:
            error_log("主題變更處理錯誤", e)
    
    def drawRect_(self, rect):
        """繪製背景"""
        try:
            # 使用更符合 macOS 標準的背景顏色
            isDarkMode = NSApp.effectiveAppearance().name().containsString_("Dark")
            if isDarkMode:
                backgroundColor = NSColor.windowBackgroundColor()
            else:
                # 在亮色模式下使用淺灰色，更符合 macOS 標準
                backgroundColor = NSColor.colorWithCalibratedWhite_alpha_(0.93, 1.0)
            
            backgroundColor.set()
            NSRectFill(rect)
            
            # 繪製分隔線
            bounds = self.bounds()
            margin = 12
            
            # 在搜尋面板和鎖定面板之間繪製分隔線
            if self.searchPanel and self.lockFieldsPanel:
                searchBottom = self.searchPanel.frame().origin.y
                lineY = searchBottom - 8
                
                lineRect = NSMakeRect(margin, lineY, bounds.size.width - 2 * margin, 1)
                NSColor.separatorColor().set()
                NSRectFill(lineRect)
            
        except Exception as e:
            error_log("繪製背景錯誤", e)
    
    def dealloc(self):
        """析構函數"""
        try:
            NSNotificationCenter.defaultCenter().removeObserver_(self)
        except:
            pass
        objc.super(ControlsPanelView, self).dealloc()


# 為了向後兼容，保留一些舊的引用
BaseTextField = None
CustomTextField = None
LockCharacterField = None
