# encoding: utf-8

"""
Light Table Support - 九宮格預覽的 Light Table 整合支援
適配平面座標系統 (0-8) 的標準化實作
"""

from __future__ import division, print_function, unicode_literals

# =============================================================================
# 環境依賴管理
# =============================================================================

# 基本模組匯入（在 Glyphs.app 外掛環境中應該永遠可用）
from GlyphsApp import Glyphs
from AppKit import NSEvent, NSEventModifierFlagShift, NSEventMaskFlagsChanged
import objc

# 安全的類別尋找函數
def safe_class_lookup(class_name):
    """安全的類別尋找，找不到時返回 None 而不是拋出例外"""
    try:
        return objc.lookUpClass(class_name)
    except objc.nosuchclass_error:
        return None

# 只有 Light Table 模組需要優雅降級
try:
    import lighttable as lt
    LIGHTTABLE_AVAILABLE = True
except (ImportError, Exception):
    lt = None
    LIGHTTABLE_AVAILABLE = False

# 常數定義（移除舊的工具名稱常數，改用 NSClassFromString 方法）


# =============================================================================
# LightTableMonitor 類別
# =============================================================================

class LightTableMonitor(object):
    """Light Table Shift 鍵監控器"""
    
    def __init__(self, preview_view=None):
        self.preview_view = preview_view
        self.is_shift_pressed = False
        self._monitoring = False
        self._monitor = None
    
    def start_monitoring(self):
        """啟動監控"""
        if self._monitoring:
            return
        
        try:
            if NSEvent and NSEventMaskFlagsChanged:
                self._monitor = NSEvent.addLocalMonitorForEventsMatchingMask_handler_(
                    NSEventMaskFlagsChanged, self._handle_modifier_event
                )
                self._monitoring = self._monitor is not None
        except Exception:
            # 監控器啟動失敗時靜默處理
            self._monitoring = False
    
    def stop_monitoring(self):
        """停止監控"""
        if self._monitor and NSEvent:
            NSEvent.removeMonitor_(self._monitor)
            self._monitor = None
        self._monitoring = False
    
    def _handle_modifier_event(self, event):
        """處理修飾鍵事件"""
        try:
            if not event or not NSEventModifierFlagShift:
                return event
                
            old_state = self.is_shift_pressed
            self.is_shift_pressed = bool(event.modifierFlags() & NSEventModifierFlagShift)
            
            # 如果狀態有變更且在 Light Table 模式下，觸發即時重繪
            if old_state != self.is_shift_pressed and is_light_table_active():
                self._trigger_immediate_redraw()
            
        except Exception:
            # 靜默處理事件處理錯誤
            pass
        
        return event
    
    def _trigger_immediate_redraw(self):
        """觸發即時重繪（使用官方標準方法）"""
        try:
            if self.preview_view and hasattr(self.preview_view, 'update'):
                self.preview_view.update()
            elif self.preview_view and hasattr(self.preview_view, 'setNeedsDisplay_'):
                # 備用方法：如果沒有 update() 方法
                self.preview_view.setNeedsDisplay_(True)
        except Exception:
            # 靜默處理重繪錯誤
            pass
    
    def check_shift_state(self):
        """檢查 Shift 鍵狀態"""
        return self.is_shift_pressed if self._monitoring else False


# =============================================================================
# 全域監控器管理
# =============================================================================

# 全域監控器
_global_monitor = None

def start_light_table_monitoring(preview_view=None):
    """啟動監控"""
    global _global_monitor
    
    if _global_monitor is None:
        _global_monitor = LightTableMonitor(preview_view)
    else:
        _global_monitor.preview_view = preview_view
    
    _global_monitor.start_monitoring()

def stop_light_table_monitoring():
    """停止監控"""
    global _global_monitor
    if _global_monitor:
        _global_monitor.stop_monitoring()

def is_shift_pressed():
    """檢查 Shift 鍵狀態"""
    global _global_monitor
    return _global_monitor.check_shift_state() if _global_monitor else False


# =============================================================================
# Light Table 狀態偵測
# =============================================================================

def is_light_table_active(font=None):
    """檢查 Light Table 工具或手形工具是否啟用"""
    target_font = font or Glyphs.font
    if not target_font:
        return False
    
    # 使用 toolDrawDelegate 方法偵測工具（參考 Speed Punk 外掛）
    if hasattr(Glyphs, 'currentDocument') and Glyphs.currentDocument:
        current_document = Glyphs.currentDocument
        if hasattr(current_document, 'windowController'):
            window_controller = current_document.windowController()
            if window_controller and hasattr(window_controller, 'toolDrawDelegate'):
                tool = window_controller.toolDrawDelegate()
                if tool:
                    # 偵測 Light Table 工具（測試多種可能名稱）
                    light_table_class = (
                        safe_class_lookup("LightTableComparisonTool") or
                        safe_class_lookup("LightTable.ComparisonTool") or  
                        safe_class_lookup("LightTableInterface")
                    )
                    light_table_active = light_table_class and tool.isKindOfClass_(light_table_class)
                    
                    # 偵測手形工具
                    hand_tool_class = safe_class_lookup("GlyphsToolHand")
                    hand_tool_active = hand_tool_class and tool.isKindOfClass_(hand_tool_class)
                    
                    return light_table_active or hand_tool_active
        
    return False


# =============================================================================
# 版本比較邏輯
# =============================================================================

def should_use_comparison_version(font=None):
    """判斷是否應該使用比較版本"""
    return is_light_table_active(font) and is_shift_pressed()

def get_display_font_version(font):
    """取得要顯示的字型版本"""
    target_font = font or Glyphs.font
    if not target_font or not should_use_comparison_version(target_font):
        return target_font
    
    # 取得 Light Table 選擇的比較版本
    if hasattr(target_font, 'lt_selected_version'):
        lt_version = getattr(target_font, 'lt_selected_version', None)
        if lt_version and hasattr(lt_version, 'font'):
            comparison_font = getattr(lt_version, 'font', lt_version)
            if comparison_font:
                return comparison_font
    
    return target_font


# =============================================================================
# Light Table 比較版本支援
# =============================================================================

def get_comparison_font(font):
    """取得 Light Table 的比較版本字型
    
    Args:
        font: 當前字型
        
    Returns:
        GSFont or None: Light Table 比較版本字型，如果無效則返回 None
    """
    if not should_use_comparison_version(font):
        return None
    
    # 取得 Light Table 選擇的比較版本
    if hasattr(font, 'lt_selected_version'):
        lt_version = getattr(font, 'lt_selected_version', None)
        if lt_version and hasattr(lt_version, 'font'):
            comparison_font = getattr(lt_version, 'font', lt_version)
            if comparison_font and comparison_font != font:
                return comparison_font
    
    return None


