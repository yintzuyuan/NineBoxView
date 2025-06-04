# encoding: utf-8
"""
九宮格預覽外掛 - 事件處理器
Nine Box Preview Plugin - Event Handlers
"""

from __future__ import division, print_function, unicode_literals
import traceback
from GlyphsApp import Glyphs
from AppKit import NSTextField
from constants import DEBUG_MODE, DEFAULT_ZOOM
from utils import debug_log, parse_input_text, generate_arrangement, apply_locked_chars, validate_locked_positions, get_cached_glyph


class EventHandlers:
    """集中管理所有事件處理邏輯"""
    
    def __init__(self, plugin):
        self.plugin = plugin
    
    # === 界面更新 ===
    
    def update_interface(self, sender):
        """更新界面（優化版）"""
        try:
            # 避免重複更新
            if self.plugin._update_scheduled:
                return
            
            if hasattr(self.plugin, 'windowController') and self.plugin.windowController is not None:
                # 批次更新
                self.plugin._update_scheduled = True
                
                # 特殊情況處理：沒有選擇字符但有鎖定字符
                if (not self.plugin.selectedChars and hasattr(self.plugin, 'lockedChars') and 
                    self.plugin.lockedChars and not self._get_lock_state()):
                    debug_log("沒有選擇字符，但在上鎖狀態下有鎖定字符，重新生成排列")
                    self.generate_new_arrangement()
                
                # 觸發重繪
                if hasattr(self.plugin.windowController, 'redraw'):
                    self.plugin.windowController.redraw()
                
                # 更新控制面板 - 一般情況下不更新鎖定輸入框
                if hasattr(self.plugin.windowController, 'request_controls_panel_ui_update'):
                    self.plugin.windowController.request_controls_panel_ui_update(update_lock_fields=False)
                    
                self.plugin._update_scheduled = False
                
        except Exception as e:
            self.plugin._update_scheduled = False
            debug_log(f"更新介面時發生錯誤: {e}")
            if DEBUG_MODE:
                print(traceback.format_exc())
    
    def selection_changed(self, sender):
        """選擇變更處理"""
        try:
            # 清除快取
            if hasattr(self.plugin, 'clear_cache'):
                self.plugin.clear_cache()
            
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
            debug_log(f"選擇變更處理錯誤: {e}")
    
    # === 搜尋欄位相關 ===
    
    def search_field_callback(self, sender):
        """處理搜尋欄位輸入（優化版）"""
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
            
            if new_chars != self.plugin.selectedChars:
                self.plugin.selectedChars = new_chars
                self.generate_new_arrangement()
        else:
            # 輸入為空時的處理
            is_in_clear_mode = self._get_lock_state()
            has_locked_chars = hasattr(self.plugin, 'lockedChars') and self.plugin.lockedChars
            
            self.plugin.selectedChars = []  # 清空selectedChars
            
            if not is_in_clear_mode and has_locked_chars:
                # 上鎖狀態且有鎖定字符，重新生成排列
                self.generate_new_arrangement()
            else:
                # 解鎖狀態或沒有鎖定字符，清空currentArrangement
                self.plugin.currentArrangement = []

        # 更新介面與控制面板
        self.update_interface_for_search_field(None)
        
        # 更新控制面板但不更新鎖定輸入框
        if hasattr(self.plugin, 'windowController') and self.plugin.windowController:
            if hasattr(self.plugin.windowController, 'request_controls_panel_ui_update'):
                self.plugin.windowController.request_controls_panel_ui_update(update_lock_fields=False)
    
    def update_interface_for_search_field(self, sender):
        """專為搜尋欄位的更新"""
        try:
            if hasattr(self.plugin, 'windowController') and self.plugin.windowController is not None:
                self.plugin.windowController.redraw()
        except Exception as e:
            debug_log(f"更新搜尋欄位介面錯誤: {e}")
    
    # === 鎖定字符相關 ===
    
    def smart_lock_character_callback(self, sender):
        """智能鎖定字符回調（資料處理與即時更新）"""
        try:
            if not Glyphs.font:
                return
            
            # 解鎖狀態時，鎖定輸入欄不影響主視窗
            is_in_clear_mode = self._get_lock_state()
            if is_in_clear_mode:
                return
            
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
                else:
                    return  # 沒有變更，直接返回
            else:
                # 智能辨識
                recognized_char = self._recognize_character(input_text)
                
                # 檢查是否有變更
                if position not in self.plugin.lockedChars or self.plugin.lockedChars[position] != recognized_char:
                    self.plugin.lockedChars[position] = recognized_char
                    arrangement_changed = True
                else:
                    return  # 沒有變更，直接返回
            
            # 有變更時更新排列並重繪
            if arrangement_changed:
                self.plugin.savePreferences()
                
                # 更新排列和畫面
                if hasattr(self.plugin, 'selectedChars') and self.plugin.selectedChars:
                    self.generate_new_arrangement()
                elif self.plugin.lockedChars:  # 即使沒有選擇字符，如果有鎖定字符也更新
                    self.generate_new_arrangement()
                else:
                    self.update_interface(sender)
                
                # 直接重繪主畫面，不更新控制面板UI
                if hasattr(self.plugin, 'windowController') and self.plugin.windowController:
                    if hasattr(self.plugin.windowController, 'redraw'):
                        self.plugin.windowController.redraw()
        
        except Exception as e:
            debug_log(f"智能鎖定字符處理錯誤: {e}")
            if DEBUG_MODE:
                print(traceback.format_exc())
    
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
            
            # 備份當前狀態
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
            
            # 更新排列和介面
            self.generate_new_arrangement()
            self.plugin.savePreferences()
            self.update_interface(None)
            
        except Exception as e:
            debug_log(f"清空鎖定輸入框錯誤: {e}")
            if DEBUG_MODE:
                print(traceback.format_exc())
    
    # === 其他回調 ===
    
    def pick_glyph_callback(self, sender):
        """選擇字符按鈕回調（優化版）"""
        try:
            if not Glyphs.font:
                debug_log("警告：沒有開啟字型檔案")
                return
            
            # 準備選項列表
            options = self._prepare_glyph_options()
            
            if options:
                selection = Glyphs.displayDialog(
                    Glyphs.localize({
                        'en': u'Select glyphs (use Shift/Cmd for multiple selections)',
                        'zh-Hant': u'選擇字符（使用 Shift/Cmd 進行多選）',
                        'zh-Hans': u'选择字符（使用 Shift/Cmd 进行多选）',
                        'ja': u'グリフを選択（複数選択には Shift/Cmd を使用）',
                        'ko': u'글자 선택 (여러 개를 선택하려면 Shift/Cmd 사용)',
                    }),
                    options,
                    allowsMultipleSelection=True
                )
                
                if selection:
                    selected_chars = self._parse_glyph_selection(selection)
                    
                    if selected_chars:
                        self.plugin.selectedChars = selected_chars
                        self.generate_new_arrangement()
                        self.plugin.lastInput = "".join(selected_chars)
                        
                        if (hasattr(self.plugin, 'windowController') and 
                            self.plugin.windowController and
                            hasattr(self.plugin.windowController, 'controlsPanelView') and 
                            self.plugin.windowController.controlsPanelView and
                            hasattr(self.plugin.windowController.controlsPanelView, 'searchPanel')):
                            self.plugin.windowController.controlsPanelView.searchPanel.set_search_value(self.plugin.lastInput)
                        
                        self.plugin.savePreferences()
                        self.update_interface(None)
                        
        except Exception as e:
            debug_log(f"選擇字符錯誤: {e}")
    
    def randomize_callback(self, sender):
        """隨機排列按鈕回調（優化版）"""
        if not self.plugin.selectedChars:
            if Glyphs.font and Glyphs.font.selectedLayers:
                self.update_interface(None)
            return
        
        # 設定強制重排標記
        self.plugin.force_randomize = True
        self.generate_new_arrangement()
        
        # 直接調用重繪，避免觸發控制面板UI更新
        if hasattr(self.plugin, 'windowController') and self.plugin.windowController:
            if hasattr(self.plugin.windowController, 'redraw'):
                self.plugin.windowController.redraw()
        else:
            self.update_interface(None)
        
        self.plugin.force_randomize = False
    
    def reset_zoom(self, sender):
        """重置縮放"""
        self.plugin.zoomFactor = DEFAULT_ZOOM
        self.plugin.savePreferences()
        self.update_interface(None)
    
    # === 字符排列生成 ===
    
    def generate_new_arrangement(self):
        """生成新的字符排列（優化版）"""
        # 驗證鎖定字符
        if hasattr(self.plugin, 'lockedChars'):
            self.plugin.lockedChars = validate_locked_positions(self.plugin.lockedChars, Glyphs.font)
        
        # 檢查是否應用鎖定
        should_apply_locks = not self._get_lock_state()
        
        # 在解鎖狀態下且沒有selectedChars時清空排列
        is_in_clear_mode = self._get_lock_state()
        if is_in_clear_mode:
            if not self.plugin.selectedChars:
                self.plugin.currentArrangement = []
                self.plugin.savePreferences()
                return
        
        # 特殊處理空的selectedChars但有lockedChars的情況
        if not self.plugin.selectedChars:
            # 使用當前編輯的字符或預設值
            self._generate_default_arrangement(should_apply_locks)
            return
        
        # 生成基礎排列
        base_arrangement = generate_arrangement(self.plugin.selectedChars, 8)
        
        # 根據鎖頭狀態決定是否應用鎖定字符
        if should_apply_locks and hasattr(self.plugin, 'lockedChars') and self.plugin.lockedChars:
            self.plugin.currentArrangement = apply_locked_chars(
                base_arrangement, self.plugin.lockedChars, self.plugin.selectedChars
            )
        else:
            self.plugin.currentArrangement = base_arrangement
        
        self.plugin.savePreferences()
    
    # === 輔助方法 ===
    
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
        
        # 5. 使用當前正在編輯的字符
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
        
        # 7. 絕對保底：返回 "A"
        return "A"
    
    def _prepare_glyph_options(self):
        """準備字形選項列表"""
        options = []
        for glyph in Glyphs.font.glyphs:
            if glyph.unicode:
                try:
                    char = chr(int(glyph.unicode, 16))
                    options.append(f"{char} ({glyph.name})")
                except:
                    options.append(f".notdef ({glyph.name})")
            else:
                options.append(f".notdef ({glyph.name})")
        return options
    
    def _parse_glyph_selection(self, selection):
        """解析選擇的字形"""
        selected_chars = []
        for item in selection:
            if " (" in item and ")" in item:
                char = item.split(" (")[0]
                if char != ".notdef":
                    selected_chars.append(char)
        return selected_chars
    
    def _generate_default_arrangement(self, should_apply_locks):
        """生成預設排列"""
        # 如果是上鎖狀態且有鎖定字符，使用當前編輯的字符作為基礎排列
        if should_apply_locks and hasattr(self.plugin, 'lockedChars') and self.plugin.lockedChars:
            current_layer = None
            if Glyphs.font and Glyphs.font.selectedLayers:
                current_layer = Glyphs.font.selectedLayers[0]
            
            if current_layer and current_layer.parent:
                # 使用當前字符的名稱或Unicode值創建基礎排列
                current_glyph = current_layer.parent
                current_char = None
                if current_glyph.unicode:
                    try:
                        current_char = chr(int(current_glyph.unicode, 16))
                    except:
                        pass
                
                if not current_char and current_glyph.name:
                    current_char = current_glyph.name
                
                if current_char:
                    # 創建一個全是當前字符的基礎排列
                    base_arrangement = [current_char] * 8
                    
                    # 應用鎖定字符
                    self.plugin.currentArrangement = apply_locked_chars(
                        base_arrangement, self.plugin.lockedChars, []
                    )
                    self.plugin.savePreferences()
                    return
        
        # 使用當前編輯的字符
        current_layer = None
        if Glyphs.font and Glyphs.font.selectedLayers:
            current_layer = Glyphs.font.selectedLayers[0]
        
        if current_layer and current_layer.parent:
            current_glyph = current_layer.parent
            current_char = None
            if current_glyph.unicode:
                try:
                    current_char = chr(int(current_glyph.unicode, 16))
                except:
                    pass
            
            if not current_char and current_glyph.name:
                current_char = current_glyph.name
            
            if current_char:
                self.plugin.currentArrangement = [current_char] * 8
                self.plugin.savePreferences()
                return
        
        # 如果找不到當前字符，使用字型中的第一個有效字符
        if Glyphs.font and Glyphs.font.glyphs:
            for glyph in Glyphs.font.glyphs:
                if glyph.unicode:
                    try:
                        char = chr(int(glyph.unicode, 16))
                        self.plugin.currentArrangement = [char] * 8
                        self.plugin.savePreferences()
                        return
                    except:
                        continue
                elif glyph.name:
                    self.plugin.currentArrangement = [glyph.name] * 8
                    self.plugin.savePreferences()
                    return
        
        # 極端情況下，使用預設值
        self.plugin.currentArrangement = ["A"] * 8
        self.plugin.savePreferences()
