# encoding: utf-8
"""
九宮格預覽外掛 - 預覽畫面（穩定佈局版）
Nine Box Preview Plugin - Preview View (Stable Layout Version)
基於字身寬度的穩定佈局設計
"""

from __future__ import division, print_function, unicode_literals
import traceback
import objc
import time
import random
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
    GRID_SIZE, GRID_TOTAL, CENTER_POSITION, REDRAW_THRESHOLD
)
from utils import debug_log, get_cached_glyph, get_cached_width

class NineBoxPreviewView(NSView):
    """
    九宮格預覽畫面類別（穩定佈局版）
    Nine Box Preview View Class (Stable Layout Version)
    
    設計原則：
    - 佈局計算完全基於 layer.width（字身寬度）
    - 不使用 LSB、RSB 或路徑邊界等動態資訊
    - 提供穩定的預覽框架，不受路徑編輯影響
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
            
            # 效能優化：快取常用值
            self._last_redraw_time = 0
            self._cached_theme_is_black = None
            self._cached_master = None
            self._cached_grid_metrics = None
            
            # 監聽主題變更
            NSNotificationCenter.defaultCenter().addObserver_selector_name_object_(
                self,
                "glyphsPreviewThemeChanged:",
                NSUserDefaultsDidChangeNotification,
                None
            )
            
        return self
    
    def glyphsPreviewThemeChanged_(self, notification):
        """處理主題變更"""
        try:
            # 清除主題快取
            self._cached_theme_is_black = None
            self.setNeedsDisplay_(True)
            debug_log("主題變更，已觸發重繪")
        except Exception as e:
            debug_log(f"處理主題變更時發生錯誤: {e}")
    
    def mouseDown_(self, event):
        """處理滑鼠點擊事件"""
        self.window().makeKeyWindow()
        self.window().makeFirstResponder_(self)
        self.plugin.randomizeCallback(self)

    def _should_redraw(self):
        """檢查是否應該重繪（節流）"""
        # 檢查是否為強制重繪
        if getattr(self, '_force_redraw', False):
            self._force_redraw = False
            debug_log("強制重繪")
            return True
            
        # 正常的節流邏輯
        current_time = time.time()
        if current_time - self._last_redraw_time < REDRAW_THRESHOLD:
            return False
        self._last_redraw_time = current_time
        return True

    def force_redraw(self):
        """設置強制重繪標記"""
        self._force_redraw = True
        self._last_redraw_time = 0  # 重置節流計時器
        self.setNeedsDisplay_(True)
        debug_log("已請求強制重繪，重置節流計時器")
    
    def setFrame_(self, frame):
        """覆寫 setFrame_ 方法"""
        # 記錄舊框架
        oldFrame = self.frame()
        
        # 呼叫父類方法
        objc.super(NineBoxPreviewView, self).setFrame_(frame)
        
        # 如果框架大小改變，觸發重繪
        if (oldFrame.size.width != frame.size.width or 
            oldFrame.size.height != frame.size.height):
            debug_log(f"預覽視圖框架變更：{oldFrame.size.width}x{oldFrame.size.height} -> {frame.size.width}x{frame.size.height}")
            
            # 清除網格度量快取
            self._cached_grid_metrics = None
            
            # 強制重繪
            self.force_redraw()

    def _get_theme_is_black(self):
        """檢查當前主題是否為深色模式"""
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
            baseWidth = self.plugin.getBaseWidth()
            debug_log(f"基準寬度 baseWidth: {baseWidth}")
            
            # === 計算最大字身寬度（僅使用 layer.width）===
            # 這是佈局計算的唯一依據，確保穩定性
            maxWidth = 0  # 初始設為 0，不預設為 baseWidth
            
            # 考慮周圍8個字符的寬度
            if display_chars:
                for char in display_chars:
                    glyph = get_cached_glyph(Glyphs.font, char)
                    if glyph and glyph.layers[currentMaster.id]:
                        # 僅使用 layer.width（字身寬度）
                        layer_width = glyph.layers[currentMaster.id].width
                        maxWidth = max(maxWidth, layer_width)
                        debug_log(f"字符 '{char}' 的字身寬度: {layer_width}")
            
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
                debug_log(f"無有效字符寬度，使用基準寬度: {baseWidth}")
            
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
            
            # 應用自定義縮放
            customScale = self.plugin.zoomFactor
            scale *= customScale
            debug_log(f"應用自定義縮放後的比例 scale: {scale}")
            
            # 更新網格尺寸
            cellWidth *= scale
            gridWidth *= scale
            gridHeight *= scale
            SPACING *= scale
            debug_log(f"縮放後的單元格寬度 cellWidth: {cellWidth}")
            debug_log(f"縮放後的網格總寬度 gridWidth: {gridWidth}")
            
            # === 計算繪製起始位置（固定的佈局）===
            startX = rect.size.width / 2 - gridWidth / 2
            offsetY = rect.size.height * 0.05  # 向上偏移 5%
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
            debug_log(f"計算網格度量時發生錯誤：{e}")
            if DEBUG_MODE:
                print(traceback.format_exc())
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
            debug_log(f"繪製字符時發生錯誤: {e}")
            if DEBUG_MODE:
                print(traceback.format_exc())

    def drawRect_(self, rect):
        """繪製畫面內容（穩定佈局版）"""
        try:
            # 檢查是否需要重繪（節流）
            if not self._should_redraw() and not DEBUG_MODE:
                return
            
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
            
            # === 修正：當currentArrangement非空時使用它，無論selectedChars是否為空 ===
            # 使用目前的排列
            display_chars = self.plugin.currentArrangement if (self.plugin.selectedChars or self.plugin.currentArrangement) else []
            debug_log(f"使用排列: {display_chars}")
            
            # 計算網格度量
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
                
                # 選擇要繪製的字符層
                layer = None
                if i == 4 and Glyphs.font.selectedLayers:  # 中心位置
                    layer = Glyphs.font.selectedLayers[0]
                else:
                    # 當沒有其他字符時，使用目前編輯的字符填充
                    if not display_chars:
                        if Glyphs.font.selectedLayers:
                            layer = Glyphs.font.selectedLayers[0]
                    else:
                        char_index = i if i < 4 else i - 1
                        if char_index < len(display_chars):
                            glyph = Glyphs.font.glyphs[display_chars[char_index]]
                            layer = glyph.layers[currentMaster.id] if glyph else None
                
                if layer:
                    # 計算單元格高度
                    cellHeight = metrics['gridHeight'] / 3 - metrics['SPACING']
                    
                    # 繪製字符
                    self._draw_character_at_position(
                        layer, centerX, centerY, 
                        metrics['cellWidth'], cellHeight, 
                        metrics['scale'], is_black
                    )
                    
        except Exception as e:
            print(f"繪製預覽畫面時發生錯誤: {e}")
            if DEBUG_MODE:
                print(traceback.format_exc())
    
    def dealloc(self):
        """析構函數"""
        try:
            NSNotificationCenter.defaultCenter().removeObserver_(self)
        except:
            pass
        objc.super(NineBoxPreviewView, self).dealloc()
