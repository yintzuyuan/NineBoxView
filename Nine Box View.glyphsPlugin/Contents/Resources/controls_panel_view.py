# encoding: utf-8
"""
九宮格預覽外掛 - 控制面板畫面（重構版）
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

# Constant for the internal margin used within SearchPanel for its NSScrollView
SEARCH_PANEL_INTERNAL_SCROLLVIEW_MARGIN = 8


class ControlsPanelView(NSView):
    """
    控制面板畫面類別（重構版）
    Controls Panel View class (Refactored)
    """
    
    def initWithFrame_plugin_(self, frame, plugin):
        """初始化控制面板畫面"""
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
                
                # 設定畫面屬性
                self.setAutoresizingMask_(NSViewWidthSizable | NSViewHeightSizable)
                
                # 建立UI元件
                self.setupUI()
                
                # 監聽主題變更
                NSNotificationCenter.defaultCenter().addObserver_selector_name_object_(
                    self,
                    "themeChanged:",
                    NSUserDefaultsDidChangeNotification,
                    None
                )
                
                debug_log("控制面板畫面初始化完成")
                
            return self
        except Exception as e:
            error_log("初始化控制面板畫面錯誤", e)
            return None
    
    def setupUI(self):
        """設定使用者介面元件"""
        try:
            # 清除現有子畫面
            for subview in self.subviews():
                subview.removeFromSuperview()
            
            # 取得畫面尺寸
            bounds = self.bounds()
            top_margin = 10
            bottom_margin = 10
            margin = 10  # 左右
            spacing = 6  # 原本是12，改小一點
            
            # 計算鎖定欄位面板的高度（3x3網格 + 清除按鈕）
            lock_field_height = 30
            lock_fields_internal_grid_spacing = 4 # From LockFieldsPanel._create_lock_fields
            lock_fields_clear_button_height = 22 # From LockFieldsPanel._create_clear_button
            lock_fields_spacing_above_button = 8 # From LockFieldsPanel._create_lock_fields current_y
            lock_panel_height = (3 * lock_field_height + 2 * lock_fields_internal_grid_spacing) + lock_fields_clear_button_height + lock_fields_spacing_above_button
            
            # 容器可用寬度
            container_content_width = bounds.size.width - 2 * margin
            
            # 建立搜尋面板（頂部，動態高度）
            search_panel_y = bottom_margin + lock_panel_height + spacing
            search_panel_height = bounds.size.height - search_panel_y - top_margin
            search_panel_height = max(search_panel_height, 50)  # 最小高度
            search_panel_frame_width = container_content_width
            
            searchRect = NSMakeRect(margin, search_panel_y,
                                   search_panel_frame_width, search_panel_height)
            self.searchPanel = SearchPanel.alloc().initWithFrame_plugin_(searchRect, self.plugin)
            self.addSubview_(self.searchPanel)
            
            # 建立鎖定欄位面板（底部，固定高度），寬度根據搜尋面板的內容寬度
            # SearchPanel's scrollView width = search_panel_frame_width - 2 * SEARCH_PANEL_INTERNAL_SCROLLVIEW_MARGIN
            lock_panel_target_width = search_panel_frame_width - 2 * SEARCH_PANEL_INTERNAL_SCROLLVIEW_MARGIN
            
            # 中心對齊鎖定面板
            lock_panel_x = margin + (container_content_width - lock_panel_target_width) / 2.0
            
            lockRect = NSMakeRect(lock_panel_x, bottom_margin,
                                 lock_panel_target_width, lock_panel_height)
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
        
        # 呼叫父類別方法
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
            top_margin = 10
            bottom_margin = 10
            margin = 10  # 左右
            spacing = 6

            # 計算鎖定欄位面板的高度
            lock_field_height = 30
            lock_fields_internal_grid_spacing = 4
            lock_fields_clear_button_height = 22
            lock_fields_spacing_above_button = 8
            lock_panel_height = (3 * lock_field_height + 2 * lock_fields_internal_grid_spacing) + lock_fields_clear_button_height + lock_fields_spacing_above_button

            container_content_width = bounds.size.width - 2 * margin

            # 調整搜尋面板位置和大小（頂部，動態高度）
            if self.searchPanel:
                search_panel_y = bottom_margin + lock_panel_height + spacing
                search_panel_height = bounds.size.height - search_panel_y - top_margin
                search_panel_height = max(search_panel_height, 50)  # 最小高度
                search_panel_frame_width = container_content_width
                
                searchRect = NSMakeRect(margin, search_panel_y,
                                       search_panel_frame_width, search_panel_height)
                self.searchPanel.setFrame_(searchRect)
            else: # Fallback if searchPanel is somehow not yet created
                search_panel_frame_width = container_content_width

            # 調整鎖定欄位面板位置（底部，固定高度），寬度根據搜尋面板的內容寬度
            if self.lockFieldsPanel:
                lock_panel_target_width = search_panel_frame_width - 2 * SEARCH_PANEL_INTERNAL_SCROLLVIEW_MARGIN
                lock_panel_x = margin + (container_content_width - lock_panel_target_width) / 2.0
                
                lockRect = NSMakeRect(lock_panel_x, bottom_margin,
                                     lock_panel_target_width, lock_panel_height)
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
        """解構式"""
        try:
            NSNotificationCenter.defaultCenter().removeObserver_(self)
        except:
            pass
        objc.super(ControlsPanelView, self).dealloc()


# 為了向後相容，保留一些舊的引用
BaseTextField = None
CustomTextField = None
LockCharacterField = None
