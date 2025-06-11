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
from constants import DEBUG_MODE, DEFAULT_ZOOM, FULL_ARRANGEMENT_SIZE, CENTER_POSITION
from utils import debug_log, error_log, parse_input_text, generate_arrangement, validate_locked_positions, get_cached_glyph


class EventHandlers:
    """集中管理所有事件處理邏輯"""
    
    def __init__(self, plugin):
        self.plugin = plugin
        
    
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
        """選擇變更處理"""
        try:
            # 清除快取
            if hasattr(self.plugin, 'clear_cache'):
                self.plugin.clear_cache()
            
            # 重新生成排列以反映當前編輯字符的變更
            debug_log("字符選擇變更，重新生成排列")
            self.generate_new_arrangement()
            
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
        """處理搜尋欄位輸入（最佳化版）"""
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
        """智慧鎖定字符回呼（資料處理與即時更新）"""
        try:
            if not Glyphs.font:
                return
            
            # 取得鎖定狀態
            is_in_clear_mode = self._get_lock_state()
            
            if not hasattr(self.plugin, 'lockedChars'):
                self.plugin.lockedChars = {}
            
            position = sender.position
            input_text = sender.stringValue()
            arrangement_changed = False
            
            if not input_text:
                # 清除鎖定
                if position in self.plugin.lockedChars:
                    del self.plugin.lockedChars[position]
                    arrangement_changed = True
                    debug_log(f"[智慧鎖定] 清除位置 {position} 的鎖定")
            else:
                # 智慧辨識
                recognized_char = self._recognize_character(input_text)
                
                # 檢查是否有變更
                if position not in self.plugin.lockedChars or self.plugin.lockedChars[position] != recognized_char:
                    self.plugin.lockedChars[position] = recognized_char
                    arrangement_changed = True
                    debug_log(f"[智慧鎖定] 位置 {position} 設定為: {recognized_char}")
            
            # 有變更時更新
            if arrangement_changed:
                self.plugin.savePreferences()
                debug_log("[智慧鎖定] 已保存更改到偏好設定")
                
                # 根據當前狀態決定更新方式
                if not is_in_clear_mode:
                    debug_log("[智慧鎖定] 🔒 上鎖狀態 - 更新預覽")
                    try:
                        # 更新指定位置的字符
                        self._update_single_position(position, input_text)
                        
                        # 官方模式：更新 preview view 的屬性設定器
                        if (hasattr(self.plugin, 'windowController') and 
                            self.plugin.windowController and
                            hasattr(self.plugin.windowController, 'previewView')):
                            debug_log("[智慧鎖定] 更新 currentArrangement 屬性")
                            self.plugin.windowController.previewView.currentArrangement = self.plugin.currentArrangement
                        
                        # 更新介面
                        self.update_interface(None)
                        
                    except Exception as e:
                        error_log("[智慧鎖定] 更新預覽時發生錯誤", e)
                else:
                    debug_log("[智慧鎖定] 🔓 解鎖狀態")
                    # 在解鎖狀態下，檢查是否需要更新當前字符排列
                    if not (hasattr(self.plugin, 'lastInput') and self.plugin.lastInput):
                        debug_log("[智慧鎖定] 搜索框為空，更新當前排列")
                        current_char = self._get_current_editing_char()
                        if hasattr(self.plugin, 'currentArrangement'):
                            self.plugin.currentArrangement = [current_char] * FULL_ARRANGEMENT_SIZE
                            # 官方模式：更新 preview view 的屬性設定器
                            if (hasattr(self.plugin, 'windowController') and 
                                self.plugin.windowController and
                                hasattr(self.plugin.windowController, 'previewView')):
                                self.plugin.windowController.previewView.currentArrangement = self.plugin.currentArrangement
                
            else:
                debug_log("[智慧鎖定] 無變更，跳過更新")
        
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
                        
                        # 如果目前文字不是空的，且最後一個字符不是空格，則加入空格
                        if current_text and not current_text.endswith(' '):
                            new_text = current_text + ' ' + chars_to_insert
                        else:
                            new_text = current_text + chars_to_insert
                        
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
        """隨機排列按鈕回呼（最佳化版）"""
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
        """生成新的字符排列（9格版本，遵循 flow.md 邏輯）"""
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
                    # R1: 中心: activeGlyph, 鎖定格: lockedChars, 其餘格: 從 batchChars 隨機
                    arrangement[CENTER_POSITION] = activeGlyph
                    self._apply_locked_chars(arrangement, lockedChars)
                    self._fill_remaining_with_batch(arrangement, batchChars)
                    debug_log("R1: activeGlyph + 上鎖 + 有locked + 有batch")
                else:  # 無批量輸入
                    # R2: 中心: activeGlyph, 鎖定格: lockedChars, 其餘格: activeGlyph
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
                # R13: 中心: activeGlyph, 周圍格: activeGlyph
                arrangement = [activeGlyph] * FULL_ARRANGEMENT_SIZE
                debug_log("R13: activeGlyph + 解鎖 + 無batch")
        
        return arrangement
    
    def _handle_without_active_glyph(self, is_locked, has_locked, lockedChars, has_batch, batchChars):
        """處理沒有 activeGlyph 的情況"""
        arrangement = [None] * FULL_ARRANGEMENT_SIZE
        
        if is_locked:  # 上鎖模式
            if has_locked:  # 有鎖定字符
                if has_batch:  # 有批量輸入
                    # R7: 中心: 從 batchChars 隨機, 鎖定格: lockedChars, 其餘格: 從 batchChars 隨機
                    self._apply_locked_chars(arrangement, lockedChars)
                    self._fill_remaining_with_batch(arrangement, batchChars)
                    if arrangement[CENTER_POSITION] is None:  # 中心未被鎖定
                        arrangement[CENTER_POSITION] = random.choice(batchChars)
                    debug_log("R7: 無activeGlyph + 上鎖 + 有locked + 有batch")
                else:  # 無批量輸入
                    # R8: 中心: 空白, 鎖定格: lockedChars, 其餘格: 空白
                    self._apply_locked_chars(arrangement, lockedChars)
                    # 其餘位置保持 None（空白）
                    debug_log("R8: 無activeGlyph + 上鎖 + 有locked + 無batch")
            else:  # 無鎖定字符
                if has_batch:  # 有批量輸入
                    # R9: 中心: 從 batchChars 隨機, 周圍格: 從 batchChars 隨機
                    self._fill_all_with_batch(arrangement, batchChars)
                    debug_log("R9: 無activeGlyph + 上鎖 + 無locked + 有batch")
                else:  # 無批量輸入
                    # R10: 所有九格皆為空白
                    # arrangement 已經全為 None
                    debug_log("R10: 無activeGlyph + 上鎖 + 無locked + 無batch")
        else:  # 解鎖模式
            if has_batch:  # 有批量輸入
                # R11: 中心: 從 batchChars 隨機, 周圍格: 從 batchChars 隨機
                self._fill_all_with_batch(arrangement, batchChars)
                debug_log("R11: 無activeGlyph + 解鎖 + 有batch")
            else:  # 無批量輸入
                # R12: 所有九格皆為空白
                # arrangement 已經全為 None
                debug_log("R12: 無activeGlyph + 解鎖 + 無batch")
        
        return arrangement
    
    # === 9格填充輔助方法 ===
    
    def _apply_locked_chars(self, arrangement, lockedChars):
        """將鎖定字符應用到排列中"""
        for position, char in lockedChars.items():
            if 0 <= position < FULL_ARRANGEMENT_SIZE:
                arrangement[position] = char
    
    def _fill_remaining_with_batch(self, arrangement, batchChars):
        """用批量字符填充剩餘的None位置"""
        for i in range(FULL_ARRANGEMENT_SIZE):
            if arrangement[i] is None:
                arrangement[i] = random.choice(batchChars)
    
    def _fill_remaining_with_char(self, arrangement, char):
        """用指定字符填充剩餘的None位置"""
        for i in range(FULL_ARRANGEMENT_SIZE):
            if arrangement[i] is None:
                arrangement[i] = char
    
    def _fill_surrounding_with_batch(self, arrangement, batchChars):
        """用批量字符填充周圍8格（不包括中心格）"""
        for i in range(FULL_ARRANGEMENT_SIZE):
            if i != CENTER_POSITION:
                arrangement[i] = random.choice(batchChars)
    
    def _fill_all_with_batch(self, arrangement, batchChars):
        """用批量字符填充所有9格"""
        for i in range(FULL_ARRANGEMENT_SIZE):
            arrangement[i] = random.choice(batchChars)
    
    # === 輔助方法 ===
    
    def _update_single_position(self, position, input_text):
        """
        更新單個位置的字符，而不重新生成整個排列
        
        Args:
            position: 要更新的位置 (0-7)
            input_text: 輸入的文字
        """
        import random  # 確保在函數開頭就匯入 random 模組
        
        try:
            # 確保有 currentArrangement
            if not hasattr(self.plugin, 'currentArrangement') or not self.plugin.currentArrangement or len(self.plugin.currentArrangement) != 8:
                # 如果沒有目前排列，需要生成一個基礎排列
                debug_log("[單一更新] currentArrangement 不存在或長度不對，重新生成。")
                source_for_init = list(self.plugin.selectedChars) if hasattr(self.plugin, 'selectedChars') and self.plugin.selectedChars else []
                if not source_for_init:
                    source_for_init = [self._get_current_editing_char()]
                
                # smart_lock_character_callback 應該已經更新了 self.plugin.lockedChars
                locked_map_for_init = self.plugin.lockedChars if hasattr(self.plugin, 'lockedChars') else {}
                
                self.plugin.currentArrangement = generate_arrangement(
                    source_for_init,
                    locked_map_for_init, 8
                )
            
            # 建立 currentArrangement 的可變複本
            # 處理可能是不可變 NSArray 的情況
            if hasattr(self.plugin, 'currentArrangement'):
                current_arr = list(self.plugin.currentArrangement)
            else:
                current_arr = []
            
            # 確保排列有足夠的長度
            while len(current_arr) < 8:
                if hasattr(self.plugin, 'selectedChars') and self.plugin.selectedChars:
                    current_arr.append(random.choice(self.plugin.selectedChars))
                else:
                    current_arr.append(self._get_current_editing_char())
            
            # 更新特定位置
            if position < len(current_arr):
                if input_text:
                    # 有輸入：更新為識別的字符
                    recognized_char = self._recognize_character(input_text)
                    current_arr[position] = recognized_char
                    debug_log(f"[單一更新] 位置 {position} 更新為: {recognized_char}")
                else:
                    # 清空輸入：優先使用原始排列的字符
                    if hasattr(self.plugin, 'originalArrangement') and self.plugin.originalArrangement and position < len(self.plugin.originalArrangement):
                        # 使用原始排列中的字符
                        replacement_char = self.plugin.originalArrangement[position]
                        current_arr[position] = replacement_char
                        debug_log(f"[單一更新] 位置 {position} 清空，回復原始字符: {replacement_char}")
                    elif hasattr(self.plugin, 'selectedChars') and self.plugin.selectedChars:
                        # 沒有原始排列時，用隨機字符替換
                        replacement_char = random.choice(self.plugin.selectedChars)
                        current_arr[position] = replacement_char
                        debug_log(f"[單一更新] 位置 {position} 清空，替換為: {replacement_char}")
                    else:
                        # 沒有選擇字符，使用目前編輯字符
                        current_char = self._get_current_editing_char()
                        current_arr[position] = current_char
                        debug_log(f"[單一更新] 位置 {position} 清空，使用目前字符: {current_char}")
            
            # 將修改後的數組賦值回plugin
            self.plugin.currentArrangement = current_arr
            
            # 儲存更新
            self.plugin.savePreferences()
            debug_log(f"[單一更新] 目前排列: {self.plugin.currentArrangement}")
            
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
    
    def _recognize_character(self, input_text):
        """辨識字符，優先考慮完整輸入、區分大小寫"""
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
        
        # 6. 使用字型中的第一個有效字符
        if Glyphs.font and Glyphs.font.glyphs:
            for glyph in Glyphs.font.glyphs:
                if glyph.unicode:
                    try:
                        char = chr(int(glyph.unicode, 16))
                        return char
                    except:
                        continue
                elif glyph.name:
                    return glyph.name
        
        # 7. 絕對保底：回傳 "A"
        return "A"
