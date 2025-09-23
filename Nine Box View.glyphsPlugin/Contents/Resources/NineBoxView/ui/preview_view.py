# encoding: utf-8

"""
PreviewView - 九宮格預覽視圖（整合進階重繪機制）
支援 Light Table、寬度變更偵測、強制重繪等功能
適配平面座標系統 (0-8) 的現代化架構
"""

from __future__ import division, print_function, unicode_literals
import traceback
import objc
import time
from AppKit import (
    NSView, NSColor, NSBezierPath, NSRectFill, NSAffineTransform,
    NSNotificationCenter, NSApp
)

# 透過統一服務介面存取 Glyphs API（移除直接匯入）
from ..core.glyphs_service import get_glyphs_service
from ..core.light_table_support import start_light_table_monitoring, stop_light_table_monitoring

# 佈局常數（適配平面座標系統）
MARGIN_RATIO = 0.08  # 邊距比例
SPACING_RATIO = 0.0  # 間距比例（原版設為 0）
CENTER_POSITION = 4  # 平面座標系統中央位置
MIN_ZOOM = 0.1
MAX_ZOOM = 3.0


class NineBoxPreviewView(NSView):
    """九宮格預覽視圖（整合進階重繪機制）
    
    採用官方 Glyphs UI 重繪模式，支援：
    - Light Table 整合
    - 寬度變更主動偵測
    - 檔案切換強制重繪
    - 屬性設定器觸發重繪
    """
    
    def initWithFrame_plugin_(self, frame, plugin):
        """初始化視圖（整合進階重繪機制）
        
        Args:
            frame (NSRect): 視圖框架
            plugin: NineBoxPluginController 實例
        """
        self = objc.super(NineBoxPreviewView, self).initWithFrame_(frame)
        if self:
            # Plugin Controller 整合
            self.plugin = plugin
            
            # 核心狀態
            self._currentArrangement = []
            
            # 佈局快取（簡化版本）
            self._cached_layout = None
            self._layout_cache_key = None
            self.cachedHeight = 0
            
            # 移除舊的主題快取（改用新的主題偵測器）
            
            # 寬度變更檢測機制
            self._width_change_cache = {}
            self._last_check_time = 0  # 寬度檢測節流機制

            # 防抖機制狀態（修復聚焦後立即點擊的雙重隨機排列問題）
            self._last_randomize_time = 0
            self._debounce_interval = 0.08  # 80ms 防抖間隔

            # 初始化
            self._setup_view()
            self._load_initial_state()
            
            # 啟動 Light Table 監控
            start_light_table_monitoring(self)
            
        return self
    
    def _setup_view(self):
        """設定視圖基本屬性"""
        try:
            # 系統主題監聽已由 KVO 統一處理（減法重構：移除重複監聽）
            pass
            
        except Exception:
            print(traceback.format_exc())
    
    def dealloc(self):
        """視圖釋放時的清理工作"""
        try:
            # 停止 Light Table 監控
            stop_light_table_monitoring()
            
            # 移除通知觀察者
            NSNotificationCenter.defaultCenter().removeObserver_(self)
            
        except Exception:
            print(traceback.format_exc())
        
        # 呼叫父類的 dealloc
        objc.super(NineBoxPreviewView, self).dealloc()
    
    def _load_initial_state(self):
        """載入初始狀態（參照原始穩定版）"""
        try:
            # 從 plugin 取得字符排列
            if hasattr(self.plugin, 'compose_display_arrangement'):
                arrangement = self.plugin.compose_display_arrangement()
                self._currentArrangement = arrangement if arrangement else []
            else:
                # 備用方案：直接存取屬性
                if hasattr(self.plugin, 'displayArrangement'):
                    arrangement = self.plugin.displayArrangement()
                    self._currentArrangement = arrangement if arrangement else []
                    
        except Exception:
            print(traceback.format_exc())
            self._currentArrangement = []
    
    
    # ==========================================================================
    # 統一重繪介面（官方標準 - 純 NSView 模式）
    # ==========================================================================
    
    def _trigger_redraw(self):
        """統一重繪方法（官方 NSView 標準）
        
        採用標準 NSView 重繪機制，讓系統決定重繪時機
        """
        # 立即標記需要重繪
        self.setNeedsDisplay_(True)
        
        # 可選：強制立即處理顯示更新（僅在必要時使用）
        # self.displayIfNeeded()
    
    def update(self):
        """手動更新介面（官方標準）"""
        self._trigger_redraw()
    
    def refresh(self):
        """強制更新介面（清理快取並重繪）"""
        # 清理必要的快取
        self._clear_essential_caches()
        
        # 觸發重繪
        self._trigger_redraw()
    
    def redraw(self):
        """標準重繪方法（照抄 RotateView 模式）"""
        self.setNeedsDisplay_(True)
    
    # ==========================================================================
    # 屬性存取器（官方屬性驅動重繪模式）
    # ==========================================================================
    
    @property
    def currentArrangement(self):
        """當前字符排列"""
        return self._currentArrangement
    
    @currentArrangement.setter
    def currentArrangement(self, value):
        """設定當前字符排列並觸發重繪（官方模式）"""
        if self._currentArrangement != value:
            self._currentArrangement = value[:] if value is not None else []
            self._invalidate_layout_cache()
            self._trigger_redraw()  # 使用統一重繪方法
    
        
    def setGridGlyphs_(self, glyphs):
        """設定九宮格字符陣列（相容性方法）
        
        Args:
            glyphs (list): 長度為9的字符陣列
        """
        if len(glyphs) == 9:
            self.currentArrangement = glyphs[:]
            
    def setGridFont_(self, font):
        """設定顯示字體（相容性方法）
        
        Args:
            font: Glyphs 字體物件（在新架構中未直接使用）
        """
        # 在新架構中，字體資訊由 plugin controller 管理
        # font 參數保留用於向後相容性，但不直接使用
        _ = font  # 避免未使用警告
        self._trigger_redraw()  # 使用統一重繪方法
        
        
    # ==========================================================================
    # 簡化快取管理（官方 NSView 模式）
    # ==========================================================================
    
    def _clear_essential_caches(self):
        """清除必要快取（簡化版本）"""
        try:
            # 清除佈局快取
            self._cached_layout = None
            self._layout_cache_key = None
            
            # 清除新主題偵測器的快取
            from ..core.theme_detector import clear_theme_cache
            clear_theme_cache()
            
            # 清除高度快取
            self.cachedHeight = 0
            
        except Exception:
            print(traceback.format_exc())

    # ==========================================================================
    # 寬度變更檢測（智慧被動模式）
    # ==========================================================================

    def _detect_width_changes(self):
        """檢測字符寬度變更（智慧被動模式 - 修復版本）

        採用原版的正確做法：在重繪時主動檢測寬度變更
        只檢測當前選中字符，減少檢測範圍提升性能

        Returns:
            bool: True 如果檢測到寬度變更
        """
        try:
            # 節流機制：避免過度頻繁檢查（每 100ms 最多檢查一次）
            current_time = time.time() * 1000  # 轉換為毫秒
            if current_time - self._last_check_time < 100:
                return False

            self._last_check_time = current_time

            # 透過統一服務獲取字型上下文
            glyphs_service = get_glyphs_service()
            font, current_master = glyphs_service.get_current_font_context()

            if not font or not current_master:
                return False

            width_changed = False

            # 智慧檢測：只檢測當前選中的字符寬度（減少檢測範圍）
            if hasattr(self.plugin, 'event_handler') and self.plugin.event_handler:
                current_glyph = self.plugin.event_handler.get_selected_glyph()
                if current_glyph:
                    try:
                        glyph = glyphs_service.get_glyph_from_font(font, current_glyph)
                        if glyph and glyph.layers[current_master.id]:
                            layer = glyph.layers[current_master.id]
                            layer_id = f"{current_glyph}_{current_master.id}"
                            current_width = layer.width
                            cached_width = self._width_change_cache.get(layer_id)

                            if cached_width != current_width:
                                self._width_change_cache[layer_id] = current_width
                                if cached_width is not None:  # 只有已有快取時才算變更
                                    width_changed = True
                    except Exception:
                        pass

            return width_changed

        except Exception:
            return False

    # ==========================================================================
    # 主要繪製方法
    # ==========================================================================
    
    def drawRect_(self, rect):
        """繪製畫面內容（官方 NSView 模式：智慧被動檢測）"""
        try:
            # 修復：恢復被動寬度變更檢測
            # 這是原版的正確做法：在每次重繪時檢測寬度變更
            width_changed = self._detect_width_changes()
            if width_changed:
                # 寬度變更時清理佈局快取並觸發重新計算
                self._invalidate_layout_cache()

            # === 繪製背景 ===
            is_black = self._get_theme_is_black()
            if is_black:
                NSColor.blackColor().set()
            else:
                NSColor.whiteColor().set()
            NSRectFill(rect)
            
            # 透過統一服務獲取字型上下文（官方模式）
            glyphs_service = get_glyphs_service()
            font, currentMaster = glyphs_service.get_current_font_context()
            if not font or not currentMaster:
                return
            
            # 取得並標準化排列
            arrangement = self.plugin.displayArrangement() if self.plugin else self._currentArrangement
            
            # 簡化排列同步檢查
            if arrangement != self._currentArrangement:
                self._currentArrangement = arrangement[:] if arrangement else []
                self._invalidate_layout_cache()
            
            # 標準化排列資料
            if not isinstance(arrangement, list) or len(arrangement) != 9:
                arrangement = ["A"] * 9
            else:
                arrangement = [char if char is not None else "" for char in arrangement]
            
            # 計算佈局
            layout = self._calculate_layout()
            if not layout:
                return
            
            # 繪製九宮格
            self._draw_grid_with_layout(layout, is_black, font, currentMaster)
            
        except Exception:
            print(traceback.format_exc())
    
    def _invalidate_layout_cache(self):
        """使佈局快取失效"""
        self._cached_layout = None
        self._layout_cache_key = None
    
    def _calculate_layout(self):
        """計算九宮格佈局（採用官方模式統一上下文）"""
        try:
            frame = self.frame()
            
            # 透過統一服務獲取字型上下文
            glyphs_service = get_glyphs_service()
            font, currentMaster = glyphs_service.get_current_font_context()
            if not font or not currentMaster:
                return None
            
            # 建立快取鍵（簡化版，依賴官方重繪處理字符切換）
            cache_key = (
                frame.size.width, frame.size.height,
                tuple(self._currentArrangement)
            )
            
            # 檢查快取
            if self._layout_cache_key == cache_key and self._cached_layout:
                return self._cached_layout
            
            # 計算網格度量（使用前8個字符作為參考）
            arrangement = self._currentArrangement or []
            display_chars = arrangement[:8] if len(arrangement) >= 8 else arrangement
            metrics = self._calculate_grid_metrics(frame, display_chars, currentMaster, font)
            
            if not metrics:
                return None
            
            # 建構九宮格位置資訊（復刻自原版）
            positions = []
            for i in range(9):
                row = i // 3
                col = i % 3
                
                # 計算目前單元格的中心位置（精確復刻原版公式）
                centerX = metrics['startX'] + (col + 0.5) * metrics['cellWidth'] + col * metrics['SPACING']
                centerY = metrics['startY'] - (row + 0.5) * (metrics['gridHeight'] / 3)
                
                # 計算單元格高度
                cellHeight = metrics['gridHeight'] / 3 - metrics['SPACING']
                
                positions.append({
                    'centerX': centerX,
                    'centerY': centerY,
                    'cellWidth': metrics['cellWidth'],
                    'cellHeight': cellHeight
                })
            
            layout = {
                'positions': positions,
                'metrics': metrics,
                'arrangement': arrangement[:9]  # 確保只有 9 個元素
            }
            
            # 更新快取
            self._cached_layout = layout
            self._layout_cache_key = cache_key
            
            return layout
            
        except Exception:
            print(traceback.format_exc())
            return None
    
    def _calculate_grid_metrics(self, rect, display_chars, currentMaster, font):
        """計算網格度量（採用官方模式參數傳遞）"""
        try:
            # 檢查區域是否合法
            if rect.size.width <= 0 or rect.size.height <= 0:
                return None
            
            # 計算字符高度和邊距
            self.cachedHeight = currentMaster.ascender - currentMaster.descender
            MARGIN = min(rect.size.width, rect.size.height) * MARGIN_RATIO
            
            # === 使用 getBaseWidth 方法取得基準寬度 ===
            try:
                if hasattr(self.plugin, 'getBaseWidth'):
                    baseWidth = self.plugin.getBaseWidth()
                    if not isinstance(baseWidth, (int, float)) or baseWidth <= 0:
                        baseWidth = 1000
                else:
                    baseWidth = 1000
            except Exception:
                baseWidth = 1000
            
            # === 計算最大字身寬度（僅使用 layer.width）===
            maxWidth = 0
            
            # 考慮周圍字符的寬度（過濾掉 None 值）
            if display_chars:
                # 透過統一服務獲取字符
                glyphs_service = get_glyphs_service()
                for char in display_chars:
                    if char is not None:  # 只處理非 None 的字符
                        glyph = glyphs_service.get_glyph_from_font(font, char)
                        if glyph and glyph.layers[currentMaster.id]:
                            # 僅使用 layer.width（字身寬度）
                            layer_width = glyph.layers[currentMaster.id].width
                            maxWidth = max(maxWidth, layer_width)
            
            # 減法優化：移除即時字符獲取，改用現有排列中的字符
            # 原本每次 drawRect_ 都重新獲取 selectedLayers，是性能殺手
            # 改為直接從 currentArrangement 中獲取中央字符
            if hasattr(self, '_currentArrangement') and len(self._currentArrangement) > 4:
                center_char = self._currentArrangement[4]  # 中央位置
                if center_char:
                    # 透過統一服務獲取字符
                    glyph = glyphs_service.get_glyph_from_font(font, center_char)
                    if glyph and glyph.layers[currentMaster.id]:
                        center_width = glyph.layers[currentMaster.id].width
                        maxWidth = max(maxWidth, center_width)
            
            # 如果沒有有效字符或所有字符寬度為0，則使用 baseWidth
            if maxWidth == 0:
                maxWidth = baseWidth
            
            # 基於字身寬度計算間距
            SPACING = maxWidth * SPACING_RATIO
            
            # 計算單元格寬度（基於字身寬度）
            cellWidth = maxWidth + SPACING
            
            # 計算網格總寬度和高度
            gridWidth = 3 * cellWidth + 2 * SPACING
            gridHeight = 3 * self.cachedHeight + 2 * SPACING
            
            # 計算縮放比例（移除 zoomFactor，只使用自適應縮放）
            availableWidth = rect.size.width - 2 * MARGIN
            availableHeight = rect.size.height - 2 * MARGIN
            scale = min(availableWidth / gridWidth, availableHeight / gridHeight, 1.0)
            
            # 更新網格尺寸
            cellWidth *= scale
            gridWidth *= scale
            gridHeight *= scale
            SPACING *= scale
            
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
            
            return metrics
        
        except Exception:
            print(traceback.format_exc())
            return None
    
    def _draw_character_at_position(self, layer, centerX, centerY, cellWidth, cellHeight, _scale, is_black):
        """繪製單個字符（完全復刻原版智慧縮放邏輯）"""
        if not layer:
            return
        
        try:
            # === 佈局計算：僅使用字身寬度（layer.width）===
            glyphWidth = layer.width  # 字身寬度（advance width）- 佈局的唯一依據
            glyphHeight = self.cachedHeight
            
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
            completeBezierPath = layer.completeBezierPath
            completeOpenBezierPath = layer.completeOpenBezierPath
            
            # 檢查路徑是否為空
            fill_empty = completeBezierPath is None or completeBezierPath.isEmpty()
            stroke_empty = completeOpenBezierPath is None or completeOpenBezierPath.isEmpty()
            
            # 如果兩個路徑都為空，嘗試備用方法
            if fill_empty and stroke_empty:
                # 嘗試 bezierPath (不含組件)
                bezierPath = layer.bezierPath
                if bezierPath and not bezierPath.isEmpty():
                    completeBezierPath = bezierPath.copy()
                else:
                    return
            
            if completeBezierPath and not completeBezierPath.isEmpty():
                completeBezierPath = completeBezierPath.copy()
                completeBezierPath.transformUsingAffineTransform_(transform)
            
            if completeOpenBezierPath and not completeOpenBezierPath.isEmpty():
                completeOpenBezierPath = completeOpenBezierPath.copy()
                completeOpenBezierPath.transformUsingAffineTransform_(transform)
            
            # 設定繪製顏色（根據主題）
            if is_black:
                fillColor = NSColor.whiteColor()
                strokeColor = NSColor.whiteColor()
            else:
                fillColor = NSColor.blackColor()
                strokeColor = NSColor.blackColor()
            
            # 繪製路徑（只繪製有效的非空路徑）
            if completeBezierPath and not completeBezierPath.isEmpty():
                try:
                    fillColor.set()
                    completeBezierPath.fill()
                except Exception:
                    print(traceback.format_exc())
            
            if completeOpenBezierPath and not completeOpenBezierPath.isEmpty():
                try:
                    strokeColor.set()
                    completeOpenBezierPath.setLineWidth_(1.0)
                    completeOpenBezierPath.stroke()
                except Exception:
                    print(traceback.format_exc())
            
        except Exception:
            print(traceback.format_exc())
    
    def _is_in_font_view(self):
        """偵測當前是否在 Font View 模式（透過統一服務）"""
        try:
            glyphs_service = get_glyphs_service()
            return glyphs_service.is_in_font_view()
        except:
            return True  # 例外時假設在 Font View
    
    def _get_visible_tab_layers(self):
        """取得當前分頁中可見的圖層列表（Edit View 專用，透過統一服務）"""
        try:
            glyphs_service = get_glyphs_service()
            return glyphs_service.get_visible_tab_layers()
            
        except Exception:
            print(traceback.format_exc())
            return []
    
    def _find_layer_in_tab_layers(self, char_or_name, visible_layers):
        """在分頁圖層中尋找匹配的圖層（Edit View 專用）"""
        try:
            if not visible_layers or not char_or_name:
                return None
            
            # 按順序檢查每個可見圖層
            for layer in visible_layers:
                if not layer or not hasattr(layer, 'parent'):
                    continue
                
                glyph = layer.parent
                if not glyph:
                    continue
                
                # 檢查字符匹配
                if self._does_glyph_match_char(glyph, char_or_name):
                    return layer
            
            return None
            
        except Exception:
            print(traceback.format_exc())
            return None
    
    def _does_glyph_match_char(self, glyph, char_or_name):
        """檢查字符是否匹配（Edit View 備份邏輯專用）"""
        try:
            if not glyph or not char_or_name:
                return False
            
            # 檢查字符名稱匹配
            if hasattr(glyph, 'name') and glyph.name == char_or_name:
                return True
            
            # 檢查 Unicode 匹配
            if hasattr(glyph, 'unicode') and glyph.unicode:
                try:
                    unicode_char = chr(int(glyph.unicode, 16))
                    if unicode_char == char_or_name:
                        return True
                except (ValueError, TypeError):
                    pass
            
            # 檢查單字符直接匹配
            if len(char_or_name) == 1:
                try:
                    char_unicode = ord(char_or_name)
                    if hasattr(glyph, 'unicode') and glyph.unicode:
                        glyph_unicode = int(glyph.unicode, 16)
                        if char_unicode == glyph_unicode:
                            return True
                except (ValueError, TypeError):
                    pass
            
            return False
            
        except Exception:
            print(traceback.format_exc())
            return False
    
    def _draw_grid_with_layout(self, layout, is_black, font, currentMaster):
        """使用佈局設計繪製九宮格（整合中央格進階邏輯）"""
        try:
            positions = layout['positions']
            arrangement = layout['arrangement']
            
            # === 繪製九宮格字符 ===
            for i in range(len(positions)):
                position_info = positions[i]
                
                # 從排列中取得字符
                char_or_name = arrangement[i] if i < len(arrangement) else None
                
                layer = None
                if char_or_name is not None:
                    if i == CENTER_POSITION:
                        # 中央格：根據視圖模式選擇策略
                        if self._is_in_font_view():
                            # Font View: 使用簡化邏輯（Light Table → 標準快取）
                            layer = self._get_center_layer(char_or_name, font)
                        else:
                            # Edit View: 使用完整備份機制（Light Table → tab.layers → 標準快取）
                            layer = self._get_center_layer_with_backup(char_or_name, font)
                    else:
                        # 周圍格：透過統一服務獲取
                        glyphs_service = get_glyphs_service()
                        glyph = glyphs_service.get_glyph_from_font(font, char_or_name)
                        if glyph and glyph.layers[currentMaster.id]:
                            layer = glyph.layers[currentMaster.id]
                
                # 繪製字符（如果有有效的layer）
                if layer:
                    # 繪製字符
                    self._draw_character_at_position(
                        layer, 
                        position_info['centerX'], 
                        position_info['centerY'], 
                        position_info['cellWidth'], 
                        position_info['cellHeight'], 
                        layout['metrics']['scale'], 
                        is_black
                    )
                else:
                    # None 值或無效字符：完全不繪製任何內容，保持背景色
                    pass
                    
        except Exception:
            print(traceback.format_exc())
    
    def _get_theme_is_black(self):
        """檢查目前主題是否為深色模式（基於 Georg Seifert 的建議）"""
        # 使用新的 tab 層級主題偵測器
        from ..core.theme_detector import get_current_theme_is_black
        return get_current_theme_is_black()
    
    def isFlipped(self):
        """使用標準座標系統（Y 軸向上為正）"""
        return False

    
    # ==========================================================================
    # 其他事件處理
    # ==========================================================================
    
    
    def setFrame_(self, frame):
        """覆寫 setFrame_ 方法（官方模式）"""
        # 記錄舊框架
        oldFrame = self.frame()
        
        # 呼叫父類別方法
        objc.super(NineBoxPreviewView, self).setFrame_(frame)
        
        # 如果框架大小改變，觸發重繪
        if (oldFrame.size.width != frame.size.width or 
            oldFrame.size.height != frame.size.height):
            
            # 清除必要快取
            self._clear_essential_caches()
            
            # 觸發重繪
            self._trigger_redraw()
    
    def force_full_redraw(self):
        """強制完整重繪（用於檔案切換）"""
        # 清除所有快取
        self._clear_essential_caches()
        
        # 清除額外的狀態
        if hasattr(self, '_width_change_cache'):
            self._width_change_cache.clear()
        
        # 觸發重繪
        self._trigger_redraw()
    
    # ==========================================================================
    # 滑鼠事件處理（修復左鍵點擊隨機排列功能）
    # ==========================================================================
    
    def mouseDown_(self, event):
        """處理滑鼠左鍵點擊事件，觸發隨機排列

        左鍵點擊九宮格字符位置觸發隨機排列功能（減法重構：複用右鍵偵測邏輯）
        包含防抖機制，避免聚焦後立即點擊導致的雙重隨機排列

        Args:
            event: 滑鼠點擊事件
        """
        try:
            # 防抖檢查：避免與 UPDATEINTERFACE 事件衝突
            current_time = time.monotonic()
            if current_time - self._last_randomize_time < self._debounce_interval:
                return  # 在防抖間隔內，忽略這次點擊

            # 取得點擊位置
            click_point = event.locationInWindow()
            view_point = self.convertPoint_fromView_(click_point, None)

            # 使用現有的九宮格點擊偵測邏輯（減法重構：統一而非新增）
            from ..core.menu_manager import MenuManager
            grid_index = MenuManager.get_grid_index_at_point(self, view_point)

            # 只在九宮格有效範圍內觸發隨機排列
            if grid_index is None:
                return  # 點擊位置不在九宮格範圍內

            # 更新防抖時間戳
            self._last_randomize_time = current_time

            # 在九宮格範圍內點擊時，觸發隨機排列
            self.window().makeKeyWindow()
            self.window().makeFirstResponder_(self)

            # 呼叫 plugin 的隨機排列回呼方法
            if hasattr(self.plugin, 'randomizeAction_'):
                self.plugin.randomizeAction_(self)
            else:
                # 如果沒有回呼方法，通過統一入口觸發隨機排列
                if hasattr(self.plugin, 'event_handler'):
                    self.plugin.event_handler.update_and_redraw_grid(force_randomize=True)

        except Exception:
            print(traceback.format_exc())
    
    def rightMouseDown_(self, event):
        """處理滑鼠右鍵點擊事件，顯示右鍵選單
        
        委派給 MenuManager 處理所有右鍵邏輯
        
        Args:
            event: 滑鼠右鍵點擊事件
        """
        try:
            from ..core.menu_manager import MenuManager
            MenuManager.handle_right_mouse_click(self, event)
        except Exception:
            print(traceback.format_exc())
    
    # ==========================================================================
    # 右鍵選單動作處理方法
    # ==========================================================================
    
    def copyGlyphName_(self, sender):
        """複製字符名稱動作處理"""
        try:
            from ..core.menu_manager import MenuManager
            glyph_name = sender.representedObject()
            MenuManager.copy_glyph_name(glyph_name)
        except Exception:
            print(traceback.format_exc())
    
    def insertGlyphToCurrentTab_(self, sender):
        """插入字符到目前分頁動作處理"""
        try:
            from ..core.menu_manager import MenuManager
            char_info = sender.representedObject()
            MenuManager.insert_glyph_to_current_tab(char_info)
        except Exception:
            print(traceback.format_exc())
    
    def openGlyphInNewTab_(self, sender):
        """在新分頁開啟字符動作處理"""
        try:
            from ..core.menu_manager import MenuManager
            glyph = sender.representedObject()
            MenuManager.open_glyph_in_new_tab(glyph)
        except Exception:
            print(traceback.format_exc())
    
    
    # ==========================================================================
    # 中央格處理方法（整合 Light Table 支援）
    # ==========================================================================
    
    def _get_center_layer(self, char_or_name, font):
        """
        取得中央格顯示圖層（Font View 簡化版本）
        
        Font View 邏輯：Light Table 且 Shift → 比較版本，否則標準快取
        
        Args:
            char_or_name (str): 字符或字符名稱
            font: 當前字型
            
        Returns:
            GSLayer or None: 中央格要顯示的圖層
        """
        try:
            # 基本類型檢查
            if not isinstance(char_or_name, str):
                return None
                        
            # 透過統一服務獲取字符
            glyphs_service = get_glyphs_service()
            glyph = glyphs_service.get_glyph_from_font(font, char_or_name)
            if glyph and font.selectedFontMaster:
                return glyph.layers[font.selectedFontMaster.id]
            
            return None
                
        except Exception:
            print(traceback.format_exc())
            return None
    
    def _get_center_layer_with_backup(self, char_or_name, font):
        """
        取得中央格顯示圖層（Edit View 完整備份版本）
        
        Edit View 三層備份機制：
        1. Light Table 比較版本（如果啟用且按下 Shift）
        2. tab.layers 備份機制（Edit View 模式）
        3. 標準 cache 機制（最後復原）
        
        Args:
            char_or_name (str): 字符或字符名稱
            font: 當前字型
            
        Returns:
            GSLayer or None: 中央格要顯示的圖層
        """
        try:
            # 基本類型檢查
            if not isinstance(char_or_name, str):
                return None
            
            # === 第一層：Light Table 比較版本 ===
            from ..core.light_table_support import should_use_comparison_version, get_comparison_font
            
            if should_use_comparison_version(font):
                comparison_font = get_comparison_font(font)
                if comparison_font:
                    glyphs_service = get_glyphs_service()
                    glyph = glyphs_service.get_glyph_from_font(comparison_font, char_or_name)
                    if glyph and font.selectedFontMaster:
                        try:
                            return glyph.layers[font.selectedFontMaster.id]
                        except (KeyError, IndexError):
                            # Master ID 不匹配時使用第一個圖層
                            return glyph.layers[0] if glyph.layers else None
            
            # === 第二層：tab.layers 備份機制（Edit View 專用）===
            visible_layers = self._get_visible_tab_layers()
            layer = self._find_layer_in_tab_layers(char_or_name, visible_layers)
            if layer:
                return layer
            
            # === 第三層：標準 cache 機制 ===
            glyphs_service = get_glyphs_service()
            glyph = glyphs_service.get_glyph_from_font(font, char_or_name)
            if glyph and font.selectedFontMaster:
                return glyph.layers[font.selectedFontMaster.id]
            
            return None
                
        except Exception:
            print(traceback.format_exc())
            return None



# =============================================================================
# 工廠函數（符合原始穩定版模式）
# =============================================================================

def create_preview_view(posSize, plugin):
    """建立預覽視圖（整合進階重繪機制）
    
    Args:
        posSize (tuple): 位置和大小 (x, y, w, h)
        plugin: NineBoxPluginController 實例
        
    Returns:
        NineBoxPreviewView: 整合進階重繪機制的預覽視圖實例
    """
    from Foundation import NSMakeRect
    
    x, y, w, h = posSize
    frame = NSMakeRect(x, y, w, h)
    return NineBoxPreviewView.alloc().initWithFrame_plugin_(frame, plugin)