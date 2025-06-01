# encoding: utf-8
"""
九宮格預覽外掛 - 預覽畫面（優化版）
Nine Box Preview Plugin - Preview View (Optimized)
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
    九宮格預覽畫面類別（優化版）
    Nine Box Preview View Class (Optimized)
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
        """設置強制重繪標記（階段1.3：優化版）"""
        self._force_redraw = True
        self._last_redraw_time = 0  # 重置節流計時器
        self.setNeedsDisplay_(True)
        debug_log("[階段1.3] 已請求強制重繪，重置節流計時器")
    
    def setFrame_(self, frame):
        """覆寫 setFrame_ 方法（階段1.3：新增）"""
        # 記錄舊框架
        oldFrame = self.frame()
        
        # 呼叫父類方法
        objc.super(NineBoxPreviewView, self).setFrame_(frame)
        
        # 如果框架大小改變，觸發重繪
        if (oldFrame.size.width != frame.size.width or 
            oldFrame.size.height != frame.size.height):
            debug_log(f"[階段1.3] 預覽視圖框架變更：{oldFrame.size.width}x{oldFrame.size.height} -> {frame.size.width}x{frame.size.height}")
            
            # 清除網格度量快取
            self._cached_grid_metrics = None
            
            # 強制重繪
            self.force_redraw()

    def _get_theme_is_black(self):
        """檢查當前主題是否為深色模式"""
        return NSUserDefaults.standardUserDefaults().boolForKey_("GSPreview_Black")
    
    def _get_lock_state(self):
        """取得鎖頭狀態"""
        if (hasattr(self, 'plugin') and self.plugin and
            hasattr(self.plugin, 'windowController') and self.plugin.windowController and 
            hasattr(self.plugin.windowController, 'controlsPanelView') and 
            self.plugin.windowController.controlsPanelView and 
            hasattr(self.plugin.windowController.controlsPanelView, 'isInClearMode')):
            return self.plugin.windowController.controlsPanelView.isInClearMode
        return False  # 預設為上鎖（與控制面板預設值一致）

    def _calculate_grid_metrics(self, rect, display_chars, currentMaster):
        """計算並快取網格度量"""
        try:
            # 檢查區域是否合法
            if rect.size.width <= 0 or rect.size.height <= 0:
                debug_log(f"警告：無效的繪製區域：{rect.size.width}x{rect.size.height}")
                return {
                    'cellWidth': 10,
                    'gridWidth': 30,
                    'gridHeight': 30,
                    'SPACING': 1,
                    'startX': 0,
                    'startY': 30,
                    'scale': 1
                }
            
            # 檢查是否可以使用快取
            cache_key = (rect.size.width, rect.size.height, len(display_chars), self.plugin.zoomFactor)
            if self._cached_grid_metrics and self._cached_grid_metrics[0] == cache_key:
                return self._cached_grid_metrics[1]
            
            # 計算新的度量
            self.cachedHeight = max(currentMaster.ascender - currentMaster.descender, 100)  # 確保最小高度
            MARGIN = min(rect.size.width, rect.size.height) * MARGIN_RATIO
            
            # 使用 getBaseWidth 方法取得基準寬度
            baseWidth = max(self.plugin.getBaseWidth(), 100)  # 確保最小寬度
            
            # 優化：批次計算最大寬度
            maxWidth = baseWidth
            if display_chars:
                for char in display_chars:
                    glyph = get_cached_glyph(Glyphs.font, char)
                    if glyph:
                        layer = glyph.layers[currentMaster.id]
                        if layer:
                            maxWidth = max(maxWidth, get_cached_width(layer))
            
            # 確保最小寬度
            maxWidth = max(maxWidth, 100)
            
            SPACING = maxWidth * SPACING_RATIO
            cellWidth = maxWidth + SPACING
            
            # 計算網格總寬度和高度
            gridWidth = GRID_SIZE * cellWidth + (GRID_SIZE - 1) * SPACING
            gridHeight = GRID_SIZE * self.cachedHeight + (GRID_SIZE - 1) * SPACING
            
            # 計算縮放比例，但確保不會太小
            availableWidth = max(rect.size.width - 2 * MARGIN, 10)
            availableHeight = max(rect.size.height - 2 * MARGIN, 10)
            scale = min(availableWidth / gridWidth, availableHeight / gridHeight, 1)
            
            # 應用自定義縮放
            customScale = min(max(self.plugin.zoomFactor, MIN_ZOOM), MAX_ZOOM)
            scale *= customScale
            
            # 確保最小縮放比例
            scale = max(scale, 0.01)
            
            # 更新網格尺寸
            cellWidth *= scale
            gridWidth *= scale
            gridHeight *= scale
            SPACING *= scale
            
            # 計算繪製起始位置（置中）
            startX = rect.size.width / 2 - gridWidth / 2 + self.panOffset[0]
            # 垂直置中
            startY = rect.size.height / 2 + gridHeight / 2 + self.panOffset[1]
            
            # 快取結果
            metrics = {
                'cellWidth': cellWidth,
                'gridWidth': gridWidth,
                'gridHeight': gridHeight,
                'SPACING': SPACING,
                'startX': startX,
                'startY': startY,
                'scale': scale
            }
            self._cached_grid_metrics = (cache_key, metrics)
            
            debug_log(f"計算網格度量：{metrics}")
            return metrics
        
        except Exception as e:
            debug_log(f"計算網格度量時發生錯誤：{e}")
            if DEBUG_MODE:
                print(traceback.format_exc())
            
            # 返回默認度量以避免繪製失敗
            return {
                'cellWidth': 50,
                'gridWidth': 150,
                'gridHeight': 150,
                'SPACING': 5,
                'startX': 10,
                'startY': 160,
                'scale': 0.5
            }

    def _draw_character_at_position(self, layer, centerX, centerY, cellWidth, cellHeight, scale, is_black):
        """繪製單個字符（優化版）"""
        if not layer:
            return
        
        try:
            # 檢查參數是否有效
            if cellWidth <= 0 or cellHeight <= 0 or scale <= 0:
                debug_log(f"無效的繪製參數：cellWidth={cellWidth}, cellHeight={cellHeight}, scale={scale}")
                return
            
            # 檢查位置是否在視圖範圍內
            viewFrame = self.frame()
            if (centerX < -cellWidth or centerX > viewFrame.size.width + cellWidth or
                centerY < -cellHeight or centerY > viewFrame.size.height + cellHeight):
                return  # 在視圖範圍外，不需要繪製
            
            glyphWidth = max(get_cached_width(layer), 1)  # 確保寬度不為0
            glyphHeight = max(self.cachedHeight, 1)  # 確保高度不為0
            
            # 計算字符縮放比例
            scaleX = cellWidth / glyphWidth if glyphWidth > 0 else 1
            scaleY = cellHeight / glyphHeight if glyphHeight > 0 else 1
            glyphScale = max(min(scaleX, scaleY), 0.01)  # 確保縮放比例在合理範圍
            
            # 計算位置
            scaledWidth = glyphWidth * glyphScale
            scaledHeight = glyphHeight * glyphScale
            x = centerX - scaledWidth / 2
            y = centerY - scaledHeight / 2
            
            # 建立變換矩陣
            transform = NSAffineTransform.transform()
            transform.translateXBy_yBy_(x, y)
            transform.scaleBy_(glyphScale)
            
            # 設定顏色
            if is_black:
                fillColor = NSColor.colorWithCalibratedRed_green_blue_alpha_(0.95, 0.95, 0.95, 1.0)
            else:
                fillColor = NSColor.blackColor()
            
            # 使用圖形上下文設定繪製環境
            currentContext = NSGraphicsContext.currentContext()
            if currentContext:
                currentContext.saveGraphicsState()
                
                # 繪製路徑
                bezierPath = layer.completeBezierPath
                if bezierPath:
                    bezierPath = bezierPath.copy()
                    bezierPath.transformUsingAffineTransform_(transform)
                    fillColor.set()
                    bezierPath.fill()
                
                # 繪製開放路徑
                openBezierPath = layer.completeOpenBezierPath
                if openBezierPath:
                    openBezierPath = openBezierPath.copy()
                    openBezierPath.transformUsingAffineTransform_(transform)
                    fillColor.set()
                    openBezierPath.setLineWidth_(1.0 * glyphScale)
                    openBezierPath.stroke()
                
                currentContext.restoreGraphicsState()
                
        except Exception as e:
            debug_log(f"繪製字符時發生錯誤: {e}")
            if DEBUG_MODE:
                print(traceback.format_exc())

    def drawRect_(self, rect):
        """繪製畫面內容（階段2.1：修正版）"""
        try:
            # 檢查是否需要重繪（節流）
            if not self._should_redraw() and not DEBUG_MODE:
                return
            
            rect_width = rect.size.width
            rect_height = rect.size.height
            debug_log(f"[階段2.1] 預覽重繪：{rect_width}x{rect_height}，視窗尺寸：{self.frame().size.width}x{self.frame().size.height}")
            
            # 確保繪製區域有效
            if rect_width <= 0 or rect_height <= 0:
                debug_log("無效的繪製區域尺寸")
                return
            
            # 設定背景顏色（根據 Glyphs 主題設定）
            is_black = self._get_theme_is_black()
            backgroundColor = NSColor.blackColor() if is_black else NSColor.whiteColor()
            backgroundColor.set()
            NSRectFill(rect)
            
            # 檢查字型
            if not Glyphs.font:
                debug_log("沒有開啟字型，中止繪製")
                return
            
            currentMaster = Glyphs.font.selectedFontMaster
            if not currentMaster:
                debug_log("沒有選擇主板，中止繪製")
                return
            
            # === 階段2.1：統一的九宮格繪製邏輯 ===
            # 確保字符資料有效
            if (hasattr(self.plugin, 'selectedChars') and self.plugin.selectedChars and 
                not getattr(self.plugin, 'currentArrangement', None)):
                debug_log("重新生成排列")
                self.plugin.generateNewArrangement()
            
            # 使用目前的排列
            display_chars = getattr(self.plugin, 'currentArrangement', [])
            if not display_chars and hasattr(self.plugin, 'selectedChars'):
                display_chars = self.plugin.selectedChars[:8]
            
            # 建立已存在字符的清單（用於替代不存在的字符）
            available_chars = []
            if display_chars:
                for char in display_chars:
                    glyph = get_cached_glyph(Glyphs.font, char)
                    if glyph and glyph.layers[currentMaster.id]:
                        available_chars.append(char)
            
            # 如果沒有可用字符，使用當前選中的字符作為備用
            if not available_chars and Glyphs.font.selectedLayers:
                available_chars = [Glyphs.font.selectedLayers[0].parent.name]
            
            # 計算網格度量
            metrics = self._calculate_grid_metrics(rect, display_chars, currentMaster)
            
            # 顯示九宮格對應關係
            debug_log("\n[階段2.2] 九宮格對應關係：")
            debug_log("網格索引(i) -> 字符索引(char_index)")
            for test_i in range(GRID_TOTAL):
                if test_i == CENTER_POSITION:
                    debug_log(f"  {test_i} -> 中央位置")
                else:
                    test_char_index = test_i if test_i < CENTER_POSITION else test_i - 1
                    debug_log(f"  {test_i} -> {test_char_index}")
            debug_log("")
            
            # 計算單元格高度（更正確地計算）
            cellHeight = (metrics['gridHeight'] - 2 * metrics['SPACING']) / GRID_SIZE
            
            # 批次繪製字符
            char_count = 0
            available_char_index = 0  # 用於循環使用已存在的字符
            
            for i in range(GRID_TOTAL):
                row = i // GRID_SIZE
                col = i % GRID_SIZE
                
                # 計算位置
                centerX = metrics['startX'] + (col + 0.5) * metrics['cellWidth'] + col * metrics['SPACING']
                centerY = metrics['startY'] - (row + 0.5) * cellHeight - row * metrics['SPACING']
                
                # 選擇圖層
                layer = None
                
                if i == CENTER_POSITION:
                    # 中央位置：優先使用當前選中的字符，如果沒有則隨機選擇周圍字符
                    if Glyphs.font.selectedLayers:
                        layer = Glyphs.font.selectedLayers[0]
                        debug_log(f"[階段2.1] 中央位置使用選中字符：{layer.parent.name}")
                    elif available_chars:
                        # 沒有選中字符時，從可用字符中隨機選一個
                        random_char = random.choice(available_chars)
                        glyph = get_cached_glyph(Glyphs.font, random_char)
                        if glyph and glyph.layers[currentMaster.id]:
                            layer = glyph.layers[currentMaster.id]
                            debug_log(f"[階段2.1] 中央位置使用隨機字符：{random_char}")
                    elif display_chars:
                        # 如果沒有可用字符，但有顯示字符，嘗試使用第一個存在的
                        random_char = random.choice(display_chars)
                        glyph = get_cached_glyph(Glyphs.font, random_char)
                        if glyph and glyph.layers[currentMaster.id]:
                            layer = glyph.layers[currentMaster.id]
                            debug_log(f"[階段2.1] 中央位置使用顯示字符：{random_char}")
                else:
                    # 周圍位置
                    char_index = i if i < CENTER_POSITION else i - 1
                    target_char = None
                    
                    # === 修正：檢查鎖頭狀態，只在上鎖狀態時使用鎖定字符 ===
                    lock_state = self._get_lock_state()
                    if not lock_state and hasattr(self.plugin, 'lockedChars') and char_index in self.plugin.lockedChars:
                        # 🔒 上鎖狀態：使用鎖定字符
                        target_char = self.plugin.lockedChars[char_index]
                        debug_log(f"🔒 位置 {char_index} (網格{i}: 行{row}列{col}) 使用鎖定字符：{target_char}")
                    elif char_index < len(display_chars):
                        # 🔓 解鎖狀態或無鎖定：使用顯示字符
                        target_char = display_chars[char_index]
                        lock_mode_str = "🔓 解鎖" if lock_state else "🔒 無鎖定"
                        debug_log(f"{lock_mode_str} 位置 {char_index} (網格{i}: 行{row}列{col}) 使用顯示字符：{target_char}")
                    
                    # 嘗試取得目標字符的圖層
                    if target_char:
                        glyph = get_cached_glyph(Glyphs.font, target_char)
                        if glyph and glyph.layers[currentMaster.id]:
                            layer = glyph.layers[currentMaster.id]
                    
                    # 如果目標字符不存在，使用已存在的字符替代
                    if not layer and available_chars:
                        replacement_char = available_chars[available_char_index % len(available_chars)]
                        available_char_index += 1
                        glyph = get_cached_glyph(Glyphs.font, replacement_char)
                        if glyph and glyph.layers[currentMaster.id]:
                            layer = glyph.layers[currentMaster.id]
                            debug_log(f"位置 {char_index} 使用替代字符：{replacement_char}")
                
                # 繪製字符
                if layer:
                    char_count += 1
                    self._draw_character_at_position(
                        layer, centerX, centerY, 
                        metrics['cellWidth'], cellHeight, 
                        metrics['scale'], is_black
                    )
            
            debug_log(f"[階段2.1] 完成繪製，共 {char_count} 個字符")
                    
        except Exception as e:
            print(f"[階段2.1] 繪製預覽畫面時發生錯誤: {e}")
            if DEBUG_MODE:
                print(traceback.format_exc())
    
    def dealloc(self):
        """析構函數"""
        try:
            NSNotificationCenter.defaultCenter().removeObserver_(self)
        except:
            pass
        objc.super(NineBoxPreviewView, self).dealloc()