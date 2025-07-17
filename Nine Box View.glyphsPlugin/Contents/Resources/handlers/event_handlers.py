# encoding: utf-8
"""
九宮格預覽外掛 - 事件處理器
Nine Box Preview Plugin - Event Handlers
"""

from __future__ import division, print_function, unicode_literals
import traceback
import random
from GlyphsApp import Glyphs, PickGlyphs, GSGlyph
from AppKit import NSTextField
from core.constants import DEBUG_MODE, DEFAULT_ZOOM, FULL_ARRANGEMENT_SIZE, CENTER_POSITION, SURROUNDING_POSITIONS
from core.utils import debug_log, error_log, parse_input_text, generate_arrangement, validate_locked_positions, get_cached_glyph, generate_non_repeating_batch

class EventHandlers:
    """集中管理所有事件處理邏輯"""
    
    def __init__(self, plugin):
        self.plugin = plugin
        # 新增細粒度更新標記，防止重繪時意外觸發其他邏輯
        self._performing_granular_update = False
        
    
    # === 介面更新 ===
    
    def update_interface(self, sender):
        """更新介面（官方模式 + 批次處理最佳化）"""
        try:
            # 避免重複更新
            if self.plugin._update_scheduled:
                return
            
            if hasattr(self.plugin, 'windowController') and self.plugin.windowController is not None:
                # 使用官方 API 的批次處理機制
                font = Glyphs.font
                if font:
                    font.disableUpdateInterface()
                
                try:
                    # 批次更新標記
                    self.plugin._update_scheduled = True
                    
                    # 特殊情況處理：沒有選擇字符但有鎖定字符
                    if (not self.plugin.selectedChars and hasattr(self.plugin, 'lockedChars') and 
                        self.plugin.lockedChars and not self._get_lock_state()):
                        debug_log("沒有選擇字符，但在上鎖狀態下有鎖定字符，重新生成排列")
                        self.generate_new_arrangement()
                    
                    # 直接同步當前排列到預覽視圖 (增強型)
                    if (hasattr(self.plugin.windowController, 'previewView') and 
                        self.plugin.windowController.previewView is not None):
                        # 同步當前排列到預覽視圖
                        if hasattr(self.plugin, 'currentArrangement'):
                            debug_log("update_interface: 同步 currentArrangement 到預覽視圖")
                            self.plugin.windowController.previewView.currentArrangement = self.plugin.currentArrangement
                        # 同步縮放因子到預覽視圖
                        if hasattr(self.plugin, 'zoomFactor'):
                            self.plugin.windowController.previewView.zoomFactor = self.plugin.zoomFactor
                    
                    # 官方模式：觸發重繪
                    if hasattr(self.plugin.windowController, 'update'):
                        debug_log("update_interface: 強制觸發重繪")
                        self.plugin.windowController.update()
                    
                    # 更新控制面板 - 一般情況下不更新鎖定輸入框
                    if hasattr(self.plugin.windowController, 'request_controls_panel_ui_update'):
                        self.plugin.windowController.request_controls_panel_ui_update(update_lock_fields=False)
                        
                finally:
                    # 確保重新啟用介面更新和重置標記
                    if font:
                        font.enableUpdateInterface()
                    self.plugin._update_scheduled = False
                
        except Exception as e:
            self.plugin._update_scheduled = False
            error_log("更新介面時發生錯誤", e)
    
    def selection_changed(self, sender):
        """選擇變更處理（只更新中心格，保持周圍格不變）"""
        try:
            # 清除快取
            if hasattr(self.plugin, 'clear_cache'):
                self.plugin.clear_cache()
            
            # 獲取新的 activeGlyph
            new_active_glyph = self._get_current_editing_char()
            debug_log(f"字符選擇變更，新的 activeGlyph: {new_active_glyph}")
            
            # 智慧更新：只更新中心格，保持周圍格穩定
            self._update_center_position_only(new_active_glyph)
            
            # 確保預覽視圖更新 - 如果主視窗已顯示則直接更新預覽
            if (hasattr(self.plugin, 'windowController') and 
                self.plugin.windowController is not None):
                
                # 更新 preview view 的屬性設定器 (確保同步)
                if (hasattr(self.plugin.windowController, 'previewView') and 
                    self.plugin.windowController.previewView is not None):
                    # 同步當前排列到預覽視圖
                    if hasattr(self.plugin, 'currentArrangement'):
                        self.plugin.windowController.previewView.currentArrangement = self.plugin.currentArrangement
                        debug_log("已同步 currentArrangement 到預覽視圖")
                    # 同步縮放因子到預覽視圖
                    if hasattr(self.plugin, 'zoomFactor'):
                        self.plugin.windowController.previewView.zoomFactor = self.plugin.zoomFactor
                
                # 官方模式：使用標準更新方法強制重繪
                self.plugin.windowController.update()
                debug_log("已強制重繪預覽視圖")
            
            # 更新介面
            self.update_interface(None)
            
            # 更新控制面板（僅更新搜尋欄位，不更新鎖定輸入框）
            if (hasattr(self.plugin, 'windowController') and 
                self.plugin.windowController is not None and
                hasattr(self.plugin.windowController, 'controlsPanelView') and 
                self.plugin.windowController.controlsPanelView is not None and
                hasattr(self.plugin.windowController, 'controlsPanelVisible') and
                self.plugin.windowController.controlsPanelVisible):
                
                self.plugin.windowController.controlsPanelView.update_ui(self.plugin, update_lock_fields=False)
                
        except Exception as e:
            error_log("選擇變更處理錯誤", e)
    
    # === 搜尋欄位相關 ===
    
    def search_field_callback(self, sender):
        """處理搜尋欄位輸入"""
        if not Glyphs.font:
            debug_log("警告：沒有開啟字型檔案")
            return

        input_text = sender.stringValue()
        
        # 檢查是否有變更
        if hasattr(self.plugin, 'lastInput') and self.plugin.lastInput == input_text:
            return
        
        # 更新 lastInput
        self.plugin.lastInput = input_text

        # 有輸入內容時的處理
        if input_text:
            new_chars = parse_input_text(input_text)
            
            # 確保 selectedChars 是可變列表
            if hasattr(self.plugin, 'selectedChars'):
                self.plugin.selectedChars = list(self.plugin.selectedChars) if self.plugin.selectedChars else []
                
            if new_chars != self.plugin.selectedChars:
                self.plugin.selectedChars = new_chars
                self.generate_new_arrangement()
        else:
            # 輸入為空時的處理
            is_in_clear_mode = self._get_lock_state()
            has_locked_chars = hasattr(self.plugin, 'lockedChars') and self.plugin.lockedChars
            
            # 確保 selectedChars 是可變列表
            if hasattr(self.plugin, 'selectedChars'):
                self.plugin.selectedChars = list(self.plugin.selectedChars) if self.plugin.selectedChars else []
                
            self.plugin.selectedChars = []  # 清空selectedChars
            
            # 修改：當搜索框為空時，使用當前編輯字符填充所有位置
            current_char = self._get_current_editing_char()
            debug_log(f"搜索框被清空，使用當前字符 '{current_char}' 填充")
            
            if not is_in_clear_mode and has_locked_chars:
                # 上鎖狀態且有鎖定字符，重新生成排列
                self.generate_new_arrangement()
            else:
                # 解鎖狀態或沒有鎖定字符：直接用當前字符填充
                self.plugin.currentArrangement = [current_char] * FULL_ARRANGEMENT_SIZE
                self.plugin.savePreferences()

        # 更新介面與控制面板
        self.update_interface_for_search_field(None)
        
        # 更新控制面板但不更新鎖定輸入框
        if hasattr(self.plugin, 'windowController') and self.plugin.windowController:
            if hasattr(self.plugin.windowController, 'request_controls_panel_ui_update'):
                self.plugin.windowController.request_controls_panel_ui_update(update_lock_fields=False)
    
    def update_interface_for_search_field(self, sender):
        """專為搜尋欄位的更新（官方模式）- 增強型"""
        try:
            if hasattr(self.plugin, 'windowController') and self.plugin.windowController is not None:
                # 同步資料到預覽視圖
                if (hasattr(self.plugin.windowController, 'previewView') and 
                    self.plugin.windowController.previewView is not None):
                    # 同步當前排列到預覽視圖
                    if hasattr(self.plugin, 'currentArrangement'):
                        debug_log("update_interface_for_search_field: 同步 currentArrangement 到預覽視圖")
                        self.plugin.windowController.previewView.currentArrangement = self.plugin.currentArrangement
                    # 同步縮放因子到預覽視圖
                    if hasattr(self.plugin, 'zoomFactor'):
                        self.plugin.windowController.previewView.zoomFactor = self.plugin.zoomFactor
                
                # 官方模式：使用標準更新方法
                self.plugin.windowController.update()
                debug_log("update_interface_for_search_field: 已觸發強制重繪")
        except Exception as e:
            error_log("更新搜尋欄位介面錯誤", e)
    
    # === 鎖定字符相關 ===
    
    def smart_lock_character_callback(self, sender):
        """智慧鎖定字符回呼（鎖定操作使用細粒度更新）"""
        try:
            debug_log(f"[智慧鎖定] === 開始處理鎖定回呼 ===")
            debug_log(f"[智慧鎖定] 位置: {sender.position}, 輸入: '{sender.stringValue()}'")
            
            if not Glyphs.font:
                debug_log("[智慧鎖定] 無字型檔案，中止處理")
                return
            
            # 檢查當前狀態
            lock_state = self._get_lock_state()
            
            debug_log(f"[智慧鎖定] 鎖定模式: {'🔓 解鎖' if lock_state else '🔒 上鎖'}")
            
            # === 解鎖模式下，鎖定框輸入僅更新 lockedChars，不影響預覽 ===
            if lock_state:
                debug_log("[智慧鎖定] 🔓 解鎖模式：鎖定框輸入不影響預覽，但仍更新 lockedChars")
                self._update_locked_chars_only(sender)
                return
            
            debug_log("[智慧鎖定] 🔒 上鎖模式，處理輸入並更新預覽...")
            
            # 上鎖模式：更新 lockedChars 並使用細粒度更新
            self._update_locked_chars_only(sender)
            
            # === 使用細粒度更新，只影響鎖定位置，保持其他位置不變 ===
            position = sender.position
            input_text = sender.stringValue()
            
            if input_text:
                # 有輸入：驗證並更新該位置
                recognized_char = self._recognize_character(input_text)
                if get_cached_glyph(Glyphs.font, recognized_char):
                    debug_log(f"[智慧鎖定] 🔒 上鎖模式 - 使用細粒度更新位置 {position} 為 '{recognized_char}'")
                    self.update_locked_position(position, recognized_char)
                else:
                    debug_log(f"[智慧鎖定] 字符 '{input_text}' -> '{recognized_char}' 無效，忽略")
            else:
                # 清空輸入：清除該位置的鎖定
                debug_log(f"[智慧鎖定] 🔒 上鎖模式 - 清除位置 {position} 的鎖定")
                self._clear_single_locked_position(position)
            
            # 儲存變更
            self.plugin.savePreferences()
            
            debug_log(f"[智慧鎖定] === 完成處理鎖定回呼（細粒度更新）===")
        
        except Exception as e:
            error_log("智慧鎖定字符處理錯誤", e)
    
    def clear_all_lock_fields_callback(self, sender):
        """清空所有鎖定輸入框"""
        try:
            if not Glyphs.font:
                return
            
            # 初始化必要的字典
            if not hasattr(self.plugin, 'lockedChars'):
                self.plugin.lockedChars = {}
            if not hasattr(self.plugin, 'previousLockedChars'):
                self.plugin.previousLockedChars = {}
            
            # 備份目前狀態
            self.plugin.previousLockedChars = self.plugin.lockedChars.copy()
            
            # 清空鎖定字符
            self.plugin.lockedChars = {}
            
            # 清空所有鎖定輸入框
            if (hasattr(self.plugin, 'windowController') and self.plugin.windowController and
                hasattr(self.plugin.windowController, 'controlsPanelView') and 
                self.plugin.windowController.controlsPanelView and 
                hasattr(self.plugin.windowController.controlsPanelView, 'lockFieldsPanel') and
                self.plugin.windowController.controlsPanelView.lockFieldsPanel and
                hasattr(self.plugin.windowController.controlsPanelView.lockFieldsPanel, 'lockFields')):
                
                for field in self.plugin.windowController.controlsPanelView.lockFieldsPanel.lockFields.values():
                    field.setStringValue_("")
            
            # 確保selectedChars是可變列表
            if hasattr(self.plugin, 'selectedChars'):
                self.plugin.selectedChars = list(self.plugin.selectedChars) if self.plugin.selectedChars else []
            
            # 確保currentArrangement是可變列表
            if hasattr(self.plugin, 'currentArrangement'):
                self.plugin.currentArrangement = list(self.plugin.currentArrangement) if self.plugin.currentArrangement else []
            
            # 更新排列和介面
            self.generate_new_arrangement()
            self.plugin.savePreferences()
            self.update_interface(None)
            
        except Exception as e:
            error_log("清空鎖定輸入框錯誤", e)
    
    # === 其他回呼 ===
    
    def pick_glyph_callback(self, sender):
        """選擇字符按鈕回呼（使用官方 PickGlyphs API）"""
        try:
            if not Glyphs.font:
                debug_log("警告：沒有開啟字型檔案")
                return
            
            # 使用官方 PickGlyphs API
            choice = PickGlyphs(
                content=list(Glyphs.font.glyphs),
                masterID=Glyphs.font.selectedFontMaster.id,
                searchString=self.plugin.lastInput if hasattr(self.plugin, 'lastInput') else "",
                defaultsKey="com.YinTzuYuan.NineBoxView.search"
            )
            
            if choice and choice[0]:
                selected_chars = []
                for selection in choice[0]:
                    if isinstance(selection, GSGlyph):
                        # 優先使用 Unicode 字符，如果沒有則使用字符名稱
                        if selection.unicode:
                            try:
                                char = chr(int(selection.unicode, 16))
                                selected_chars.append(char)
                            except:
                                selected_chars.append(selection.name)
                        else:
                            selected_chars.append(selection.name)
                
                if selected_chars:
                    # 取得搜尋框的目前內容
                    if (hasattr(self.plugin, 'windowController') and 
                        self.plugin.windowController and
                        hasattr(self.plugin.windowController, 'controlsPanelView') and 
                        self.plugin.windowController.controlsPanelView and
                        hasattr(self.plugin.windowController.controlsPanelView, 'searchPanel') and
                        self.plugin.windowController.controlsPanelView.searchPanel):
                        
                        search_panel = self.plugin.windowController.controlsPanelView.searchPanel
                        current_text = search_panel.get_search_value()
                        
                        # 將選取的字符用空格連接
                        chars_to_insert = ' '.join(selected_chars)
                        
                        # 智能插入：獲取游標位置並在正確位置插入
                        new_text = self._smart_insert_text(
                            search_panel.searchField, current_text, chars_to_insert)
                        
                        # 設定新的文字
                        search_panel.set_search_value(new_text)
                        
                        # 觸發 searchFieldCallback 以更新介面
                        # 建立一個模擬的 sender 物件
                        class MockSender:
                            def __init__(self, value):
                                self.value = value
                            def stringValue(self):
                                return self.value
                        
                        mock_sender = MockSender(new_text)
                        self.search_field_callback(mock_sender)
                    
        except Exception as e:
            error_log("選擇字符錯誤", e)
    
    def randomize_callback(self, sender):
        """隨機排列按鈕回呼"""
        # 確保 selectedChars 是可變列表
        if hasattr(self.plugin, 'selectedChars'):
            self.plugin.selectedChars = list(self.plugin.selectedChars) if self.plugin.selectedChars else []
            
        if not self.plugin.selectedChars:
            debug_log("隨機排列按鈕被點擊 - 但沒有可用字符")
            if Glyphs.font and Glyphs.font.selectedLayers:
                # 使用目前編輯字符
                current_char = self._get_current_editing_char()
                if current_char:
                    debug_log(f"使用目前編輯字符 '{current_char}' 填充")
                    self.plugin.selectedChars = [current_char]
                    # 強制繼續執行
                else:
                    self.update_interface(None)
                    return
            else:
                self.update_interface(None)
                return
        
        debug_log(f"隨機排列按鈕被點擊 - 使用所有 {len(self.plugin.selectedChars)} 個字符作為基數")
        
        # === 新增：清除原始排列，因為使用者主動要求新的隨機排列 ===
        if hasattr(self.plugin, 'originalArrangement'):
            self.plugin.originalArrangement = []
            debug_log("已清除原始排列，將生成全新的隨機排列")
        
        self.generate_new_arrangement()
        
        # 官方模式：更新預覽畫面
        if hasattr(self.plugin, 'windowController') and self.plugin.windowController:
            if hasattr(self.plugin.windowController, 'previewView') and self.plugin.windowController.previewView:
                debug_log("更新主預覽畫面的屬性設定器")
                self.plugin.windowController.previewView.currentArrangement = self.plugin.currentArrangement
            else:
                debug_log("呼叫標準更新函數")
                self.plugin.windowController.update()
        else:
            debug_log("無法找到視窗控制器，使用通用更新")
            self.update_interface(None)
        
        debug_log("隨機排列完成")
    
    def reset_zoom(self, sender):
        """重置縮放"""
        self.plugin.zoomFactor = DEFAULT_ZOOM
        self.plugin.savePreferences()
        self.update_interface(None)
    
    # === 字符排列生成 ===
    
    def generate_new_arrangement(self):
        """生成新的字符排列（9格版本，遵循 flow.md 邏輯）
        
        注意：此方法會完整重新生成排列，包括隨機化其餘格
        只應在以下情況使用：
        1. 搜尋欄位變更（批量輸入框變更）
        2. 用戶點擊隨機按鈕
        3. 初始化載入
        """
        try:
            debug_log("開始生成新的9格排列")
            
            # 檢查字型
            if not Glyphs.font:
                debug_log("警告：沒有開啟字型檔案")
                return
            
            # 1. 取得 activeGlyph（當前編輯字符）
            activeGlyph = self._get_current_editing_char()
            has_active = activeGlyph is not None  # None 表示無 activeGlyph
            
            # 2. 取得鎖定狀態
            is_in_clear_mode = self._get_lock_state()
            is_locked = not is_in_clear_mode
            
            # 3. 取得批量輸入字符（batchChars）
            batchChars = list(self.plugin.selectedChars) if hasattr(self.plugin, 'selectedChars') and self.plugin.selectedChars else []
            # 驗證 batchChars
            if Glyphs.font and batchChars:
                valid_batch_chars = [
                    char for char in batchChars 
                    if get_cached_glyph(Glyphs.font, char)
                ]
                batchChars = valid_batch_chars
            has_batch = bool(batchChars)
            
            # 4. 取得鎖定字符（lockedChars）
            lockedChars = getattr(self.plugin, 'lockedChars', {})
            if lockedChars:
                lockedChars = validate_locked_positions(lockedChars, Glyphs.font)
            has_locked = bool(lockedChars)
            
            debug_log(f"Flow.md 決策參數:")
            debug_log(f"  - activeGlyph: {activeGlyph} (has_active: {has_active})")
            debug_log(f"  - 鎖定模式: {'🔒 上鎖' if is_locked else '🔓 解鎖'}")
            debug_log(f"  - batchChars: {batchChars} (has_batch: {has_batch})")
            debug_log(f"  - lockedChars: {lockedChars} (has_locked: {has_locked})")
            
            # 5. 根據 flow.md 決策樹生成9格排列
            if has_active:
                arrangement = self._handle_with_active_glyph(activeGlyph, is_locked, has_locked, lockedChars, has_batch, batchChars)
            else:
                arrangement = self._handle_without_active_glyph(is_locked, has_locked, lockedChars, has_batch, batchChars)
            
            # 6. 更新 currentArrangement（9格）
            self.plugin.currentArrangement = list(arrangement)
            debug_log(f"生成的9格排列: {self.plugin.currentArrangement}")
            
            # 儲存變更
            self.plugin.savePreferences()
            
            # 官方模式：更新 preview view 的屬性設定器
            if (hasattr(self.plugin, 'windowController') and 
                self.plugin.windowController and
                hasattr(self.plugin.windowController, 'previewView')):
                debug_log("更新 currentArrangement 屬性")
                self.plugin.windowController.previewView.currentArrangement = self.plugin.currentArrangement
            
        except Exception as e:
            error_log("生成9格排列時發生錯誤", e)
    
    def _handle_with_active_glyph(self, activeGlyph, is_locked, has_locked, lockedChars, has_batch, batchChars):
        """處理有 activeGlyph 的情況"""
        arrangement = [None] * FULL_ARRANGEMENT_SIZE
        
        if is_locked:  # 上鎖模式
            if has_locked:  # 有鎖定字符
                if has_batch:  # 有批量輸入
                    # R1: 中心: activeGlyph, 其餘格: 鎖定格+batchChars
                    arrangement[CENTER_POSITION] = activeGlyph
                    self._apply_locked_chars(arrangement, lockedChars)
                    self._fill_remaining_with_batch(arrangement, batchChars)
                    debug_log("R1: activeGlyph + 上鎖 + 有locked + 有batch")
                else:  # 無批量輸入
                    # R2: 中心: activeGlyph, 其餘格: 鎖定格+activeGlyph
                    arrangement[CENTER_POSITION] = activeGlyph
                    self._apply_locked_chars(arrangement, lockedChars)
                    self._fill_remaining_with_char(arrangement, activeGlyph)
                    debug_log("R2: activeGlyph + 上鎖 + 有locked + 無batch")
            else:  # 無鎖定字符
                if has_batch:  # 有批量輸入
                    # R3: 中心: activeGlyph, 周圍格: 從 batchChars 隨機
                    arrangement[CENTER_POSITION] = activeGlyph
                    self._fill_surrounding_with_batch(arrangement, batchChars)
                    debug_log("R3: activeGlyph + 上鎖 + 無locked + 有batch")
                else:  # 無批量輸入
                    # R4: 中心: activeGlyph, 周圍格: activeGlyph
                    arrangement = [activeGlyph] * FULL_ARRANGEMENT_SIZE
                    debug_log("R4: activeGlyph + 上鎖 + 無locked + 無batch")
        else:  # 解鎖模式
            if has_batch:  # 有批量輸入
                # R5: 中心: activeGlyph, 周圍格: 從 batchChars 隨機
                arrangement[CENTER_POSITION] = activeGlyph
                self._fill_surrounding_with_batch(arrangement, batchChars)
                debug_log("R5: activeGlyph + 解鎖 + 有batch")
            else:  # 無批量輸入
                # R6: 中心: activeGlyph, 周圍格: activeGlyph
                arrangement = [activeGlyph] * FULL_ARRANGEMENT_SIZE
                debug_log("R6: activeGlyph + 解鎖 + 無batch")
        
        return arrangement
    
    def _handle_without_active_glyph(self, is_locked, has_locked, lockedChars, has_batch, batchChars):
        """處理沒有 activeGlyph 的情況（修正版：符合 flow.md 邏輯）"""
        arrangement = [None] * FULL_ARRANGEMENT_SIZE
        
        if is_locked:  # 上鎖模式
            if has_locked:  # 有鎖定字符
                if has_batch:  # 有批量輸入
                    # R7: 中心: 從 batchChars 隨機, 其餘格: 鎖定格+batchChars
                    arrangement[CENTER_POSITION] = random.choice(batchChars)
                    self._apply_locked_chars(arrangement, lockedChars)
                    self._fill_remaining_with_batch(arrangement, batchChars)
                    debug_log("R7: 無activeGlyph + 上鎖 + 有locked + 有batch")
                else:  # 無批量輸入
                    # R8: 中心: 空白, 其餘格: 鎖定格+空白
                    arrangement[CENTER_POSITION] = None
                    self._apply_locked_chars(arrangement, lockedChars)
                    debug_log("R8: 無activeGlyph + 上鎖 + 有locked + 無batch")
            else:  # 無鎖定字符
                if has_batch:  # 有批量輸入
                    # R9: 中心: 從 batchChars 隨機, 周圍格: 從 batchChars 隨機
                    arrangement[CENTER_POSITION] = random.choice(batchChars)
                    self._fill_surrounding_with_batch(arrangement, batchChars)
                    debug_log("R9: 無activeGlyph + 上鎖 + 無locked + 有batch")
                else:  # 無批量輸入
                    # R10: 所有九格皆為空白
                    debug_log("R10: 無activeGlyph + 上鎖 + 無locked + 無batch")
        else:  # 解鎖模式
            if has_batch:  # 有批量輸入
                # R11: 中心: 從 batchChars 隨機, 周圍格: 從 batchChars 隨機
                arrangement[CENTER_POSITION] = random.choice(batchChars)
                self._fill_surrounding_with_batch(arrangement, batchChars)
                debug_log("R11: 無activeGlyph + 解鎖 + 有batch")
            else:  # 無批量輸入
                # R12: 所有九格皆為空白
                debug_log("R12: 無activeGlyph + 解鎖 + 無batch")
        
        return arrangement
    
    # === 細粒度更新方法（符合 flow.md 邏輯）===
    
    def update_lock_mode_display(self):
        """更新鎖定模式顯示邏輯（不觸發隨機排列）
        
        根據 flow.md 步驟2：只影響鎖定格的顯示/隱藏，不影響其餘格的隨機排列
        """
        try:
            # 設置細粒度更新標記
            self._performing_granular_update = True
            debug_log("[細粒度更新] 更新鎖定模式顯示邏輯")
            
            if not hasattr(self.plugin, 'currentArrangement') or not self.plugin.currentArrangement:
                debug_log("[細粒度更新] 無現有排列，需要完整初始化")
                self.generate_new_arrangement()
                return
            
            # 確保 currentArrangement 是可變列表且長度正確
            current_arr = list(self.plugin.currentArrangement)
            while len(current_arr) < FULL_ARRANGEMENT_SIZE:
                current_arr.append(None)
            
            # 取得當前狀態
            is_in_clear_mode = self._get_lock_state()
            lockedChars = getattr(self.plugin, 'lockedChars', {})
            
            debug_log(f"[細粒度更新] 鎖定模式: {'🔓 解鎖' if is_in_clear_mode else '🔒 上鎖'}")
            debug_log(f"[細粒度更新] 鎖定字符: {lockedChars}")
            
            if is_in_clear_mode:
                # 解鎖模式：鎖定格恢復為其他邏輯決定的內容
                debug_log("[細粒度更新] 解鎖模式：清除鎖定格內容")
                self._restore_non_locked_content(current_arr, lockedChars.keys())
            else:
                # 上鎖模式：應用鎖定字符到對應位置
                debug_log("[細粒度更新] 上鎖模式：應用鎖定字符")
                self._apply_locked_chars(current_arr, lockedChars)
            
            # 更新排列
            self.plugin.currentArrangement = current_arr
            self.plugin.savePreferences()
            
            # 更新預覽
            self._update_preview_only()
            
            debug_log(f"[細粒度更新] 完成，最終排列: {self.plugin.currentArrangement}")
            
        except Exception as e:
            error_log("[細粒度更新] 更新鎖定模式顯示時發生錯誤", e)
        finally:
            # 清除細粒度更新標記
            self._performing_granular_update = False
    
    def clear_locked_positions(self):
        """清除鎖定位置（不觸發隨機排列）
        
        根據 flow.md 步驟3：只影響鎖定格內容，不影響其餘格的隨機排列
        """
        try:
            # 設置細粒度更新標記
            self._performing_granular_update = True
            debug_log("[細粒度更新] 清除鎖定位置")
            
            # 記錄要清除的位置
            positions_to_clear = list(getattr(self.plugin, 'lockedChars', {}).keys())
            debug_log(f"[細粒度更新] 要清除的位置: {positions_to_clear}")
            
            # 清除 lockedChars
            if hasattr(self.plugin, 'lockedChars'):
                self.plugin.lockedChars.clear()
            
            # 如果有現有排列，才進行細粒度清除
            if hasattr(self.plugin, 'currentArrangement') and self.plugin.currentArrangement:
                debug_log("[細粒度更新] 有現有排列，進行細粒度清除")
                # 確保 currentArrangement 是可變列表
                current_arr = list(self.plugin.currentArrangement)
                
                # 只有當有位置需要清除時才恢復內容
                if positions_to_clear:
                    self._restore_non_locked_content(current_arr, positions_to_clear)
                    self.plugin.currentArrangement = current_arr
                    debug_log(f"[細粒度更新] 已恢復 {len(positions_to_clear)} 個位置的內容")
                else:
                    debug_log("[細粒度更新] 沒有位置需要清除")
            else:
                debug_log("[細粒度更新] 無現有排列，僅清除鎖定狀態")
            
            # 重要：不管有沒有排列，都要觸發重繪和儲存
            self.plugin.savePreferences()
            self._update_preview_only()  # 確保主視窗重繪
            
            debug_log(f"[細粒度更新] 清除完成，最終排列: {getattr(self.plugin, 'currentArrangement', 'None')}")
            
        except Exception as e:
            error_log("[細粒度更新] 清除鎖定位置時發生錯誤", e)
        finally:
            # 清除細粒度更新標記
            self._performing_granular_update = False
    
    def update_center_position(self, new_active_glyph):
        """只更新中心格（不觸發隨機排列）
        
        根據 flow.md 步驟1：只影響中心格，不影響其餘格
        """
        try:
            debug_log(f"[細粒度更新] 更新中心格為: {new_active_glyph}")
            
            if not hasattr(self.plugin, 'currentArrangement') or not self.plugin.currentArrangement:
                debug_log("[細粒度更新] 無現有排列，生成新排列")
                self.generate_new_arrangement()
                return
            
            # 確保 currentArrangement 是可變列表且長度正確
            current_arr = list(self.plugin.currentArrangement)
            while len(current_arr) < FULL_ARRANGEMENT_SIZE:
                current_arr.append(None)
            
            # 檢查中心格是否被鎖定
            if CENTER_POSITION in getattr(self.plugin, 'lockedChars', {}):
                debug_log("[細粒度更新] 中心格被鎖定，保持不變")
                return
            
            # 更新中心位置
            if new_active_glyph is not None:
                current_arr[CENTER_POSITION] = new_active_glyph
                debug_log(f"[細粒度更新] 中心格更新為: {new_active_glyph}")
            
            # 更新排列
            self.plugin.currentArrangement = current_arr
            self.plugin.savePreferences()
            
            # 更新預覽
            self._update_preview_only()
            
            debug_log(f"[細粒度更新] 中心格更新完成")
            
        except Exception as e:
            error_log("[細粒度更新] 更新中心格時發生錯誤", e)
    
    def update_locked_position(self, position, char):
        """更新單個鎖定位置（不觸發隨機排列）
        
        Args:
            position: 要更新的位置 (0-8)
            char: 要設定的字符
        """
        try:
            debug_log(f"[細粒度更新] 更新鎖定位置 {position} 為: {char}")
            
            if not hasattr(self.plugin, 'currentArrangement') or not self.plugin.currentArrangement:
                debug_log("[細粒度更新] 無現有排列，生成新排列")
                self.generate_new_arrangement()
                return
            
            # 確保 currentArrangement 是可變列表且長度正確
            current_arr = list(self.plugin.currentArrangement)
            while len(current_arr) < FULL_ARRANGEMENT_SIZE:
                current_arr.append(None)
            
            # 檢查是否在上鎖模式
            is_in_clear_mode = self._get_lock_state()
            if is_in_clear_mode:
                debug_log("[細粒度更新] 解鎖模式下，鎖定位置不影響預覽")
                return
            
            # 更新指定位置
            if 0 <= position < FULL_ARRANGEMENT_SIZE:
                current_arr[position] = char
                debug_log(f"[細粒度更新] 位置 {position} 更新為: {char}")
            
            # 更新排列
            self.plugin.currentArrangement = current_arr
            self.plugin.savePreferences()
            
            # 更新預覽
            self._update_preview_only()
            
            debug_log(f"[細粒度更新] 鎖定位置更新完成")
            
        except Exception as e:
            error_log("[細粒度更新] 更新鎖定位置時發生錯誤", e)
    
    def _restore_non_locked_content(self, arrangement, positions):
        """恢復非鎖定位置的內容（遵循 flow.md 邏輯，並處理批次輸入變更）"""
        try:
            # 優先使用原始排列
            if hasattr(self.plugin, 'originalArrangement') and self.plugin.originalArrangement:
                batch_chars = list(getattr(self.plugin, 'selectedChars', []))
                for pos in positions:
                    if pos < len(self.plugin.originalArrangement) and pos < len(arrangement):
                        orig_char = self.plugin.originalArrangement[pos]
                        # 若批次輸入存在且 orig_char 不在其中，則隨機選一個新字元
                        if batch_chars and orig_char not in batch_chars:
                            replacement = random.choice(batch_chars)
                            arrangement[pos] = replacement
                            debug_log(f"[恢復內容] 位置 {pos} 原字元 '{orig_char}' 已不存在於批次輸入，改用新字元: {replacement}")
                        else:
                            arrangement[pos] = orig_char
                            debug_log(f"[恢復內容] 位置 {pos} 恢復為原始字符: {arrangement[pos]}")
                return
            
            # 根據 flow.md 邏輯決定恢復內容
            activeGlyph = self._get_current_editing_char()
            has_active = activeGlyph is not None
            has_batch = bool(getattr(self.plugin, 'selectedChars', []))
            
            debug_log(f"[恢復內容] 決策參數: has_active={has_active}, has_batch={has_batch}")
            
            if has_active:
                # 有 activeGlyph：根據是否有批量字符決定
                if has_batch:
                    # 有批量字符：使用批量字符
                    for pos in positions:
                        if pos < len(arrangement):
                            replacement_char = random.choice(self.plugin.selectedChars)
                            arrangement[pos] = replacement_char
                            debug_log(f"[恢復內容] 位置 {pos} 使用批量字符: {replacement_char}")
                else:
                    # 無批量字符：全部使用 activeGlyph
                    for pos in positions:
                        if pos < len(arrangement):
                            arrangement[pos] = activeGlyph
                            debug_log(f"[恢復內容] 位置 {pos} 使用 activeGlyph: {activeGlyph}")
            else:
                # 無 activeGlyph：根據是否有批量字符決定
                if has_batch:
                    # 有批量字符：使用批量字符
                    for pos in positions:
                        if pos < len(arrangement):
                            replacement_char = random.choice(self.plugin.selectedChars)
                            arrangement[pos] = replacement_char
                            debug_log(f"[恢復內容] 位置 {pos} 使用批量字符: {replacement_char}")
                else:
                    # 無批量字符：設為空白（None）
                    for pos in positions:
                        if pos < len(arrangement):
                            arrangement[pos] = None
                            debug_log(f"[恢復內容] 位置 {pos} 設為空白（符合 flow.md）")
                
        except Exception as e:
            error_log("[恢復內容] 恢復非鎖定內容時發生錯誤", e)
    
    def _update_preview_only(self):
        """只更新預覽，不觸發其他邏輯（強制重繪版）"""
        try:
            if (hasattr(self.plugin, 'windowController') and 
                self.plugin.windowController and
                hasattr(self.plugin.windowController, 'previewView')):
                # 同步排列到預覽視圖
                self.plugin.windowController.previewView.currentArrangement = self.plugin.currentArrangement
                debug_log("[預覽更新] 已同步 currentArrangement 到預覽視圖")
                
                # === 強制觸發重繪，確保主視窗立即更新 ===
                self.plugin.windowController.update()
                debug_log("[預覽更新] 已強制觸發主視窗重繪")
        except Exception as e:
            error_log("[預覽更新] 更新預覽時發生錯誤", e)
    
    # === 9格填充輔助方法 ===
    
    def _apply_locked_chars(self, arrangement, lockedChars):
        """將鎖定字符應用到排列中"""
        for position, char in lockedChars.items():
            if 0 <= position < FULL_ARRANGEMENT_SIZE:
                arrangement[position] = char
    
    def _fill_remaining_with_batch(self, arrangement, batchChars):
        """用批量字符填充剩餘的None位置，依據細緻規則"""
        # 找出所有 None 的位置
        positions = [i for i in range(FULL_ARRANGEMENT_SIZE) if arrangement[i] is None]
        chars_to_use = generate_non_repeating_batch(batchChars, len(positions))
        for idx, pos in enumerate(positions):
            arrangement[pos] = chars_to_use[idx] if idx < len(chars_to_use) else None
    
    def _fill_remaining_with_char(self, arrangement, char):
        """用指定字符填充剩餘的None位置"""
        for i in range(FULL_ARRANGEMENT_SIZE):
            if arrangement[i] is None:
                arrangement[i] = char
    
    def _fill_surrounding_with_batch(self, arrangement, batchChars):
        """用批量字符填充周圍8格（不包括中心格），依據細緻規則"""
        chars_to_use = generate_non_repeating_batch(batchChars, len(SURROUNDING_POSITIONS))
        for idx, pos in enumerate(SURROUNDING_POSITIONS):
            arrangement[pos] = chars_to_use[idx] if idx < len(chars_to_use) else None
    
    def _fill_all_with_batch(self, arrangement, batchChars):
        """用批量字符填充所有9格，依據細緻規則"""
        chars_to_use = generate_non_repeating_batch(batchChars, FULL_ARRANGEMENT_SIZE)
        for idx in range(FULL_ARRANGEMENT_SIZE):
            arrangement[idx] = chars_to_use[idx] if idx < len(chars_to_use) else None
    
    # === 輔助方法 ===
    
    def _update_center_position_only(self, new_active_glyph):
        """只更新中心格，保持周圍格排列穩定
        
        Args:
            new_active_glyph: 新的中央編輯字符
        """
        try:
            # 檢查是否有搜尋欄內容（批量字符）
            has_batch = bool(getattr(self.plugin, 'selectedChars', []))
            
            # 如果搜尋欄包含有效字符，只更新中心格
            if has_batch:
                debug_log("[中心更新] 搜尋欄包含有效字符，只更新中心格，保持周圍格穩定")
                
                # 確保有 currentArrangement
                if not hasattr(self.plugin, 'currentArrangement') or not self.plugin.currentArrangement:
                    debug_log("[中心更新] 沒有現有排列，生成新排列")
                    self.generate_new_arrangement()
                    return
                
                # 確保 currentArrangement 是可變列表且長度正確
                current_arr = list(self.plugin.currentArrangement)
                
                # 確保排列長度是9格
                while len(current_arr) < FULL_ARRANGEMENT_SIZE:
                    current_arr.append(None)
                
                # 只更新中心位置（位置4）
                if new_active_glyph is not None:
                    current_arr[CENTER_POSITION] = new_active_glyph
                    debug_log(f"[中心更新] 中心格更新為: {new_active_glyph}")
                else:
                    # 沒有 activeGlyph，從批量字符中選擇
                    current_arr[CENTER_POSITION] = random.choice(self.plugin.selectedChars)
                    debug_log(f"[中心更新] 中心格更新為隨機批量字符: {current_arr[CENTER_POSITION]}")
                
                # 更新 currentArrangement
                self.plugin.currentArrangement = current_arr
                
                # 儲存變更
                self.plugin.savePreferences()
                
                debug_log(f"[中心更新] 完成（穩定模式），當前排列: {self.plugin.currentArrangement}")
                
            else:
                # 沒有搜尋欄內容，使用原始的完全重新生成邏輯
                debug_log("[中心更新] 搜尋欄為空，重新生成完整排列")
                self.generate_new_arrangement()
            
        except Exception as e:
            error_log("[中心更新] 更新中心位置時發生錯誤", e)
            # 如果發生錯誤，回退到完全重新生成
            debug_log("[中心更新] 錯誤回退：重新生成完整排列")
            self.generate_new_arrangement()
    
    def _update_single_position(self, position, input_text):
        """
        更新單個位置的字符（增強 debug 版本：追蹤邏輯衝突）
        
        Args:
            position: 要更新的位置 (0-8，但排除中心位置4)
            input_text: 輸入的文字
        """
        try:
            debug_log(f"[單一更新] === 開始處理位置 {position}，輸入文字: '{input_text}' ===")
            
            # 檢查當前狀態
            current_active = self._get_current_editing_char()
            has_batch = bool(getattr(self.plugin, 'selectedChars', []))
            lock_state = self._get_lock_state()
            
            debug_log(f"[單一更新] 當前狀態檢查:")
            debug_log(f"  - activeGlyph: {current_active}")
            debug_log(f"  - has_batch: {has_batch}")
            debug_log(f"  - lock_state (解鎖模式): {lock_state}")
            debug_log(f"  - selectedChars: {getattr(self.plugin, 'selectedChars', [])}")
            
            # 確保有 currentArrangement
            if not hasattr(self.plugin, 'currentArrangement') or not self.plugin.currentArrangement:
                debug_log("[單一更新] 無 currentArrangement，生成新排列")
                self.generate_new_arrangement()
                return
            
            # 建立可變複本
            current_arr = list(self.plugin.currentArrangement)
            while len(current_arr) < FULL_ARRANGEMENT_SIZE:
                current_arr.append(None)
            
            debug_log(f"[單一更新] 當前排列: {current_arr}")
            debug_log(f"[單一更新] 位置 {position} 的當前值: {current_arr[position]}")
            
            # 檢查是否在上鎖模式
            if lock_state:  # 解鎖模式
                debug_log(f"[單一更新] 🔓 解鎖模式下，不更新預覽顯示")
                return
            
            debug_log(f"[單一更新] 🔒 上鎖模式，繼續處理...")
            
            if input_text:
                # 有輸入：驗證並更新
                debug_log(f"[單一更新] 處理有效輸入: '{input_text}'")
                recognized_char = self._recognize_character(input_text)
                debug_log(f"[單一更新] 辨識結果: '{recognized_char}'")
                
                if get_cached_glyph(Glyphs.font, recognized_char):
                    current_arr[position] = recognized_char
                    self.plugin.currentArrangement = current_arr
                    debug_log(f"[單一更新] ✅ 位置 {position} 更新為有效字符: {recognized_char}")
                else:
                    debug_log(f"[單一更新] ❌ 位置 {position} 的字符 '{input_text}' -> '{recognized_char}' 無效，保持原狀")
                    return
            else:
                # 清空輸入：根據 flow.md 邏輯決定填入內容
                debug_log(f"[單一更新] 處理清空輸入")
                
                # 重新檢查 activeGlyph（可能狀態已變）
                activeGlyph = self._get_current_editing_char()
                debug_log(f"[單一更新] 重新檢查 activeGlyph: {activeGlyph}")
                
                if activeGlyph is not None:
                    # 有 activeGlyph：根據 flow.md，應該填入 activeGlyph 而不是 None
                    old_value = current_arr[position]
                    current_arr[position] = activeGlyph
                    debug_log(f"[單一更新] ✅ 有 activeGlyph - 位置 {position}: '{old_value}' -> '{activeGlyph}'")
                else:
                    # 無 activeGlyph：設為空白（None）
                    old_value = current_arr[position]
                    current_arr[position] = None
                    debug_log(f"[單一更新] ❌ 無 activeGlyph - 位置 {position}: '{old_value}' -> None")
                
                self.plugin.currentArrangement = current_arr
                
                # 同時清除 lockedChars 中的記錄
                if hasattr(self.plugin, 'lockedChars') and position in self.plugin.lockedChars:
                    del self.plugin.lockedChars[position]
                    debug_log(f"[單一更新] 已清除位置 {position} 的鎖定記錄")
            
            debug_log(f"[單一更新] 最終排列: {self.plugin.currentArrangement}")
            
            # 儲存更新
            self.plugin.savePreferences()
            debug_log(f"[單一更新] === 完成處理位置 {position} ===")
            
        except Exception as e:
            error_log("[單一更新] 更新單個位置時發生錯誤", e)
    
    def _get_current_editing_char(self):
        """取得目前正在編輯的字符（官方 API 最佳化版本）"""
        try:
            # 使用官方 API 獲取當前字型和選中的圖層
            font = Glyphs.font
            if not font:
                debug_log("無開啟的字型檔案")
                return None
                
            selected_layers = font.selectedLayers
            if not selected_layers:
                debug_log("無選中的圖層")
                return None
                
            # 獲取第一個選中的圖層
            current_layer = selected_layers[0]
            if not current_layer or not current_layer.parent:
                debug_log("無效的圖層或字符")
                return None
                
            current_glyph = current_layer.parent
            
            # 使用官方 API 屬性獲取字符資訊
            # 優先返回 Unicode 字符（官方推薦方式）
            if hasattr(current_glyph, 'unicode') and current_glyph.unicode:
                try:
                    char = chr(int(current_glyph.unicode, 16))
                    debug_log(f"取得 activeGlyph (Unicode): '{char}' ({current_glyph.unicode})")
                    return char
                except (ValueError, OverflowError) as e:
                    debug_log(f"Unicode 轉換失敗: {current_glyph.unicode}, 錯誤: {e}")
                    
            # 其次返回字符名稱（官方備選方式）
            if hasattr(current_glyph, 'name') and current_glyph.name:
                debug_log(f"取得 activeGlyph (Name): '{current_glyph.name}'")
                return current_glyph.name
                
        except Exception as e:
            debug_log(f"取得 activeGlyph 時發生錯誤: {e}")
        
        # 沒有有效的編輯字符時返回 None（符合 flow.md 規範）
        debug_log("無 activeGlyph")
        return None
    
    def _get_lock_state(self):
        """取得鎖頭狀態"""
        # 優先從控制面板讀取
        if (hasattr(self.plugin, 'windowController') and self.plugin.windowController and 
            hasattr(self.plugin.windowController, 'controlsPanelView') and 
            self.plugin.windowController.controlsPanelView and 
            hasattr(self.plugin.windowController.controlsPanelView, 'lockFieldsPanel') and
            self.plugin.windowController.controlsPanelView.lockFieldsPanel):
            return self.plugin.windowController.controlsPanelView.lockFieldsPanel.get_lock_state()
        
        # 從plugin對象讀取（控制面板未初始化時）
        return getattr(self.plugin, 'isInClearMode', False)  # 預設為上鎖
    
    def _recognize_character(self, input_text, allow_fallback=True):
        """辨識字符，優先考慮完整輸入、區分大小寫
        
        Args:
            input_text: 輸入的文字
            allow_fallback: 是否允許使用fallback邏輯（預設True以保持向後相容）
        """
        # 1. 嘗試完整輸入（區分大小寫）
        glyph = get_cached_glyph(Glyphs.font, input_text)
        if glyph:
            return input_text
        
        # 2. 嘗試第一個字符（區分大小寫）
        if len(input_text) > 0:
            first_char = input_text[0]
            first_glyph = get_cached_glyph(Glyphs.font, first_char)
            if first_glyph:
                return first_char
        
        # 3. 解析輸入
        parsed_chars = parse_input_text(input_text)
        if parsed_chars:
            return parsed_chars[0]
                
        # 4. 使用搜尋欄位的有效字符
        if hasattr(self.plugin, 'selectedChars') and self.plugin.selectedChars:
            for char in self.plugin.selectedChars:
                if get_cached_glyph(Glyphs.font, char):
                    return char
        
        # 5. 使用目前正在編輯的字符
        if Glyphs.font and Glyphs.font.selectedLayers:
            current_layer = Glyphs.font.selectedLayers[0]
            if current_layer and current_layer.parent:
                current_glyph = current_layer.parent
                if current_glyph.unicode:
                    try:
                        char = chr(int(current_glyph.unicode, 16))
                        return char
                    except:
                        pass
                if current_glyph.name:
                    return current_glyph.name
                
        # 6. 絕對保底：回傳空白
        return None
    
    def _update_locked_chars_only(self, sender):
        """僅更新 lockedChars，不影響預覽（統一版本）"""
        try:
            if not hasattr(self.plugin, 'lockedChars'):
                self.plugin.lockedChars = {}
            
            position = sender.position
            input_text = sender.stringValue()
            
            debug_log(f"[鎖定字符更新] 位置 {position}，輸入: '{input_text}'")
            
            if not input_text:
                # 清除鎖定
                if position in self.plugin.lockedChars:
                    old_char = self.plugin.lockedChars[position]
                    del self.plugin.lockedChars[position]
                    debug_log(f"[鎖定字符更新] 清除位置 {position}: '{old_char}'")
                else:
                    debug_log(f"[鎖定字符更新] 位置 {position} 本來就沒有鎖定")
            else:
                # 驗證並設定鎖定字符
                recognized_char = self._recognize_character(input_text)
                debug_log(f"[鎖定字符更新] 字符辨識: '{input_text}' -> '{recognized_char}'")
                
                # 驗證字符是否存在於當前字型中
                if not get_cached_glyph(Glyphs.font, recognized_char):
                    debug_log(f"[鎖定字符更新] ❌ 字符 '{input_text}' -> '{recognized_char}' 不存在於字型中，忽略")
                    return
                
                # 字符有效，檢查是否有變更
                old_char = self.plugin.lockedChars.get(position, None)
                if old_char != recognized_char:
                    self.plugin.lockedChars[position] = recognized_char
                    debug_log(f"[鎖定字符更新] ✅ 位置 {position} 設定: '{old_char}' -> '{recognized_char}'")
                else:
                    debug_log(f"[鎖定字符更新] 位置 {position} 字符無變更: '{recognized_char}'")
            
            debug_log(f"[鎖定字符更新] 最終 lockedChars: {self.plugin.lockedChars}")
            
        except Exception as e:
            error_log("[鎖定字符更新] 更新鎖定字符時發生錯誤", e)
    
    def _clear_single_locked_position(self, position):
        """清除單個鎖定位置（細粒度更新）"""
        try:
            debug_log(f"[清除單一鎖定] 清除位置 {position}")
            
            if not hasattr(self.plugin, 'currentArrangement') or not self.plugin.currentArrangement:
                debug_log("[清除單一鎖定] 無現有排列，跳過清除")
                return
            
            # 確保 currentArrangement 是可變列表且長度正確
            current_arr = list(self.plugin.currentArrangement)
            while len(current_arr) < FULL_ARRANGEMENT_SIZE:
                current_arr.append(None)
            
            # 恢復該位置的內容
            self._restore_non_locked_content(current_arr, [position])
            
            # 更新排列
            self.plugin.currentArrangement = current_arr
            self.plugin.savePreferences()
            
            # 更新預覽
            self._update_preview_only()
            
            debug_log(f"[清除單一鎖定] 完成清除位置 {position}")
            
        except Exception as e:
            error_log("[清除單一鎖定] 清除單個鎖定位置時發生錯誤", e)
    
    def _smart_insert_text(self, text_view, current_text, chars_to_insert):
        """智能文字插入：支援游標位置和選中文字替換
        
        Args:
            text_view: NSTextView 對象（搜索框）
            current_text: 當前文字內容
            chars_to_insert: 要插入的字符串
            
        Returns:
            str: 插入後的新文字
        """
        try:
            debug_log(f"[智能插入] 當前文字: '{current_text}', 要插入: '{chars_to_insert}'")
            
            # 獲取當前選擇範圍（游標位置或選中範圍）
            if hasattr(text_view, 'selectedRange'):
                selection_range = text_view.selectedRange()
                cursor_position = selection_range.location
                selection_length = selection_range.length
                
                debug_log(f"[智能插入] 游標位置: {cursor_position}, 選中長度: {selection_length}")
                
                # 確保位置有效
                if cursor_position < 0:
                    cursor_position = 0
                elif cursor_position > len(current_text):
                    cursor_position = len(current_text)
                
                if selection_length > 0:
                    # 有選中文字：替換選中內容
                    debug_log("[智能插入] 替換選中文字")
                    left_part = current_text[:cursor_position]
                    right_part = current_text[cursor_position + selection_length:]
                    
                    # 智能空格處理：替換模式
                    need_left_space = (left_part and not left_part.endswith(' ') and 
                                     left_part.strip())  # 左邊有非空白內容且不以空格結尾
                    need_right_space = (right_part and not right_part.startswith(' ') and 
                                      right_part.strip())  # 右邊有非空白內容且不以空格開頭
                    
                    space_left = ' ' if need_left_space else ''
                    space_right = ' ' if need_right_space else ''
                    
                    new_text = left_part + space_left + chars_to_insert + space_right + right_part
                    debug_log(f"[智能插入] 替換結果: '{new_text}'")
                    
                else:
                    # 只是游標位置：在當前位置插入
                    debug_log("[智能插入] 在游標位置插入")
                    left_part = current_text[:cursor_position]
                    right_part = current_text[cursor_position:]
                    
                    # 智能空格處理：插入模式
                    need_left_space = (left_part and not left_part.endswith(' ') and 
                                     cursor_position > 0)  # 不在開頭且左邊不是空格
                    need_right_space = (right_part and not right_part.startswith(' ') and 
                                      cursor_position < len(current_text))  # 不在結尾且右邊不是空格
                    
                    space_left = ' ' if need_left_space else ''
                    space_right = ' ' if need_right_space else ''
                    
                    new_text = left_part + space_left + chars_to_insert + space_right + right_part
                    debug_log(f"[智能插入] 插入結果: '{new_text}'")
                
                return new_text
                
            else:
                # 回退到原始邏輯（不支援 selectedRange 的情況）
                debug_log("[智能插入] 回退到末尾插入")
                return self._fallback_append_text(current_text, chars_to_insert)
                
        except Exception as e:
            error_log("[智能插入] 智能插入發生錯誤", e)
            # 發生錯誤時回退到原始邏輯
            return self._fallback_append_text(current_text, chars_to_insert)
    
    def _fallback_append_text(self, current_text, chars_to_insert):
        """回退邏輯：簡單的末尾插入"""
        debug_log(f"[回退插入] 在末尾插入: '{chars_to_insert}'")
        if current_text and not current_text.endswith(' '):
            return current_text + ' ' + chars_to_insert
        else:
            return current_text + chars_to_insert
