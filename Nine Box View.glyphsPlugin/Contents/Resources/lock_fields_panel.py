# encoding: utf-8
"""
九宮格預覽外掛 - 鎖定欄位面板模組
Nine Box Preview Plugin - Lock Fields Panel Module
"""

from __future__ import division, print_function, unicode_literals
import traceback
import objc
import random
from GlyphsApp import Glyphs
from AppKit import (
    NSView, NSTextField, NSButton, NSFont, NSColor, NSApp,
    NSMenu, NSMenuItem, NSNotificationCenter,
    NSViewWidthSizable, NSViewMaxYMargin,
    NSMakeRect, NSMakeSize, NSMakePoint,
    NSFocusRingTypeNone, NSCenterTextAlignment,
    NSBezelStyleRounded, NSBezelStyleRegularSquare,
    NSButtonTypeMomentaryPushIn, NSButtonTypeToggle,
    NSString, NSImage,
    NSFontAttributeName, NSForegroundColorAttributeName,
    NSCompositingOperationSourceOver
)
from Foundation import NSObject
try:
    from Quartz import CGColorCreateGenericRGB
except ImportError:
    CGColorCreateGenericRGB = None

from constants import DEBUG_MODE, MAX_LOCKED_POSITIONS
from utils import debug_log, error_log, get_cached_glyph


class LockCharacterField(NSTextField):
    """單字符鎖定輸入框"""
    
    def initWithFrame_position_plugin_(self, frame, position, plugin):
        """初始化單字符輸入框"""
        self = objc.super(LockCharacterField, self).initWithFrame_(frame)
        if self:
            self.position = position
            self.plugin = plugin
            self._setup_appearance()
            self._setup_context_menu()
            self._register_notifications()
        return self
    
    def _setup_appearance(self):
        """設定外觀"""
        self.setFont_(NSFont.systemFontOfSize_(16.0))
        self.setFocusRingType_(NSFocusRingTypeNone)
        self.setBezeled_(True)
        self.setEditable_(True)
        self.setUsesSingleLineMode_(True)
        self.setAlignment_(NSCenterTextAlignment)
        
        # 使用更符合 macOS 標準的輸入框顏色
        isDarkMode = NSApp.effectiveAppearance().name().containsString_("Dark")
        if isDarkMode:
            self.setBackgroundColor_(NSColor.textBackgroundColor())
        else:
            self.setBackgroundColor_(NSColor.whiteColor())
        
        # 設定提示
        lockedTooltip = Glyphs.localize({
            'en': u'Enter a character or Nice Name (only affects preview when lock mode is enabled)',
            'zh-Hant': u'輸入字符或 Nice Name（僅在鎖定模式啟用時影響預覽）',
            'zh-Hans': u'输入字符或 Nice Name（仅在锁定模式启用时影响预览）',
            'ja': u'文字または Nice Name を入力（ロックモードが有効な場合のみプレビューに影響）',
            'ko': u'문자 또는 Nice Name 입력 (잠금 모드가 활성화된 경우에만 미리보기에 영향)',
        })
        self.setToolTip_(lockedTooltip)
    
    def _setup_context_menu(self):
        """設定右鍵選單"""
        try:
            contextMenu = NSMenu.alloc().init()
            
            pickGlyphItem = NSMenuItem.alloc().initWithTitle_action_keyEquivalent_(
                Glyphs.localize({
                    'en': u'Select Glyphs from Font...',
                    'zh-Hant': u'從字型中選擇字符...',
                    'zh-Hans': u'从字体中选择字符...',
                    'ja': u'フォントから文字を選択...',
                    'ko': u'글꼴에서 글자 선택...',
                }),
                "pickGlyphAction:",
                ""
            )
            contextMenu.addItem_(pickGlyphItem)
            self.setMenu_(contextMenu)
            
        except Exception as e:
            error_log("設定右鍵選單錯誤", e)
    
    def _register_notifications(self):
        """註冊通知"""
        NSNotificationCenter.defaultCenter().addObserver_selector_name_object_(
            self,
            "textDidChange:",
            "NSControlTextDidChangeNotification",
            self
        )
    
    def pickGlyphAction_(self, sender):
        """選擇字符功能"""
        debug_log("鎖定欄位選擇字符選單被點擊")
        # 功能暫未實現
    
    def textDidChange_(self, notification):
        """文本變更時的智能回調"""
        try:
            debug_log(f"鎖定欄位 {self.position} 文本變更: {self.stringValue()}")
            if hasattr(self, 'plugin') and self.plugin:
                self.plugin.smartLockCharacterCallback(self)
        except Exception as e:
            error_log("智能鎖定字符處理錯誤", e)
    
    def dealloc(self):
        """析構函數"""
        NSNotificationCenter.defaultCenter().removeObserver_(self)
        objc.super(LockCharacterField, self).dealloc()


class LockFieldsPanel(NSView):
    """鎖定欄位面板視圖"""
    
    LOCK_FIELD_HEIGHT = 30  # 單行高度
    
    def initWithFrame_plugin_(self, frame, plugin):
        """初始化鎖定欄位面板"""
        self = objc.super(LockFieldsPanel, self).initWithFrame_(frame)
        if self:
            self.plugin = plugin
            self.lockFields = {}
            self.lockButton = None
            self.clearAllButton = None
            
            # 從 plugin 對象讀取鎖頭狀態
            self.isInClearMode = getattr(plugin, 'isInClearMode', False)
            debug_log(f"LockFieldsPanel 初始化鎖頭狀態：{'🔓 解鎖' if self.isInClearMode else '🔒 上鎖'}")
            
            self.setAutoresizingMask_(NSViewWidthSizable | NSViewMaxYMargin)
            self._setup_ui()
        return self
    
    def _setup_ui(self):
        """設定介面"""
        bounds = self.bounds()
        
        # 創建清除按鈕（底部）
        self._create_clear_button(bounds)
        
        # 創建鎖定輸入框九宮格（上方）
        self._create_lock_fields(bounds)
    
    def _create_lock_fields(self, bounds):
        """創建鎖定輸入框和鎖頭按鈕"""
        grid_spacing = 4
        button_height = 22
        spacing = 8
        
        # 計算每個輸入框的寬度
        available_width = bounds.size.width
        cell_width = (available_width - 2 * grid_spacing) / 3
        cell_height = min(cell_width, self.LOCK_FIELD_HEIGHT)
        
        # 從頂部開始（清除按鈕上方）
        current_y = button_height + spacing
        
        # 創建3x3網格
        position = 0
        for row in range(3):
            for col in range(3):
                # 計算每個單元格的位置（從底部向上）
                x = col * (cell_width + grid_spacing)
                y = current_y + (2 - row) * (cell_height + grid_spacing)
                
                if row == 1 and col == 1:  # 中央位置：放置鎖頭按鈕
                    self._create_lock_button(x, y, cell_width, cell_height)
                else:
                    # 其他位置：鎖定輸入框
                    fieldRect = NSMakeRect(x, y, cell_width, cell_height)
                    lockField = LockCharacterField.alloc().initWithFrame_position_plugin_(
                        fieldRect, position, self.plugin
                    )
                    lockField.setAutoresizingMask_(NSViewWidthSizable | NSViewMaxYMargin)
                    lockField.setFont_(NSFont.systemFontOfSize_(16.0))
                    
                    self.lockFields[position] = lockField
                    self.addSubview_(lockField)
                    position += 1
    
    def _create_lock_button(self, x, y, width, height):
        """創建鎖頭按鈕"""
        button_padding = 1
        lockRect = NSMakeRect(
            x + button_padding, 
            y + button_padding, 
            width - 2 * button_padding, 
            height - 2 * button_padding
        )
        
        self.lockButton = NSButton.alloc().initWithFrame_(lockRect)
        self.lockButton.setAutoresizingMask_(NSViewWidthSizable | NSViewMaxYMargin)
        self.lockButton.setTarget_(self)
        self.lockButton.setAction_("toggleLockMode:")
        
        # 使用極簡按鈕樣式
        self.lockButton.setBezelStyle_(NSBezelStyleRegularSquare)
        self.lockButton.setButtonType_(NSButtonTypeToggle)
        self.lockButton.setBordered_(False)
        
        # 設定字體與對齊
        self.lockButton.setFont_(NSFont.systemFontOfSize_(16.0))
        self.lockButton.setAlignment_(NSCenterTextAlignment)
        
        # 設定Layer屬性
        if hasattr(self.lockButton, 'setWantsLayer_'):
            self.lockButton.setWantsLayer_(True)
            if hasattr(self.lockButton, 'layer'):
                layer = self.lockButton.layer()
                if layer:
                    layer.setCornerRadius_(4.0)
                    layer.setShadowOpacity_(0)
        
        self.updateLockButton()
        self.addSubview_(self.lockButton)
    
    def _create_clear_button(self, bounds):
        """創建清除按鈕"""
        button_height = 22
        
        # 清空欄位按鈕，固定在底部
        clearAllRect = NSMakeRect(0, 0, bounds.size.width, button_height)
        self.clearAllButton = NSButton.alloc().initWithFrame_(clearAllRect)
        self.clearAllButton.setAutoresizingMask_(NSViewWidthSizable | NSViewMaxYMargin)
        
        # 極簡標題
        clearButtonTitle = Glyphs.localize({
            'en': u'Clear Lock',
            'zh-Hant': u'清空鎖定',
            'zh-Hans': u'清空锁定',
            'ja': u'ロックをクリア',
            'ko': u'잠금 지우기',
        })
        
        self.clearAllButton.setTitle_(clearButtonTitle)
        self.clearAllButton.setTarget_(self)
        self.clearAllButton.setAction_("clearAllFields:")
        self.clearAllButton.setBezelStyle_(NSBezelStyleRounded)
        self.clearAllButton.setButtonType_(NSButtonTypeMomentaryPushIn)
        self.clearAllButton.setFont_(NSFont.systemFontOfSize_(12.0))
        
        # 設定提示文字
        clearTooltip = Glyphs.localize({
            'en': u'Clear all lock fields',
            'zh-Hant': u'清空所有鎖定欄位',
            'zh-Hans': u'清空所有锁定栏位',
            'ja': u'すべてのロックフィールドをクリア',
            'ko': u'모든 잠금 필드 지우기',
        })
        self.clearAllButton.setToolTip_(clearTooltip)
        
        self.addSubview_(self.clearAllButton)
    
    def toggleLockMode_(self, sender):
        """切換鎖頭模式"""
        try:
            # 先儲存當前狀態
            was_in_clear_mode = self.isInClearMode
            
            # 先檢查必要的物件和方法
            if was_in_clear_mode and not hasattr(self.plugin, 'event_handlers'):
                debug_log("警告：event_handlers 未初始化，無法進行同步")
                return
            
            # 記錄切換前有內容的輸入框位置
            positions_with_content = []
            if hasattr(self, 'lockFields') and self.lockFields:
                for position, field in self.lockFields.items():
                    if field.stringValue().strip():
                        positions_with_content.append(position)
                debug_log(f"切換前有內容的輸入框位置: {positions_with_content}")
            
            # === 新增：從解鎖切換到鎖定時，保存當前的隨機排列 ===
            if was_in_clear_mode and hasattr(self.plugin, 'currentArrangement'):
                # 保存當前的隨機排列，供之後回復使用
                self.plugin.originalArrangement = list(self.plugin.currentArrangement)
                debug_log(f"保存原始隨機排列: {self.plugin.originalArrangement}")
                # 儲存到偏好設定
                self.plugin.savePreferences()
            
            # 從解鎖切換到上鎖時同步輸入框內容（但不觸發重新生成排列）
            if was_in_clear_mode:
                debug_log("從🔓解鎖切換到🔒鎖定：開始同步流程")
                try:
                    debug_log("1. 預先同步輸入欄內容（不觸發重新生成）")
                    self._sync_input_fields_to_locked_chars_without_regenerate()
                    
                    # 確認同步是否成功
                    if hasattr(self.plugin, 'lockedChars'):
                        debug_log(f"同步成功，目前鎖定字符：{self.plugin.lockedChars}")
                    else:
                        debug_log("警告：同步後 lockedChars 未正確設置")
                except Exception as e:
                    error_log("同步過程發生錯誤", e)
                debug_log("同步流程完成")
            
            # 更新狀態
            self.isInClearMode = not self.isInClearMode
            debug_log(f"鎖頭模式切換：{'🔓 解鎖' if self.isInClearMode else '🔒 上鎖'}")
            
            # 更新 UI
            self.updateLockButton()
            
            # 同步到 plugin 對象
            if hasattr(self, 'plugin') and self.plugin:
                # 更新 plugin 的狀態
                self.plugin.isInClearMode = self.isInClearMode
                debug_log(f"已同步鎖頭狀態到 plugin.isInClearMode = {self.isInClearMode}")
                
                # === 修改：確保每次切換都更新預覽（只更新有內容的位置）===
                # 先更新排列
                self._update_arrangement_for_lock_toggle(positions_with_content)
                
                # === 修正：當輸入框全部清空時，從鎖定切換到解鎖不強制重繪 ===
                # 檢查是否需要強制重繪
                should_force_redraw = True
                if was_in_clear_mode and not positions_with_content:
                    # 從解鎖切換到鎖定，且輸入框全部清空：不需要強制重繪
                    should_force_redraw = False
                    debug_log("[鎖頭切換] 輸入框全部清空，從解鎖切換到鎖定，跳過強制重繪")
                elif not was_in_clear_mode and self.isInClearMode and not positions_with_content:
                    # 從鎖定切換到解鎖，且輸入框全部清空：不需要強制重繪
                    should_force_redraw = False
                    debug_log("[鎖頭切換] 輸入框全部清空，從鎖定切換到解鎖，跳過強制重繪")
                
                # 根據判斷結果決定是否強制重繪
                if should_force_redraw:
                    # 強制重繪預覽 - 確保切換能看到更新
                    if (hasattr(self.plugin, 'windowController') and 
                        self.plugin.windowController and
                        hasattr(self.plugin.windowController, 'previewView')):
                        debug_log("[鎖頭切換] 強制重繪預覽")
                        self.plugin.windowController.previewView.force_redraw()
                    else:
                        debug_log("[鎖頭切換] 警告：無法取得 previewView，嘗試通過 updateInterface 更新")
                        # 如果無法直接重繪，則通過 updateInterface 更新
                        self.plugin.updateInterface(None)
                else:
                    debug_log("[鎖頭切換] 跳過強制重繪，保持預覽不變")
                
                # 儲存偏好設定
                self.plugin.savePreferences()
                debug_log("已儲存鎖頭狀態到偏好設定")
            
        except Exception as e:
            error_log("切換鎖頭模式錯誤", e)
            if hasattr(self, 'lockButton'):
                self.updateLockButton()
    
    def _update_arrangement_for_lock_toggle(self, positions_with_content):
        """特殊處理鎖頭切換時的排列更新（只更新有內容的輸入框位置）"""
        try:
            if not hasattr(self.plugin, 'currentArrangement'):
                self.plugin.currentArrangement = []

            # --- 新增：確保 currentArrangement 是 list ---
            if not isinstance(self.plugin.currentArrangement, list):
                self.plugin.currentArrangement = list(self.plugin.currentArrangement)
            # --- end ---

            # 檢查目前狀態
            is_in_clear_mode = self.isInClearMode
            has_locked_chars = hasattr(self.plugin, 'lockedChars') and self.plugin.lockedChars
            has_selected_chars = hasattr(self.plugin, 'selectedChars') and self.plugin.selectedChars
            
            debug_log(f"[鎖頭切換更新] 狀態: {'🔓 解鎖' if is_in_clear_mode else '🔒 上鎖'}")
            debug_log(f"[鎖頭切換更新] 有鎖定字符: {has_locked_chars}, 有選擇字符: {has_selected_chars}")
            debug_log(f"[鎖頭切換更新] 有內容的位置: {positions_with_content}")
            
            # === 確保每次切換都會更新預覽 ===
            
            if is_in_clear_mode:
                # === 解鎖狀態：回復原始隨機排列 ===
                if hasattr(self.plugin, 'originalArrangement') and self.plugin.originalArrangement:
                    # 優先使用保存的原始排列
                    self.plugin.currentArrangement = list(self.plugin.originalArrangement)
                    debug_log(f"[鎖頭切換更新] 解鎖狀態 - 回復原始排列: {self.plugin.currentArrangement}")
                    return  # 完成更新，直接返回
                elif positions_with_content and self.plugin.currentArrangement and len(self.plugin.currentArrangement) >= 8:
                    # 沒有原始排列時，只替換切換前有內容的位置為隨機字符
                    if has_selected_chars:
                        # --- 新增：確保 currentArrangement 是 list ---
                        if not isinstance(self.plugin.currentArrangement, list):
                            self.plugin.currentArrangement = list(self.plugin.currentArrangement)
                        # --- end ---
                        for position in positions_with_content:
                            if position < len(self.plugin.currentArrangement):
                                replacement_char = random.choice(self.plugin.selectedChars)
                                self.plugin.currentArrangement[position] = replacement_char
                                debug_log(f"[鎖頭切換更新] 解鎖 - 位置 {position} 替換為: {replacement_char}")
                        debug_log(f"[鎖頭切換更新] 解鎖狀態 - 只更新了位置 {positions_with_content}")
                        debug_log(f"[鎖頭切換更新] 最終排列: {self.plugin.currentArrangement}")
                        return  # 完成更新，直接返回
                    else:
                        # 沒有選擇字符時清空排列
                        self.plugin.currentArrangement = []
                        debug_log("[鎖頭切換更新] 解鎖狀態 - 無選擇字符，清空排列")
                elif has_selected_chars:
                    # === 修正：當輸入框全部清空時，不生成新的隨機排列 ===
                    if not positions_with_content:
                        # 如果沒有任何輸入框有內容（全部清空），保持現有排列不變
                        debug_log("[鎖頭切換更新] 解鎖狀態 - 輸入框全部清空，保持現有排列不變")
                        if self.plugin.currentArrangement:
                            debug_log(f"[鎖頭切換更新] 維持現有排列: {self.plugin.currentArrangement}")
                        else:
                            debug_log("[鎖頭切換更新] 無現有排列")
                        return  # 不更新排列，直接返回
                    else:
                        # 有輸入框有內容但沒有現有排列，生成新的隨機排列
                        from utils import generate_arrangement
                        self.plugin.currentArrangement = generate_arrangement(self.plugin.selectedChars, 8)
                        debug_log(f"[鎖頭切換更新] 解鎖狀態 - 生成新隨機排列: {self.plugin.currentArrangement}")
                else:
                    # 沒有選擇字符：清空排列
                    self.plugin.currentArrangement = []
                    debug_log("[鎖頭切換更新] 解鎖狀態 - 清空排列")
            else:
                # === 上鎖狀態：只更新有內容的輸入框位置 ===
                # 重要：從解鎖切換到鎖定時，應該保持現有排列，只更新有內容的位置
                
                # 先確保有基礎排列（但不要覆蓋現有排列）
                if not self.plugin.currentArrangement or len(self.plugin.currentArrangement) < 8:
                    # 只有在完全沒有排列時才創建新的
                    if has_selected_chars:
                        from utils import generate_arrangement
                        self.plugin.currentArrangement = generate_arrangement(self.plugin.selectedChars, 8)
                        debug_log(f"[鎖頭切換更新] 創建初始排列: {self.plugin.currentArrangement}")
                    else:
                        # 使用當前編輯的字符填充
                        current_char = self._get_current_editing_char()
                        self.plugin.currentArrangement = [current_char] * 8
                        debug_log(f"[鎖頭切換更新] 使用當前字符創建初始排列: {current_char}")
                
                # --- 新增：確保 currentArrangement 是 list ---
                if not isinstance(self.plugin.currentArrangement, list):
                    self.plugin.currentArrangement = list(self.plugin.currentArrangement)
                # --- end ---

                # 只更新有內容的輸入框對應的位置
                if has_locked_chars and positions_with_content:
                    # 只更新那些有內容的位置
                    updated_positions = []
                    for position in positions_with_content:
                        if position in self.plugin.lockedChars and position < len(self.plugin.currentArrangement):
                            char_or_name = self.plugin.lockedChars[position]
                            self.plugin.currentArrangement[position] = char_or_name
                            updated_positions.append(position)
                            debug_log(f"[鎖頭切換更新] 更新位置 {position}: {char_or_name}")
                    
                    debug_log(f"[鎖頭切換更新] 上鎖狀態 - 只更新了有內容的位置 {updated_positions}")
                    debug_log(f"[鎖頭切換更新] 最終排列: {self.plugin.currentArrangement}")
                else:
                    # 沒有需要更新的位置，保持現有排列不變
                    debug_log("[鎖頭切換更新] 上鎖狀態 - 無需更新，保持現有排列不變")
                    debug_log(f"[鎖頭切換更新] 當前排列: {self.plugin.currentArrangement}")
            
        except Exception as e:
            error_log("[鎖頭切換更新] 錯誤", e)
    
    def _get_current_editing_char(self):
        """取得當前正在編輯的字符"""
        try:
            if Glyphs.font and Glyphs.font.selectedLayers:
                current_layer = Glyphs.font.selectedLayers[0]
                if current_layer and current_layer.parent:
                    current_glyph = current_layer.parent
                    if current_glyph.unicode:
                        try:
                            return chr(int(current_glyph.unicode, 16))
                        except:
                            pass
                    if current_glyph.name:
                        return current_glyph.name
        except:
            pass
        return "A"  # 預設值
    
    def _sync_input_fields_to_locked_chars(self):
        """同步輸入欄內容到 plugin.lockedChars（修正版）"""
        try:
            # 基本檢查
            if not hasattr(self, 'plugin') or not self.plugin:
                debug_log("警告：無法取得 plugin 實例")
                return
            
            # 檢查必要的物件和方法
            if not hasattr(self.plugin, 'event_handlers'):
                debug_log("警告：plugin.event_handlers 未初始化")
                return
            
            if not hasattr(self.plugin, 'lockedChars'):
                self.plugin.lockedChars = {}
            
            debug_log("[同步] 開始同步鎖定字符")
            
            # 清除現有的 lockedChars
            self.plugin.lockedChars.clear()
            
            # 遍歷所有鎖定輸入欄
            for position, field in self.lockFields.items():
                input_text = field.stringValue().strip()
                if input_text:
                    # 使用 event_handlers 的 _recognize_character 方法
                    try:
                        recognized_char = self.plugin.event_handlers._recognize_character(input_text)
                        if recognized_char:
                            self.plugin.lockedChars[position] = recognized_char
                            debug_log(f"[同步] 位置 {position}: '{input_text}' → '{recognized_char}'")
                        else:
                            debug_log(f"[同步] 位置 {position}: '{input_text}' 無法辨識")
                    except Exception as e:
                        error_log("[同步] 字符辨識錯誤", e)
                        continue
                else:
                    debug_log(f"[同步] 位置 {position}: 空輸入，不設定鎖定")
            
            # 儲存偏好設定
            if hasattr(self.plugin, 'savePreferences'):
                self.plugin.savePreferences()
                debug_log(f"[同步] 已儲存 {len(self.plugin.lockedChars)} 個鎖定字符到偏好設定")
            
            # 觸發重新生成排列
            if hasattr(self.plugin, 'generateNewArrangement'):
                debug_log("[同步] 觸發重新生成排列")
                self.plugin.generateNewArrangement()
            
        except Exception as e:
            error_log("同步輸入欄內容錯誤", e)
    
    def _sync_input_fields_to_locked_chars_without_regenerate(self):
        """同步輸入欄內容到 plugin.lockedChars（不觸發重新生成排列）"""
        try:
            # 基本檢查
            if not hasattr(self, 'plugin') or not self.plugin:
                debug_log("警告：無法取得 plugin 實例")
                return
            
            # 檢查必要的物件和方法
            if not hasattr(self.plugin, 'event_handlers'):
                debug_log("警告：plugin.event_handlers 未初始化")
                return
            
            if not hasattr(self.plugin, 'lockedChars'):
                self.plugin.lockedChars = {}
            
            debug_log("[同步-無重生] 開始同步鎖定字符（不觸發重新生成）")
            
            # 清除現有的 lockedChars
            self.plugin.lockedChars.clear()
            
            # 遍歷所有鎖定輸入欄
            for position, field in self.lockFields.items():
                input_text = field.stringValue().strip()
                if input_text:
                    # 使用 event_handlers 的 _recognize_character 方法
                    try:
                        recognized_char = self.plugin.event_handlers._recognize_character(input_text)
                        if recognized_char:
                            self.plugin.lockedChars[position] = recognized_char
                            debug_log(f"[同步-無重生] 位置 {position}: '{input_text}' → '{recognized_char}'")
                        else:
                            debug_log(f"[同步-無重生] 位置 {position}: '{input_text}' 無法辨識")
                    except Exception as e:
                        error_log("[同步-無重生] 字符辨識錯誤", e)
                        continue
                else:
                    debug_log(f"[同步-無重生] 位置 {position}: 空輸入，不設定鎖定")
            
            # 儲存偏好設定
            if hasattr(self.plugin, 'savePreferences'):
                self.plugin.savePreferences()
                debug_log(f"[同步-無重生] 已儲存 {len(self.plugin.lockedChars)} 個鎖定字符到偏好設定")
            
            # 注意：不觸發重新生成排列
            debug_log("[同步-無重生] 同步完成，不觸發重新生成排列")
            
        except Exception as e:
            error_log("同步輸入欄內容錯誤", e)
    
    def createLockImage(self, locked=True):
        """創建極簡鎖頭圖示"""
        imageSize = 18
        lockImage = NSImage.alloc().initWithSize_((imageSize, imageSize))
        
        lockImage.lockFocus()
        
        try:
            NSColor.clearColor().set()
            import AppKit
            AppKit.NSRectFill(((0, 0), (imageSize, imageSize)))
            
            fontSize = 13.0
            font = NSFont.systemFontOfSize_(fontSize)
            
            attrs = {
                NSFontAttributeName: font, 
                NSForegroundColorAttributeName: NSColor.controlTextColor()
            }
            
            symbol = "🔒" if locked else "🔓"
            
            string = NSString.stringWithString_(symbol)
            stringSize = string.sizeWithAttributes_(attrs)
            
            x = (imageSize - stringSize.width) / 2
            y = (imageSize - stringSize.height) / 2
            
            string.drawAtPoint_withAttributes_(NSMakePoint(x, y), attrs)
            
            debug_log(f"已創建極簡{'鎖定' if locked else '解鎖'}圖示")
            
        except Exception as e:
            error_log("創建極簡鎖頭圖示時發生錯誤", e)
            
            try:
                systemIcon = None
                
                if locked:
                    systemIcon = NSImage.imageNamed_("NSLockLockedTemplate")
                else:
                    systemIcon = NSImage.imageNamed_("NSLockUnlockedTemplate")
                
                if systemIcon:
                    lockImage.unlockFocus()
                    return systemIcon
            except:
                pass
            
        finally:
            lockImage.unlockFocus()
        
        lockImage.setTemplate_(True)
        
        return lockImage
    
    def updateLockButton(self):
        """更新鎖頭按鈕顯示"""
        try:
            if not hasattr(self, 'lockButton'):
                return
            
            is_locked = not self.isInClearMode
            lockImage = self.createLockImage(is_locked)
            
            isDarkMode = NSApp.effectiveAppearance().name().containsString_("Dark")
            
            if lockImage:
                self.lockButton.setImage_(lockImage)
                self.lockButton.setTitle_("")
                self.lockButton.setState_(1 if is_locked else 0)
                
                # 設置背景色（如果有 layer）
                if hasattr(self.lockButton, 'layer') and self.lockButton.layer():
                    layer = self.lockButton.layer()
                    
                    try:
                        if is_locked:
                            if CGColorCreateGenericRGB:
                                color = NSColor.controlAccentColor().colorWithAlphaComponent_(0.3)
                                r, g, b, a = color.redComponent(), color.greenComponent(), color.blueComponent(), color.alphaComponent()
                                cgColor = CGColorCreateGenericRGB(r, g, b, a)
                                layer.setBackgroundColor_(cgColor)
                        else:
                            if CGColorCreateGenericRGB:
                                if isDarkMode:
                                    cgColor = CGColorCreateGenericRGB(0.25, 0.25, 0.25, 0.5)
                                else:
                                    cgColor = CGColorCreateGenericRGB(0.85, 0.85, 0.85, 0.5)
                                layer.setBackgroundColor_(cgColor)
                    except Exception as e:
                        debug_log(f"設定鎖頭按鈕背景色時發生錯誤（可忽略）: {e}")
                    
                    layer.setBorderWidth_(0.0)
                
                # 設置圖示顏色
                if hasattr(self.lockButton, 'setContentTintColor_'):
                    if is_locked:
                        self.lockButton.setContentTintColor_(NSColor.controlAccentColor())
                    else:
                        if isDarkMode:
                            self.lockButton.setContentTintColor_(NSColor.secondaryLabelColor())
                        else:
                            self.lockButton.setContentTintColor_(NSColor.labelColor())
                
                # 設置工具提示
                if self.isInClearMode:
                    tooltip = Glyphs.localize({
                        'en': u'Unlock Mode (click to lock)',
                        'zh-Hant': u'解鎖模式（點擊上鎖）',
                        'zh-Hans': u'解锁模式（点击上锁）',
                        'ja': u'アンロックモード（クリックしてロック）',
                        'ko': u'잠금 해제 모드 (클릭하여 잠금)',
                    })
                else:
                    tooltip = Glyphs.localize({
                        'en': u'Lock Mode (click to unlock)',
                        'zh-Hant': u'鎖定模式（點擊解鎖）',
                        'zh-Hans': u'锁定模式（点击解锁）',
                        'ja': u'ロックモード（クリックして解除）',
                        'ko': u'잠금 모드 (클릭하여 해제)',
                    })
                
                self.lockButton.setToolTip_(tooltip)
                self.lockButton.setNeedsDisplay_(True)
                
                debug_log(f"已更新鎖頭按鈕外觀：{'🔒 鎖定' if is_locked else '🔓 解鎖'}")
            else:
                # 後備方案：極簡文字按鈕
                debug_log("圖示創建失敗，使用極簡文字後備方案")
                
                title = "🔒" if not self.isInClearMode else "🔓"
                self.lockButton.setTitle_(title)
                self.lockButton.setImage_(None)
                self.lockButton.setFont_(NSFont.systemFontOfSize_(14.0))
                
                if hasattr(self.lockButton, 'setContentTintColor_'):
                    self.lockButton.setContentTintColor_(NSColor.controlTextColor())
            
        except Exception as e:
            error_log("更新鎖頭按鈕錯誤", e)
            if hasattr(self, 'lockButton'):
                title = "🔒" if not self.isInClearMode else "🔓"
                self.lockButton.setTitle_(title)
                self.lockButton.setImage_(None)
    
    def clearAllFields_(self, sender):
        """清空所有鎖定輸入框"""
        try:
            debug_log("清空所有欄位按鈕被點擊")
            
            # 清空所有鎖定輸入框
            if hasattr(self, 'lockFields') and self.lockFields:
                for position, field in self.lockFields.items():
                    field.setStringValue_("")
                    debug_log(f"清空位置 {position} 的輸入框")
            
            # 更新 plugin 的 lockedChars
            if hasattr(self, 'plugin') and self.plugin:
                if hasattr(self.plugin, 'lockedChars'):
                    # 備份當前狀態
                    if hasattr(self.plugin, 'previousLockedChars'):
                        self.plugin.previousLockedChars = self.plugin.lockedChars.copy()
                    
                    # 記錄被清除的鎖定位置
                    cleared_positions = list(self.plugin.lockedChars.keys())
                    debug_log(f"將清除的鎖定位置: {cleared_positions}")
                    
                    # 清空鎖定字符
                    self.plugin.lockedChars.clear()
                    debug_log("已清空 plugin.lockedChars")
                    
                    # === 確保每次清除都更新預覽（包括上鎖和解鎖狀態）===
                    # 在上鎖狀態時更新 currentArrangement
                    if not self.isInClearMode:  # 上鎖狀態
                        debug_log("🔒 上鎖狀態 - 更新排列並重繪")
                        
                        # === 修改：優先使用原始排列 ===
                        if hasattr(self.plugin, 'originalArrangement') and self.plugin.originalArrangement:
                            # 回復原始排列
                            self.plugin.currentArrangement = list(self.plugin.originalArrangement)
                            debug_log(f"清空鎖定 - 回復原始排列: {self.plugin.currentArrangement}")
                        elif hasattr(self.plugin, 'currentArrangement') and self.plugin.currentArrangement:
                            # 沒有原始排列時，使用先前的邏輯
                            # 確保 currentArrangement 是可變列表
                            if not isinstance(self.plugin.currentArrangement, list):
                                self.plugin.currentArrangement = list(self.plugin.currentArrangement)
                            debug_log(f"確保 currentArrangement 是可變列表: {type(self.plugin.currentArrangement)}")
                            # 從選擇的字符中取得替代字符
                            if hasattr(self.plugin, 'selectedChars') and self.plugin.selectedChars:
                                # 確保 selectedChars 是可變列表
                                self.plugin.selectedChars = list(self.plugin.selectedChars)
                                
                                # 只對被清除的位置進行替換
                                for pos in cleared_positions:
                                    if pos < len(self.plugin.currentArrangement):
                                        # 隨機選擇一個字符來替代
                                        replacement_char = random.choice(self.plugin.selectedChars)
                                        self.plugin.currentArrangement[pos] = replacement_char
                                        debug_log(f"位置 {pos} 替換為: {replacement_char}")
                            else:
                                # 如果沒有 selectedChars，使用當前編輯字符
                                for pos in cleared_positions:
                                    if pos < len(self.plugin.currentArrangement):
                                        # 使用當前編輯字符
                                        current_char = self._get_current_editing_char()
                                        self.plugin.currentArrangement[pos] = current_char
                                        debug_log(f"位置 {pos} 使用當前字符: {current_char}")
                    else:
                        debug_log("🔓 解鎖狀態 - 雖然不影響預覽，但仍強制重繪以確保一致性")
                    
                    # 儲存偏好設定
                    self.plugin.savePreferences()
                    
                    # 無論什麼狀態都強制重繪預覽
                    if (hasattr(self.plugin, 'windowController') and 
                        self.plugin.windowController and
                        hasattr(self.plugin.windowController, 'previewView')):
                        debug_log("[清除所有] 強制重繪預覽")
                        self.plugin.windowController.previewView.force_redraw()
            
            debug_log("完成清空所有輸入框")
            
        except Exception as e:
            error_log("清空所有欄位錯誤", e)
    
    def update_lock_fields(self, plugin_state):
        """更新鎖定輸入框內容"""
        try:
            if hasattr(plugin_state, 'lockedChars') and hasattr(self, 'lockFields'):
                # 先清空所有欄位
                for field in self.lockFields.values():
                    field.setStringValue_("")
                
                # 再填入已儲存的鎖定字符
                for position, char_or_name in plugin_state.lockedChars.items():
                    if position in self.lockFields:
                        self.lockFields[position].setStringValue_(char_or_name)
                        debug_log(f"填入位置 {position}: '{char_or_name}'")
        except Exception as e:
            error_log("更新鎖定輸入框錯誤", e)
    
    def get_lock_state(self):
        """取得鎖頭狀態"""
        return self.isInClearMode
    
    def set_lock_state(self, is_clear_mode):
        """設定鎖頭狀態"""
        self.isInClearMode = is_clear_mode
        self.updateLockButton()
    
    def dealloc(self):
        """析構函數"""
        objc.super(LockFieldsPanel, self).dealloc()
