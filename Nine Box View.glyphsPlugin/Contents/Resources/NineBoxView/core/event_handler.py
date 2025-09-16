# encoding: utf-8

"""
九宮格預覽外掛 - 事件處理器
基於原版 EventHandlers 的完整復刻，適配平面座標系統
"""

from __future__ import division, print_function, unicode_literals
from GlyphsApp import Glyphs
import traceback

# 平面座標系統常數
CENTER_POSITION = 4  # 中央位置
GRID_SIZE_TOTAL = 9  # 總共9個位置 (0-8)

class NineBoxEventHandler:
    """
    九宮格外掛事件處理器
    基於原版 EventHandlers，適配平面座標系統
    """
    
    def __init__(self, plugin):
        """初始化事件處理器"""
        self.plugin = plugin
        
        # 註冊官方回呼系統
        self._register_font_change_callbacks()
    
    def update_interface(self, sender):
        """檔案內即時更新處理（UPDATEINTERFACE 事件）"""
        try:
            # 使用新的視窗通訊介面檢查視窗狀態
            if not self.plugin.has_active_window():
                return
            
            # 執行九宮格自動同步（檔案內即時操作，使用快速重繪）
            self.update_and_redraw_grid()
            
        except Exception:
            print(traceback.format_exc())

        # 避免 sender 參數未使用警告
        _ = sender
    
    def handle_document_opened(self, sender):
        """處理文件開啟事件（DOCUMENTOPENED）- 完整初始化"""
        try:
            # 使用新的視窗通訊介面檢查視窗狀態
            if not self.plugin.has_active_window():
                return
            
            # 檔案開啟時偵測字型並處理無效字符
            font_changed = self._detect_and_handle_font_change()
            
            # 根據字型檢查結果決定重繪策略
            if font_changed:
                # 有字型變更或初次檢查：使用智慧填充
                self.update_and_redraw_grid(skip_randomize=False, force_font_change_fill=True)
            else:
                # 一般重繪
                self.update_and_redraw_grid()
            
            # 檔案開啟時主動執行視覺標注（整合字型變更偵測）
            try:
                from .input_recognition import VisualFeedbackService
                # 使用增強的字型變更響應方法
                VisualFeedbackService.refresh_all_annotations_on_font_change(self.plugin)
            except Exception:
                print(traceback.format_exc())

        except Exception:
            print(traceback.format_exc())

        # 避免 sender 參數未使用警告
        _ = sender

    def handle_document_activated(self, sender):
        """處理文件啟動事件（DOCUMENTACTIVATED）- 字型切換智慧處理"""
        try:
            # 使用新的視窗通訊介面檢查視窗狀態
            if not self.plugin.has_active_window():
                return
            
            # 字型切換偵測和智慧處理
            font_changed = self._detect_and_handle_font_change()
            
            # 如果字型有變更，觸發智慧填充；否則執行一般同步
            if font_changed:
                # 字型變更時：使用智慧填充邏輯
                self.update_and_redraw_grid(skip_randomize=False, force_font_change_fill=True)
            else:
                # 一般檔案切換：跳過隨機排列，保持現有內容
                self.update_and_redraw_grid(skip_randomize=True)
            
            # 檔案切換時主動執行視覺標注（整合字型變更偵測）
            try:
                from .input_recognition import VisualFeedbackService
                # 使用增強的字型變更響應方法
                VisualFeedbackService.refresh_all_annotations_on_font_change(self.plugin)
            except Exception:
                print(traceback.format_exc())

        except Exception:
            print(traceback.format_exc())

        # 避免 sender 參數未使用警告
        _ = sender
    
    def search_field_callback(self, sender):
        """搜尋欄位輸入處理（使用集中式防護機制）"""
        try:
            # 取得搜尋文字
            search_text = sender.stringValue() if sender else ""
            
            # 委派給統一的輸入防護服務
            from .input_recognition import InputGuardService
            
            def update_callback(chars):
                """更新回呼：填充字符到九宮格"""
                self._fill_grid_from_chars(chars)
                self.update_and_redraw_grid()
            
            def randomize_callback():
                """隨機化回呼：觸發隨機排列"""
                self.update_and_redraw_grid(force_randomize=True)
            
            # 使用防護機制處理輸入
            result = InputGuardService.process_search_input(
                search_text, 
                self.plugin, 
                update_callback, 
                randomize_callback
            )
            
            # 根據處理結果決定是否儲存狀態
            if result['processed']:
                self.plugin.savePreferences()
            
        except Exception:
            print(traceback.format_exc())

    def _fill_grid_from_chars(self, chars):
        """從字符列表隨機填充九宮格（使用隨機排列服務）"""
        try:
            # 兩層架構：使用 GridManager 填充基礎排列層
            if (hasattr(self.plugin, 'grid_manager') and 
                self.plugin.grid_manager and chars):
                
                # 先同步基礎排列層到 GridManager
                self.plugin.grid_manager.grid_glyphs = self.plugin.base_arrangement[:]
                
                # 獲取所有位置（包含中央位置）
                all_positions = [0, 1, 2, 3, 4, 5, 6, 7, 8]
                
                # 使用隨機服務填充所有位置
                changed = self.plugin.grid_manager.randomize_positions(all_positions, chars)
                if changed:
                    # 同步 GridManager 的結果到基礎排列層
                    self.plugin.base_arrangement = self.plugin.grid_manager.displayArrangement()
            else:
                # 復原方案：使用隨機排列服務
                try:
                    from .random_arrangement import get_random_service
                    random_service = get_random_service()
                    if random_service and chars:
                        all_positions = [0, 1, 2, 3, 4, 5, 6, 7, 8]
                        random_chars = random_service.create_non_repeating_batch(chars, len(all_positions))
                        for i, pos in enumerate(all_positions):
                            self.plugin.base_arrangement[pos] = random_chars[i] if i < len(random_chars) else ''
                    else:
                        raise ImportError("隨機服務不可用")
                except ImportError:
                    # 最終復原方案：填充基礎排列層
                    positions = [0, 1, 2, 3, 4, 5, 6, 7, 8]
                    for i, pos in enumerate(positions):
                        if i < len(chars):
                            self.plugin.base_arrangement[pos] = chars[i]
                        else:
                            self.plugin.base_arrangement[pos] = chars[i % len(chars)]
        except Exception:
            print(traceback.format_exc())
            # 安全復原：直接操作基礎排列層
            positions = [0, 1, 2, 3, 4, 5, 6, 7, 8]
            for i, pos in enumerate(positions):
                if i < len(chars):
                    self.plugin.base_arrangement[pos] = chars[i]
                else:
                    self.plugin.base_arrangement[pos] = chars[i % len(chars)]
    
    
    def handle_lock_field_change(self, field, text):
        """處理鎖定輸入框變更（修復：儲存原始輸入，顯示時才解析）"""
        try:
            position = field.position
            
            # 第一層防護：變更檢查（防止重複處理相同輸入）
            current_lock_value = getattr(self.plugin, 'lock_inputs', [None] * 9)[position] if hasattr(self.plugin, 'lock_inputs') else None
            if current_lock_value == text:
                return  # 沒有變更，直接返回
            
            # 第二層處理：儲存原始輸入內容（不進行解析簡化）
            if hasattr(self.plugin, 'lock_inputs'):
                current_lock_char = self.plugin.lock_inputs[position]
                
                if text != current_lock_char:
                    # 儲存使用者的完整原始輸入
                    self.plugin.lock_inputs[position] = text
                    
                    # 只在上鎖狀態時觸發重繪（解鎖狀態下只更新資料不重繪）
                    if self.plugin.isLockFieldsActive:
                        self.update_and_redraw_grid(skip_randomize=True)
                    
                    # 儲存狀態
                    self.plugin.savePreferences()
            
        except Exception:
            print(traceback.format_exc())
    
    def update_lock_mode_display(self):
        """更新鎖定模式顯示 - 減法重構：純粹的重繪方法"""
        try:
            # 純粹的顯示重繪，不觸發隨機排列
            self.update_and_redraw_grid(skip_randomize=True)
        except Exception:
            print(traceback.format_exc())

    def clear_locked_positions(self):
        """清除所有鎖定位置（減法重構：不觸發隨機排列）"""
        try:
            # 清空鎖定數組（排除中央位置）
            positions = [0, 1, 2, 3, 5, 6, 7, 8]
            for pos in positions:
                self.plugin.lock_inputs[pos] = ''
            
            # 鎖定操作不應觸發隨機排列，只需重繪即可
            self.update_and_redraw_grid(skip_randomize=True)
            
        except Exception:
            print(traceback.format_exc())

    def get_selected_glyph(self):
        """取得當前選中的字符（採用官方模式統一上下文）
        
        使用官方推薦的 selectedLayers 偵測
        沒有選擇時返回 None，由顯示邏輯處理空字符狀態
        """
        from .utils import FontManager
        font, _ = FontManager.getCurrentFontContext()
        if Glyphs and font and font.selectedLayers:
            layer = font.selectedLayers[0]
            if layer and layer.parent:
                return layer.parent.name
        
        return None  # 沒有選中任何字符，顯示為空
    
    # ==========================================================================
    # 中央格自動同步機制
    # ==========================================================================
    
    def update_and_redraw_grid(self, skip_randomize=False, force_randomize=False, force_font_change_fill=False):
        """更新並重繪九宮格（減法重構：統一的重繪協調器 + 字型變更處理）
        
        統一的九宮格重繪協調器，負責：
        - 寬度變更偵測與即時重繪（整合到統一流程中）
        - 條件性隨機排列控制：force_randomize（強制）/ skip_randomize（跳過）/ 條件判斷
        - 字型變更智慧填充：force_font_change_fill（字型切換時的特殊處理）
        - 資料同步：更新預覽視圖的排列資料
        - 智慧重繪策略：寬度變更時 refresh()，否則 setNeedsDisplay_()
        
        Args:
            skip_randomize: True時跳過隨機排列（用於鎖定操作）
            force_randomize: True時強制隨機排列（用於明確的隨機操作）
            force_font_change_fill: True時字型變更觸發的智慧填充（已在偵測階段處理）
        """
        try:
            # === 寬度變更偵測（整合到統一流程）===
            width_changed = self._detect_width_changes()
            
            # 檢查是否有可用的九宮格排列（檢查基礎排列層）
            if not hasattr(self.plugin, 'base_arrangement') or not any(self.plugin.base_arrangement):
                # 如果沒有九宮格，生成初始排列（這種情況必須生成）
                self.plugin.randomize_grid()
                return
            
            # 統一的隨機排列邏輯：明確控制何時隨機排列（含字型變更處理）
            should_randomize = (
                force_randomize or  # 強制隨機（清除鎖定、點擊預覽等）
                (not skip_randomize and not self.plugin.has_valid_search_input() and not force_font_change_fill)  # 條件隨機（只有沒有有效輸入時）
            )
            
            if should_randomize:
                self.plugin.randomize_grid()
            elif force_font_change_fill:
                # 字型變更時：無效字符已在偵測階段被替換，這裡只需要確保資料同步
                # 不觸發隨機排列，保持現有的智慧填充結果
                pass
            
            # 確保 base_glyphs 資料是最新的
            if hasattr(self.plugin, '_update_base_glyphs'):
                self.plugin._update_base_glyphs()
            
            # 使用新的視窗通訊介面更新預覽視圖
            if self.plugin.has_active_window():
                # 更新預覽視圖的排列資料
                self.plugin.update_preview_view()
                
                # 根據寬度變更決定重繪策略
                self.plugin.trigger_preview_redraw(use_refresh=width_changed)
            
            # 使用官方重繪方法（會重繪所有視圖，包括周圍格）
            Glyphs.redraw()
            
        except Exception:
            print(traceback.format_exc())

    def _detect_width_changes(self):
        """寬度變更偵測（統一到 EventHandler 中）
        
        整合雙重偵測機制：GridManager 主偵測 + cache 模組復原偵測
        
        Returns:
            bool: True 如果偵測到寬度變更
        """
        try:
            width_changed = False
            
            # 主要偵測：使用 GridManager
            if (hasattr(self.plugin, 'grid_manager') and 
                self.plugin.grid_manager):
                try:
                    width_changed = self.plugin.grid_manager.detect_width_changes()
                except Exception:
                    print(traceback.format_exc())

            # 復原偵測：直接使用 cache 模組
            if not width_changed:
                try:
                    from NineBoxView.data.cache import create_width_change_detector
                    from NineBoxView.core.utils import FontManager
                    
                    if create_width_change_detector:
                        detector = create_width_change_detector()
                        font, master = FontManager.getCurrentFontContext()
                        if font and master and detector:
                            arrangement = self.plugin.displayArrangement() if hasattr(self.plugin, 'displayArrangement') else []
                            width_changed = detector(font, arrangement, master)
                except Exception:
                    print(traceback.format_exc())

            return width_changed
            
        except Exception:
            print(traceback.format_exc())
            return False
    
    # ==========================================================================
    # 字型變更偵測和智慧處理
    # ==========================================================================
    
    def _detect_and_handle_font_change(self):
        """偵測字型變更並處理無效字符
        
        Returns:
            bool: True 如果偵測到字型變更
        """
        try:
            # 獲取當前字型上下文
            from .utils import FontManager
            current_font, current_master = FontManager.getCurrentFontContext()
            
            if not current_font:
                return False
            
            # 檢查是否有上次的字型記錄
            last_font_id = getattr(self.plugin, '_last_font_id', None)
            current_font_id = id(current_font)
            
            # 更新字型記錄
            self.plugin._last_font_id = current_font_id
            
            # 如果字型有變更，或者是初次檢查
            if (last_font_id is None) or (last_font_id != current_font_id):
                # 處理字型變更：檢查並替換無效字符
                self._handle_invalid_characters_on_font_change(current_font, current_master)
                return True
                
            return False
            
        except Exception:
            print(traceback.format_exc())
            return False
    
    def _handle_invalid_characters_on_font_change(self, new_font, new_master):
        """處理字型變更時的無效字符（分層檢查和處理）
        
        Args:
            new_font: 新的字型物件
            new_master: 新的 Master 物件
        """
        try:
            from NineBoxView.data.cache import get_glyph_with_fallback
            
            # === 第一階段：分別檢查兩層的無效字符 ===
            invalid_lock_positions = []    # 鎖定層無效位置
            invalid_base_positions = []    # 第二層無效位置
            
            # 檢查鎖定層
            for pos in range(GRID_SIZE_TOTAL):
                if pos != CENTER_POSITION and self.plugin.lock_inputs[pos]:
                    char = self.plugin.lock_inputs[pos].strip()
                    if char:
                        glyph = get_glyph_with_fallback(new_font, char, new_master)
                        if not glyph:
                            invalid_lock_positions.append(pos)
            
            # 檢查第二層（獨立檢查，不受鎖定層影響）
            for pos in range(GRID_SIZE_TOTAL):
                if self.plugin.base_arrangement[pos]:
                    char = self.plugin.base_arrangement[pos]
                    glyph = get_glyph_with_fallback(new_font, char, new_master)
                    if not glyph:
                        invalid_base_positions.append(pos)
            
            # === 第二階段：分層處理 ===
            # 處理鎖定層：暫時跳過修改，保留檢查用於視覺標註
            # 注意：invalid_lock_positions 保留給視覺標註系統使用
            _ = invalid_lock_positions  # 避免未使用變數警告
            
            # 處理第二層
            if invalid_base_positions:
                self._fill_base_arrangement_positions(invalid_base_positions, new_font, new_master)
                
        except Exception:
            print(traceback.format_exc())
    
    def _get_available_chars_from_font(self, font, plugin):
        """從用戶的 lastInput 獲取在新字型中有效的字符列表
        
        Args:
            font: 新字型物件
            plugin: 插件實例（用於獲取 lastInput）
            
        Returns:
            list: 從 lastInput 中提取的在新字型中有效的字符列表
        """
        try:
            if not font or not font.glyphs or not plugin:
                return []
            
            # 唯一來源：plugin.lastInput
            last_input = getattr(plugin, 'lastInput', '')
            if not last_input or not last_input.strip():
                return []  # lastInput 為空，返回空列表
            
            # 解析 lastInput 中的字符（使用現有的解析邏輯）
            try:
                from NineBoxView.core.input_recognition import parse_glyph_input
                from NineBoxView.core.utils import FontManager
                
                # 獲取當前 master 用於解析
                _, master = FontManager.getCurrentFontContext()
                parsed_chars = parse_glyph_input(last_input, master=master)
                
                if not parsed_chars:
                    return []  # 解析失敗，返回空列表
                
            except ImportError:
                # 復原：簡單按空格分割
                parsed_chars = last_input.strip().split()
            
            # 驗證字符在新字型中的有效性
            from NineBoxView.data.cache import get_glyph_with_fallback
            valid_chars = []
            
            for char in parsed_chars:
                if char and char.strip():
                    # 檢查字符在新字型中是否存在
                    glyph = get_glyph_with_fallback(font, char.strip())
                    if glyph:
                        valid_chars.append(char.strip())
            
            return valid_chars
            
        except Exception:
            print(traceback.format_exc())
            return []
    
    def _fill_base_arrangement_positions(self, positions, font, master):
        """專門處理第二層 base_arrangement 的無效字符替換
        
        Args:
            positions: 需要填充的第二層位置列表
            font: 新字型物件
            master: 新 Master 物件（用於快取鍵生成）
        """
        try:
            # 從用戶的 lastInput 獲取在新字型中有效的字符
            available_chars = self._get_available_chars_from_font(font, self.plugin)
            
            # 避免未使用參數警告（master 保留供未來快取功能使用）
            _ = master
            
            if not available_chars:
                # 沒有有效字符時清空第二層
                for pos in positions:
                    self.plugin.base_arrangement[pos] = ''
                return
            
            # 使用修復後的索引邏輯填充第二層
            try:
                from NineBoxView.core.random_arrangement import get_random_service
                random_service = get_random_service()
                if random_service:
                    # 生成隨機字符用於填充
                    random_chars = random_service.create_non_repeating_batch(available_chars, len(positions))
                    
                    # 使用獨立字符索引填充第二層
                    char_index = 0
                    for pos in positions:
                        if char_index < len(random_chars):
                            # 直接處理第二層，不考慮鎖定狀態
                            self.plugin.base_arrangement[pos] = random_chars[char_index]
                            char_index += 1
                else:
                    # 復原方案：使用獨立索引的循環分配
                    char_index = 0
                    for pos in positions:
                        if char_index < len(available_chars):
                            char = available_chars[char_index % len(available_chars)]
                            self.plugin.base_arrangement[pos] = char
                            char_index += 1
                            
            except ImportError:
                # 最終復原：使用獨立索引循環分配
                char_index = 0
                for pos in positions:
                    if char_index < len(available_chars):
                        char = available_chars[char_index % len(available_chars)]
                        self.plugin.base_arrangement[pos] = char
                        char_index += 1
                        
        except Exception:
            print(traceback.format_exc())
    
    # ==========================================================================
    # 官方回呼系統整合
    # ==========================================================================
    
    def _register_font_change_callbacks(self):
        """註冊字型變更回呼（使用官方 Glyphs API）"""
        try:
            from .glyphs_service import get_glyphs_service
            glyphs_service = get_glyphs_service()
            
            # 註冊官方回呼
            success = glyphs_service.register_font_change_callback(self)
            if success:
                pass
                
        except Exception:
            print(traceback.format_exc())
    
    def handle_document_saved(self, notification):
        """處理文件保存事件（官方回呼）
        
        Args:
            notification: Glyphs 通知物件
        """
        try:
            # 文件保存時也可能影響字符有效性（例如新增字符）
            from .input_recognition import VisualFeedbackService
            VisualFeedbackService.refresh_all_annotations_on_font_change(self.plugin)
            
        except Exception:
            print(traceback.format_exc())

        # 避免 notification 參數未使用警告
        _ = notification
    
    def handle_document_will_close(self, sender):
        """處理文件即將關閉事件（DOCUMENTWILLCLOSE）
        
        檢查是否所有字型檔案都即將關閉，如果是則清空預覽畫面
        
        Args:
            sender: Glyphs 通知物件
        """
        try:
            # 使用 GlyphsService 檢查是否即將關閉最後一個字型檔案
            from .glyphs_service import get_glyphs_service
            glyphs_service = get_glyphs_service()
            
            # 檢查關閉後是否還會有其他字型檔案開啟
            # 注意：在 DOCUMENTWILLCLOSE 事件中，目的檔尚未實際關閉
            # 所以我們需要檢查關閉這個文件後是否還會有其他文件
            if glyphs_service.is_last_font_closing():
                # 如果這是最後一個字型檔案即將關閉，清空預覽內容
                self._clear_preview_content()
            
        except Exception:
            print(traceback.format_exc())

        # 避免 sender 參數未使用警告
        _ = sender
    
    def _clear_preview_content(self):
        """清空預覽畫面的視覺內容，但保留使用者設定
        
        修復：檔案關閉時僅清空視覺內容，保留使用者的設定
        - 保留 lastInput：使用者的搜尋記錄
        - 保留 lock_inputs：使用者的鎖定輸入框設定
        - 清空 base_glyphs 和 base_arrangement：僅清空顯示內容
        """
        try:
            # 僅清空視覺顯示相關的資料結構（保留使用者設定）
            self.plugin.base_glyphs = [''] * GRID_SIZE_TOTAL
            self.plugin.base_arrangement = [''] * GRID_SIZE_TOTAL  
            
            # 保留使用者設定：
            # - self.plugin.lock_inputs 不清空（保留使用者的鎖定輸入框設定）
            # - self.plugin.lastInput 不清空（保留使用者的搜尋記錄）
            
            # 清空所有視覺標注（字型關閉時的特殊處理）
            try:
                from .input_recognition import VisualFeedbackService
                VisualFeedbackService.clear_all_annotations_on_font_close(self.plugin)
            except Exception:
                print(traceback.format_exc())
            
            # 如果有活動視窗，觸發重繪以顯示空內容
            if self.plugin.has_active_window():
                # 更新預覽視圖為空排列
                self.plugin.update_preview_view([''] * GRID_SIZE_TOTAL)
                
                # 觸發重繪
                self.plugin.trigger_preview_redraw(use_refresh=True)
            
            # 儲存狀態（現在只儲存視覺內容的清空，使用者設定保持不變）
            self.plugin.savePreferences()
            
        except Exception:
            print(traceback.format_exc())

    def cleanup(self):
        """清理事件處理器（移除回呼）"""
        try:
            from .glyphs_service import get_glyphs_service
            glyphs_service = get_glyphs_service()
            
            # 移除官方回呼
            success = glyphs_service.unregister_font_change_callback(self)
            if success:
                pass

        except Exception:
            print(traceback.format_exc())