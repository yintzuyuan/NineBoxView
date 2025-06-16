# encoding: utf-8
"""
九宮格預覽外掛 - 預覽畫面（官方模式版）
Nine Box Preview Plugin - Preview View (Official Mode Version)
基於字身寬度的穩定佈局設計，採用官方 Glyphs UI 重繪模式
"""

from __future__ import division, print_function, unicode_literals
import traceback
import objc
import random
import time
from GlyphsApp import Glyphs
from AppKit import (
    NSView, NSColor, NSBezierPath, NSAffineTransform, NSRectFill,
    NSFont, NSFontAttributeName, NSForegroundColorAttributeName,
    NSString, NSMakePoint, NSGradient, NSMakeRect, 
    NSFontManager, NSFontWeightThin, NSFontWeightBold,
    NSGraphicsContext, NSCompositingOperationSourceOver, NSInsetRect,
    NSUserDefaults, NSNotificationCenter, NSUserDefaultsDidChangeNotification
)

# 匯入常數和工具函數
from constants import (
    MARGIN_RATIO, SPACING_RATIO, MIN_ZOOM, MAX_ZOOM, DEBUG_MODE,
    GRID_SIZE, GRID_TOTAL, CENTER_POSITION
)
from utils import debug_log, error_log, get_cached_glyph, get_cached_width

class NineBoxPreviewView(NSView):
    """
    九宮格預覽畫面類別（官方模式版）
    Nine Box Preview View Class (Official Mode Version)
    
    設計原則：
    - 佈局計算完全基於 layer.width（字身寬度）
    - 不使用 LSB、RSB 或路徑邊界等動態資訊
    - 提供穩定的預覽框架，不受路徑編輯影響
    - 採用官方 Glyphs UI 重繪模式，使用屬性設定器自動觸發重繪
    """

    def initWithFrame_plugin_(self, frame, plugin):
        """
        初始化畫面
        Initialize the view
        """
        self = objc.super(NineBoxPreviewView, self).initWithFrame_(frame)
        if self:
            self.plugin = plugin
            self.cachedHeight = 0
            self.panOffset = (0, 0)
            
            # 效能最佳化：快取常用值
            self._cached_theme_is_black = None
            self._cached_master = None
            self._cached_grid_metrics = None
            
            # 初始化屬性設定器的內部值
            self._currentArrangement = []
            self._zoomFactor = 1.0
            
            # 監聽主題變更
            NSNotificationCenter.defaultCenter().addObserver_selector_name_object_(
                self,
                "glyphsPreviewThemeChanged:",
                NSUserDefaultsDidChangeNotification,
                None
            )
            
        return self
    
    def glyphsPreviewThemeChanged_(self, notification):
        """處理主題變更（官方模式）"""
        try:
            # 清除主題快取
            self._cached_theme_is_black = None
            self.setNeedsDisplay_(True)
            debug_log("主題變更，已觸發重繪")
        except Exception as e:
            error_log("處理主題變更時發生錯誤", e)
    
    def mouseDown_(self, event):
        """處理滑鼠點擊事件"""
        # 取得點擊位置
        click_point = event.locationInWindow()
        view_point = self.convertPoint_fromView_(click_point, None)
        
        # 取得視窗標題列高度（約 22 點）
        titlebar_height = 22
        
        # 如果點擊位置在標題列區域內，不觸發隨機排列
        if view_point.y >= self.frame().size.height - titlebar_height:
            return
        
        # 動態防抖機制
        current_time = time.time()
        
        # 初始化或取得上次點擊時間
        if not hasattr(self, '_last_click_time'):
            self._last_click_time = 0
            self._is_first_click_after_focus = True
        
        # 計算時間差
        time_diff = current_time - self._last_click_time
        
        # 根據是否為聚焦後第一次點擊決定防抖時間
        debounce_time = 0.3 if self._is_first_click_after_focus else 0.1  # 300ms vs 100ms
        
        if time_diff < debounce_time:
            return
        
        # 更新點擊時間和狀態
        self._last_click_time = current_time
        self._is_first_click_after_focus = False
        
        
        # 在非標題列區域點擊時，觸發隨機排列
        self.window().makeKeyWindow()
        self.window().makeFirstResponder_(self)
        self.plugin.randomizeCallback(self)

    # === 官方模式：屬性設定器（參照 GlyphView 模式）===
    
    def _get_currentArrangement(self):
        """取得目前排列"""
        return getattr(self, '_currentArrangement', [])
    
    def _set_currentArrangement(self, arrangement):
        """設定目前排列（自動觸發重繪）"""
        if arrangement == getattr(self, '_currentArrangement', []):
            return  # 如果排列沒有改變，不觸發重繪
    
        self._currentArrangement = arrangement if arrangement else []
        self.setNeedsDisplay_(True)  # 官方模式：屬性變更時立即重繪
        debug_log(f"currentArrangement 已更新，觸發重繪: {arrangement}")
    
    currentArrangement = property(_get_currentArrangement, _set_currentArrangement)
    
    def _get_zoomFactor(self):
        """取得縮放係數"""
        return getattr(self, '_zoomFactor', 1.0)
    
    def _set_zoomFactor(self, factor):
        """設定縮放係數（自動觸發重繪）"""
        self._zoomFactor = factor if factor else 1.0
        self.setNeedsDisplay_(True)  # 縮放變更時立即重繪
        debug_log(f"zoomFactor 已更新，觸發重繪: {factor}")
    
    zoomFactor = property(_get_zoomFactor, _set_zoomFactor)
    
    def update(self):
        """標準更新方法（遵循官方 CanvasView 模式）"""
        self.setNeedsDisplay_(True)
        debug_log("呼叫 update() 方法，觸發重繪")
    
    def setFrame_(self, frame):
        """覆寫 setFrame_ 方法（官方模式）"""
        # 記錄舊框架
        oldFrame = self.frame()
        
        # 呼叫父類別方法
        objc.super(NineBoxPreviewView, self).setFrame_(frame)
        
        # 如果框架大小改變，觸發重繪
        if (oldFrame.size.width != frame.size.width or 
            oldFrame.size.height != frame.size.height):
            debug_log(f"預覽畫面框架變更：{oldFrame.size.width}x{oldFrame.size.height} -> {frame.size.width}x{frame.size.height}")
            
            # 清除網格度量快取
            self._cached_grid_metrics = None
            
            # 官方模式：直接觸發重繪
            self.setNeedsDisplay_(True)

    def _get_theme_is_black(self):
        """檢查目前主題是否為深色模式"""
        return NSUserDefaults.standardUserDefaults().boolForKey_("GSPreview_Black")
    
    def _calculate_grid_metrics(self, rect, display_chars, currentMaster):
        """計算網格度量（完全基於字身寬度的穩定佈局）"""
        try:
            # 檢查區域是否合法
            if rect.size.width <= 0 or rect.size.height <= 0:
                debug_log(f"警告：無效的繪製區域：{rect.size.width}x{rect.size.height}")
                return None
            
            # 計算字符高度和邊距
            self.cachedHeight = currentMaster.ascender - currentMaster.descender
            MARGIN = min(rect.size.width, rect.size.height) * MARGIN_RATIO
            
            # === 使用 getBaseWidth 方法取得基準寬度 ===
            try:
                baseWidth = self.plugin.getBaseWidth()
                if not isinstance(baseWidth, (int, float)) or baseWidth <= 0:
                    debug_log(f"警告：基準寬度值無效 ({baseWidth})，使用預設值 1000")
                    baseWidth = 1000
                else:
                    debug_log(f"基準寬度 baseWidth: {baseWidth}")
            except Exception as e:
                error_log("取得基準寬度時發生錯誤", e)
                baseWidth = 1000
            
            # === 計算最大字身寬度（僅使用 layer.width）===
            # 這是佈局計算的唯一依據，確保穩定性
            maxWidth = 0  # 初始設為 0，不預設為 baseWidth
            
            # 考慮周圍字符的寬度（過濾掉 None 值）
            if display_chars:
                for char in display_chars:
                    if char is not None:  # 只處理非 None 的字符
                        glyph = get_cached_glyph(Glyphs.font, char)
                        if glyph and glyph.layers[currentMaster.id]:
                            # 僅使用 layer.width（字身寬度）
                            layer_width = glyph.layers[currentMaster.id].width
                            maxWidth = max(maxWidth, layer_width)
                            debug_log(f"字符 '{char}' 的字身寬度: {layer_width}")
                    else:
                        debug_log("跳過 None 字符的寬度計算")
            
            # 考慮中央字符的寬度
            if Glyphs.font.selectedLayers:
                center_layer = Glyphs.font.selectedLayers[0]
                if center_layer:
                    center_width = center_layer.width
                    maxWidth = max(maxWidth, center_width)
                    debug_log(f"中央字符 '{center_layer.parent.name}' 的字身寬度: {center_width}")
            
            # 如果沒有有效字符或所有字符寬度為0，則使用 baseWidth
            if maxWidth == 0:
                maxWidth = baseWidth
                debug_log(f"無有效字符寬度（可能全為空白），使用基準寬度: {baseWidth}")
            
            debug_log(f"計算後的最大寬度 maxWidth: {maxWidth}")
            
            # 基於字身寬度計算間距
            SPACING = maxWidth * SPACING_RATIO
            
            # 計算單元格寬度（基於字身寬度）
            cellWidth = maxWidth + SPACING
            debug_log(f"單元格寬度 cellWidth: {cellWidth}")
            
            # 計算網格總寬度和高度
            gridWidth = 3 * cellWidth + 2 * SPACING
            gridHeight = 3 * self.cachedHeight + 2 * SPACING
            debug_log(f"網格總寬度 gridWidth: {gridWidth}, 網格總高度 gridHeight: {gridHeight}")
            
            # 計算縮放比例
            availableWidth = rect.size.width - 2 * MARGIN
            availableHeight = rect.size.height - 2 * MARGIN
            scale = min(availableWidth / gridWidth, availableHeight / gridHeight, 1)
            debug_log(f"可用寬度 availableWidth: {availableWidth}, 可用高度 availableHeight: {availableHeight}")
            debug_log(f"計算的縮放比例 scale: {scale}")
            
            # 套用自訂縮放（使用屬性設定器）
            customScale = self.zoomFactor
            scale *= customScale
            debug_log(f"套用自訂縮放後的比例 scale: {scale}")
            
            # 更新網格尺寸
            cellWidth *= scale
            gridWidth *= scale
            gridHeight *= scale
            SPACING *= scale
            debug_log(f"縮放後的單元格寬度 cellWidth: {cellWidth}")
            debug_log(f"縮放後的網格總寬度 gridWidth: {gridWidth}")
            
            # === 計算繪製起始位置（固定的佈局）===
            startX = rect.size.width / 2 - gridWidth / 2
            offsetY = rect.size.height * 0.02  # 向上偏移 2%
            startY = (rect.size.height + gridHeight) / 2 + offsetY
            
            # 回傳穩定的網格度量
            metrics = {
                'cellWidth': cellWidth,
                'gridWidth': gridWidth,
                'gridHeight': gridHeight,
                'SPACING': SPACING,
                'startX': startX,
                'startY': startY,
                'scale': scale
            }
            
            debug_log(f"網格度量（基於字身寬度）：{metrics}")
            return metrics
        
        except Exception as e:
            error_log("計算網格度量時發生錯誤", e)
            return None

    def _draw_character_at_position(self, layer, centerX, centerY, cellWidth, cellHeight, scale, is_black):
        """繪製單個字符（完全基於字身寬度的穩定佈局）"""
        if not layer:
            return
        
        try:
            # === 佈局計算：僅使用字身寬度（layer.width）===
            glyphWidth = layer.width  # 字身寬度（advance width）- 佈局的唯一依據
            glyphHeight = self.cachedHeight
            
            debug_log(f"繪製字符 '{layer.parent.name}' - 字身寬度: {glyphWidth}")
            
            # 計算字符縮放比例（基於字身寬度）
            scaleX = cellWidth / glyphWidth if glyphWidth > 0 else 1
            scaleY = cellHeight / glyphHeight if glyphHeight > 0 else 1
            glyphScale = min(scaleX, scaleY)
            
            # === 位置計算：完全基於字身寬度，確保穩定置中 ===
            scaledWidth = glyphWidth * glyphScale
            scaledHeight = glyphHeight * glyphScale
            
            # 計算繪製起始位置（穩定的置中，不受路徑變化影響）
            x = centerX - scaledWidth / 2
            y = centerY - scaledHeight / 2
            
            # 建立變換矩陣
            transform = NSAffineTransform.transform()
            transform.translateXBy_yBy_(x, y)
            transform.scaleBy_(glyphScale)
            
            # === 內容繪製：使用 completeBezierPath 顯示實際字形 ===
            # 注意：這裡只是繪製內容，不影響佈局
            completeBezierPath = layer.completeBezierPath
            if completeBezierPath:
                completeBezierPath = completeBezierPath.copy()
                completeBezierPath.transformUsingAffineTransform_(transform)
            
            completeOpenBezierPath = layer.completeOpenBezierPath
            if completeOpenBezierPath:
                completeOpenBezierPath = completeOpenBezierPath.copy()
                completeOpenBezierPath.transformUsingAffineTransform_(transform)
            
            # 設定繪製顏色（根據主題）
            if is_black:
                fillColor = NSColor.whiteColor()
                strokeColor = NSColor.whiteColor()
            else:
                fillColor = NSColor.blackColor()
                strokeColor = NSColor.blackColor()
            
            # 繪製路徑
            if completeBezierPath:
                fillColor.set()
                completeBezierPath.fill()
            
            if completeOpenBezierPath:
                strokeColor.set()
                completeOpenBezierPath.setLineWidth_(1.0)
                completeOpenBezierPath.stroke()
            
            debug_log(f"完成繪製 - 縮放: {glyphScale:.3f}, 位置: ({x:.1f}, {y:.1f})")
                
        except Exception as e:
            error_log("繪製字符時發生錯誤", e)

    def drawRect_(self, rect):
        """繪製畫面內容（官方模式）- 增強版"""
        try:
            debug_log(f"預覽重繪：{rect.size.width}x{rect.size.height}")
            
            # === 確保在任何情況下都先繪製背景 ===
            # 設定背景顏色（根據 Glyphs 主題設定）
            is_black = self._get_theme_is_black()
            if is_black:
                NSColor.colorWithCalibratedRed_green_blue_alpha_(0, 0, 0, 1.0).set()
            else:
                NSColor.colorWithCalibratedRed_green_blue_alpha_(1.0, 1.0, 1.0, 1.0).set()
            NSRectFill(rect)
            
            # 檢查字型
            if not Glyphs.font:
                debug_log("沒有開啟字型，中止繪製")
                return
            
            currentMaster = Glyphs.font.selectedFontMaster
            if not currentMaster:
                debug_log("沒有選擇主板，中止繪製")
                return
                
            # 檢查切換字符 - 如果 plugin 存在且視窗顯示中，嘗試獲取最新數據
            try:
                if hasattr(self, 'plugin') and self.plugin:
                    if hasattr(self.plugin, 'event_handlers') and self.plugin.event_handlers:
                        # === 安全檢查：如果正在進行細粒度更新，跳過字符變更檢測 ===
                        if hasattr(self.plugin.event_handlers, '_performing_granular_update') and self.plugin.event_handlers._performing_granular_update:
                            debug_log("正在進行細粒度更新，跳過字符變更檢測")
                        else:
                            current_char = self.plugin.event_handlers._get_current_editing_char()
                            # 正確處理 None 值的字符變更檢測
                            if (hasattr(self.plugin, 'currentArrangement') and 
                                len(self.plugin.currentArrangement) >= 9):
                                current_center = self.plugin.currentArrangement[4]
                                # 只有當字符確實不同時才觸發更新，正確處理 None 值
                                if current_center != current_char:
                                    debug_log(f"檢測到字符變更: {current_center} -> {current_char}")
                                    # 主動觸發重新生成排列
                                    if hasattr(self.plugin.event_handlers, 'selection_changed'):
                                        self.plugin.event_handlers.selection_changed(None)
            except Exception as e:
                debug_log(f"檢查字符變更時出錯: {e}")
                # 繼續繪製，不中斷流程
            
            # === 使用屬性設定器的值優先，然後是 plugin 的值 ===
            arrangement = self.currentArrangement
            
            # 如果 view 的排列為空，嘗試從 plugin 取得
            if not arrangement and hasattr(self.plugin, 'currentArrangement'):
                arrangement = self.plugin.currentArrangement
                # 同時更新 view 的屬性（但不觸發重繪，避免遞迴）
                self._currentArrangement = arrangement
            
            # 檢查排列是否有效（長度為9）
            if not arrangement or len(arrangement) != 9:
                debug_log("沒有有效的9格排列，生成後備排列")
                if hasattr(self.plugin, 'event_handlers'):
                    self.plugin.event_handlers.generate_new_arrangement()
                    if (hasattr(self.plugin, 'currentArrangement') and 
                        len(self.plugin.currentArrangement) == 9):
                        arrangement = self.plugin.currentArrangement
                        # 更新 view 的屬性
                        self._currentArrangement = arrangement
                
                # 如果仍然沒有有效排列，才使用後備邏輯
                if not arrangement or len(arrangement) != 9:
                    current_char = None
                    if Glyphs.font and Glyphs.font.selectedLayers:
                        current_layer = Glyphs.font.selectedLayers[0]
                        if current_layer and current_layer.parent:
                            current_glyph = current_layer.parent
                            if current_glyph.unicode:
                                try:
                                    current_char = chr(int(current_glyph.unicode, 16))
                                except:
                                    current_char = current_glyph.name
                            elif current_glyph.name:
                                current_char = current_glyph.name
                    
                    if not current_char:
                        current_char = "A"  # 最終後備
                    
                    arrangement = [current_char] * 9
                    debug_log(f"使用最終後備排列：{arrangement}")
                    # 更新 view 的屬性
                    self._currentArrangement = arrangement
            
            # 檢查是否為有效的空白排列（根據 flow.md 規則 R8, R10, R12）
            elif arrangement and len(arrangement) == 9:
                # 檢查是否所有元素都是 None（空白排列）
                all_none = all(item is None for item in arrangement)
                if all_none:
                    debug_log("檢測到有效的空白排列（所有元素為 None），這是符合 flow.md 的正確行為")
                else:
                    debug_log(f"檢測到有效的混合排列，包含 {sum(1 for item in arrangement if item is not None)} 個非空元素")
            
            debug_log(f"最終使用排列: {arrangement}")
            
            # 計算網格度量（使用前8個字符作為參考）
            display_chars = arrangement[:8] if len(arrangement) >= 8 else arrangement
            metrics = self._calculate_grid_metrics(rect, display_chars, currentMaster)
            if not metrics:
                debug_log("無法計算網格度量")
                return
            
            # === 繪製九宮格字符 ===
            for i in range(9):
                row = i // 3
                col = i % 3
                
                # 計算目前單元格的中心位置
                centerX = metrics['startX'] + (col + 0.5) * metrics['cellWidth'] + col * metrics['SPACING']
                centerY = metrics['startY'] - (row + 0.5) * (metrics['gridHeight'] / 3)
                
                # 從排列中取得字符
                char_or_name = arrangement[i] if i < len(arrangement) else None
                
                layer = None
                if char_or_name is not None:  # 不是空白
                    # 嘗試取得字符的圖層
                    glyph = get_cached_glyph(Glyphs.font, char_or_name)
                    if glyph and glyph.layers[currentMaster.id]:
                        layer = glyph.layers[currentMaster.id]
                        debug_log(f"位置 {i}: 繪製字符 '{char_or_name}'")
                    else:
                        debug_log(f"位置 {i}: 字符 '{char_or_name}' 在字型中不存在，跳過繪製")
                        # 字符不存在時，確保不繪製任何內容
                        layer = None
                else:
                    debug_log(f"位置 {i}: 空白格（None），完全不繪製")
                
                # 繪製字符（如果有有效的layer）
                if layer:
                    # 計算單元格高度
                    cellHeight = metrics['gridHeight'] / 3 - metrics['SPACING']
                    
                    # 繪製字符
                    self._draw_character_at_position(
                        layer, centerX, centerY, 
                        metrics['cellWidth'], cellHeight, 
                        metrics['scale'], is_black
                    )
                else:
                    # None 值或無效字符：完全不繪製任何內容，保持背景色
                    debug_log(f"位置 {i}: 保持空白（無任何繪製）")
                    
        except Exception as e:
            error_log("繪製預覽畫面時發生錯誤", e)
    
    def dealloc(self):
        """解構式"""
        try:
            NSNotificationCenter.defaultCenter().removeObserver_(self)
        except:
            pass
        objc.super(NineBoxPreviewView, self).dealloc()
