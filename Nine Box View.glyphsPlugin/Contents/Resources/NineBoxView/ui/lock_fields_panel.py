# encoding: utf-8

"""
九宮格預覽外掛 - 鎖定欄位面板元件
基於原版 LockFieldsPanel 的完整復刻，適配平面座標系統 (0-8)
"""

from __future__ import division, print_function, unicode_literals
import objc
import traceback
from AppKit import (
    NSView, NSTextField, NSButton, NSFont, NSColor, NSImage,
    NSViewWidthSizable, NSViewMaxYMargin, NSMakeRect,
    NSCenterTextAlignment, NSBezelStyleRegularSquare, NSButtonTypeToggle,
    NSFontAttributeName, NSForegroundColorAttributeName, NSNotificationCenter
)

# 本地化支援
from ..localization import localize

# 平面座標系統常數
CENTER_POSITION = 4  # 中央位置
GRID_SIZE_TOTAL = 9  # 總共9個位置 (0-8)

# UI 常數（基於原版設定）
LOCK_FIELD_HEIGHT = 30
LOCK_FIELDS_INTERNAL_GRID_SPACING = 5
LOCK_FIELDS_CLEAR_BUTTON_HEIGHT = 30
LOCK_FIELDS_SPACING_ABOVE_BUTTON = 5
LOCK_BUTTON_PADDING = 2
LOCK_BUTTON_CORNER_RADIUS = 4
LOCK_IMAGE_SIZE = 16
LOCK_IMAGE_FONT_SIZE = 12

class LockCharacterField(NSTextField):
    """單字符鎖定輸入框 - 基於原版設計"""
    
    def initWithFrame_position_plugin_(self, frame, position, plugin):
        """初始化單字符輸入框"""
        self = objc.super(LockCharacterField, self).initWithFrame_(frame)
        if self:
            self.position = position
            self.plugin = plugin
            self._programmatic_update = False  # 標記是否為程式化更新
            self._setup_field()
        return self
    
    def _setup_field(self):
        """統一的輸入框設定 - 使用 DrawBot 風格的等寬字體並啟用富文本支援"""
        try:
            # 使用 DrawBot 風格的等寬字體工具
            from ..core.utils import setup_text_field_for_monospace
            setup_text_field_for_monospace(self)
            
            self.setAlignment_(NSCenterTextAlignment)
            self.setStringValue_("")
            
            # === NSTextField 富文本和底線支援設定 ===
            
            # 啟用富文本編輯屬性（關鍵：讓 NSTextField 支援屬性字符串）
            try:
                self.setAllowsEditingTextAttributes_(True)
            except Exception:
                print(traceback.format_exc())
            
            # 啟用匯入富文本（讓 NSTextField 接受屬性字符串）
            try:
                self.setImportsGraphics_(False)  # 關閉圖形匯入，但保持文本格式
            except Exception:
                print(traceback.format_exc())
            
            # 確保 NSTextField 可以顯示屬性字符串
            try:
                # 檢查是否有 cell，並設定其屬性
                cell = self.cell()
                if cell:
                    # 確保 cell 支援屬性字符串
                    if hasattr(cell, 'setAllowsEditingTextAttributes_'):
                        cell.setAllowsEditingTextAttributes_(True)
                    
                    if hasattr(cell, 'setImportsGraphics_'):
                        cell.setImportsGraphics_(False)
                        
            except Exception:
                pass
            
            # 通知註冊
            center = NSNotificationCenter.defaultCenter()
            center.addObserver_selector_name_object_(
                self, 'textDidChange:', 'NSControlTextDidChangeNotification', self
            )
            center.addObserver_selector_name_object_(
                self, 'controlTextDidBeginEditing:', 'NSControlTextDidBeginEditingNotification', self
            )
            self.setDelegate_(self)
            
            # Tooltip 設定
            self._update_tooltip()
            
        except Exception:
            print(traceback.format_exc())
    
    def textDidChange_(self, notification):
        """文字變更處理 - 委派給事件處理器並執行視覺標注"""
        text = self.stringValue()
        
        
        # 執行視覺標注（僅對非程式化更新）
        if not hasattr(self, '_programmatic_update') or not self._programmatic_update:
            self._apply_visual_feedback()
        
        if self._validate_event_handler('handle_lock_field_change'):
            self.plugin.event_handler.handle_lock_field_change(self, text)
        else:
            pass
    
    def _update_tooltip(self):
        """更新 tooltip 顯示鎖定字符名稱"""
        if self.position == CENTER_POSITION:
            self.setToolTip_(None)
            return
        
        try:
            locked_char = self._get_locked_char_for_position()
            if locked_char:
                # 只在有內容時顯示鎖定字符
                self.setToolTip_(locked_char)
            else:
                # 無內容時不顯示tooltip
                self.setToolTip_(None)
        except Exception:
            print(traceback.format_exc())
            self.setToolTip_(None)
    
    def _get_locked_char_for_position(self):
        """取得當前位置的鎖定字符"""
        if not hasattr(self.plugin, 'lock_inputs'):
            return None
        
        if self.position == CENTER_POSITION:
            return None  # 中心格不能鎖定
            
        locked_char = self.plugin.lock_inputs[self.position]
        return locked_char.strip() if locked_char else None
    
    def _apply_visual_feedback(self):
        """套用視覺標注（整合 VisualFeedbackService）"""
        try:
            current_text = self.stringValue()
            if not current_text:
                return
                
            # 執行字符驗證並套用視覺標注
            from ..core.input_recognition import InputRecognitionService, VisualFeedbackService
            validation_result = InputRecognitionService.validate_glyph_input(current_text)
            VisualFeedbackService.apply_visual_feedback(self, validation_result)
            
            # 更新工具提示以顯示驗證結果
            if validation_result['valid']:
                valid_count = len(validation_result['valid_glyphs'])
                if valid_count > 0:
                    first_valid = validation_result['valid_glyphs'][0]
                    if valid_count > 1:
                        self.setToolTip_(f"位置 {self.position} - 將使用：{first_valid}（共 {valid_count} 個有效字符）")
                    else:
                        self.setToolTip_(f"位置 {self.position} - 鎖定字符：{first_valid}")
                else:
                    self.setToolTip_(f"位置 {self.position}")
            else:
                valid_count = len(validation_result['valid_glyphs'])
                invalid_count = len(validation_result['invalid_chars'])
                if valid_count > 0:
                    first_valid = validation_result['valid_glyphs'][0]
                    self.setToolTip_(f"位置 {self.position} - 將使用：{first_valid}（{invalid_count} 個無效字符已標記）")
                else:
                    self.setToolTip_(f"位置 {self.position} - 發現 {invalid_count} 個無效字符")
                    
        except Exception:
            import traceback
            traceback.print_exc()
            # 發生錯誤時隱藏tooltip
            self.setToolTip_(None)
    
    def refresh_visual_feedback(self):
        """更新視覺標注（解耦架構要求的方法）
        
        Gemini Code Assist 建議：讓 UI 元件自行更新視覺回饋
        """
        try:
            current_text = self.stringValue()
            if current_text:
                from ..core.input_recognition import VisualFeedbackService
                VisualFeedbackService.apply_visual_feedback_to_text(self)
        except Exception:
            print(traceback.format_exc())
    
    def apply_visual_feedback_to_self(self):
        """套用視覺標注到自身（統一介面）"""
        self.refresh_visual_feedback()
    
    def setStringValue_(self, value):
        """覆寫系統方法，支援程式化更新後自動視覺標注"""
        try:
            # 呼叫父類方法設定值
            objc.super(LockCharacterField, self).setStringValue_(value or "")
            
            # 程式化更新後執行視覺標注（僅當不在程式化更新標記中）
            if not getattr(self, '_programmatic_update', False):
                try:
                    from ..core.input_recognition import VisualFeedbackService
                    VisualFeedbackService.apply_visual_feedback_to_text(self)
                except Exception:
                    print(traceback.format_exc())
            
        except Exception:
            print(traceback.format_exc())
    
    def _validate_event_handler(self, method_name):
        """統一的事件處理器驗證"""
        return (hasattr(self, 'plugin') and self.plugin and 
                hasattr(self.plugin, 'event_handler') and
                hasattr(self.plugin.event_handler, method_name))
    
    def menuForEvent_(self, event):
        """建立並返回鎖定輸入框右鍵選單（AppKit 標準方式）
        
        強化版本：確保在任何情況下都返回有效選單，永不返回 None
        """
        try:
            from ..core.menu_manager import MenuManager
            
            menu = MenuManager.create_text_field_menu(
                self, 
                include_glyph_picker=True, 
                include_tab_actions=False  # 鎖定輸入框不包含分頁操作
            )
            
            if menu is None:
                menu = self._create_emergency_menu()
            
            return menu
            
        except Exception:
            print(traceback.format_exc())
            return self._create_emergency_menu()
    
    def textView_menu_forEvent_atIndex_(self, textView, menu, event, charIndex):
        """使用系統方法：擴充預設選單而非替換"""
        from AppKit import NSMenuItem
        from ..localization import localize, localize_with_params
        
        # 使用系統提供的預設選單
        context_menu = menu 
        
        # 如果系統沒提供選單，獲取 textView 的預設選單
        if not context_menu:
            context_menu = textView.menu()
        
        # 在系統選單基礎上新增字符選擇器
        if context_menu:
            # 檢查是否已有字符選擇器
            has_glyph_picker = False
            for i in range(context_menu.numberOfItems()):
                item = context_menu.itemAtIndex_(i)
                if item.action() == "pickGlyphAction:":
                    has_glyph_picker = True
                    break
            
            if not has_glyph_picker:
                context_menu.addItem_(NSMenuItem.separatorItem())
                glyph_picker_item = NSMenuItem.alloc().initWithTitle_action_keyEquivalent_(
                    localize('menu_glyph_picker'),
                    "pickGlyphAction:",
                    ""
                )
                glyph_picker_item.setTarget_(self)
                context_menu.addItem_(glyph_picker_item)
        
        return context_menu
    
    def _create_emergency_menu(self):
        """建立緊急後備選單，確保永遠有可用的選單"""
        try:
            from AppKit import NSMenu, NSMenuItem
            
            emergency_menu = NSMenu.alloc().init()
            emergency_menu.setTitle_(localize('menu_lock_field_title'))
            
            # 手動建立字符選擇器項目
            glyph_picker_item = NSMenuItem.alloc().initWithTitle_action_keyEquivalent_(
                localize('menu_glyph_picker'), "pickGlyphAction:", ""
            )
            glyph_picker_item.setTarget_(self)
            emergency_menu.addItem_(glyph_picker_item)
            
            return emergency_menu
            
        except Exception:
            print(traceback.format_exc())
            # 最後的最後，返回一個空選單而不是 None
            from AppKit import NSMenu
            return NSMenu.alloc().init()
    
    def pickGlyphAction_(self, sender):
        """字符選擇器 action - 鎖定框特殊的單字符替換邏輯"""
        try:
            from ..core.menu_manager import MenuManager
            from ..core.glyphs_service import get_glyphs_service
            
            # 獲取選中的字符列表
            success, selected_glyphs = MenuManager.get_selected_glyphs()
            if success and selected_glyphs:
                # 鎖定框只使用第一個選中的字符
                first_glyph = selected_glyphs[0]
                glyph_name = first_glyph.name
                
                # 使用完全替換的方式設定字符名稱
                self.setStringValue_(glyph_name)
                
                # 觸發與手動編輯相同的完整邏輯鏈
                if self._validate_event_handler('handle_lock_field_change'):
                    self.plugin.event_handler.handle_lock_field_change(self, glyph_name)
                else:
                    pass
                
                # 顯示成功通知
                glyphs_service = get_glyphs_service()
                selected_count = len(selected_glyphs)
                if selected_count == 1:
                    glyphs_service.show_notification(
                        "九宮格預覽",
                        f"已設定字符：{glyph_name}"
                    )
                else:
                    glyphs_service.show_notification(
                        "九宮格預覽",
                        f"已設定字符：{glyph_name}（選擇了 {selected_count} 個，僅使用第一個）"
                        )
                        
        except Exception:
            print(traceback.format_exc())
    
    def rightMouseDown_(self, event):
        """處理右鍵按下事件 - 統一使用 menuForEvent_ 機制
        
        不再手動處理選單，統一委派給 AppKit 標準的 menuForEvent_ 機制。
        這確保聚焦和非聚焦狀態都使用相同的選單。
        """
        
        # 直接呼叫父類處理，讓 AppKit 呼叫我們的 menuForEvent_ 方法
        objc.super(LockCharacterField, self).rightMouseDown_(event)
    
    def controlTextDidBeginEditing_(self, notification):
        """開始編輯時的處理
        
        由於 NSKVONotifying_NSTextView 的 menuForEvent_ 屬性是唯讀的，
        無法進行動態替換。改為依賴 NSTextField 自身的 menuForEvent_ 實作。
        """
        try:
            # 由於 KVO 包裝物件的限制，不再嘗試動態替換 field editor 的 menuForEvent_
            # NSTextField 的 menuForEvent_ 方法會在適當時候被呼叫
            pass
                
        except Exception:
            print(traceback.format_exc())

    def dealloc(self):
        """解構式"""
        try:
            NSNotificationCenter.defaultCenter().removeObserver_(self)
        except Exception:
            try:
                print(traceback.format_exc())
            except:
                pass
        objc.super(LockCharacterField, self).dealloc()

class LockFieldsPanel(NSView):
    """鎖定欄位面板 - 基於原版設計，適配平面座標系統"""
    
    def initWithFrame_plugin_(self, frame, plugin):
        """初始化鎖定欄位面板 - 一次建立所有 UI 元件"""
        self = objc.super(LockFieldsPanel, self).initWithFrame_(frame)
        if self:
            self.plugin = plugin
            self.lockFields = {}
            self.lockButton = None
            self.clearAllButton = None
            
            self.isLockFieldsActive = getattr(plugin, 'isLockFieldsActive', True)
            
            # 一次建立所有 UI 元件
            self._create_static_ui_components()
            
            self.setAutoresizingMask_(NSViewWidthSizable | NSViewMaxYMargin)
            
        return self
    
    def _create_static_ui_components(self):
        """建立所有 UI 元件 - 一次性建立"""
        try:
            bounds = self.bounds()
            
            # 建立清除按鈕
            self._create_clear_button(bounds)
            
            # 建立九宮格佈局
            self._create_lock_grid(bounds)
            
        except Exception:
            print(traceback.format_exc())
    
    def _create_clear_button(self, bounds):
        """建立清除按鈕"""
        rect = NSMakeRect(0, 0, bounds.size.width, LOCK_FIELDS_CLEAR_BUTTON_HEIGHT)
        self.clearAllButton = NSButton.alloc().initWithFrame_(rect)
        self.clearAllButton.setAutoresizingMask_(NSViewWidthSizable | NSViewMaxYMargin)
        self.clearAllButton.setTitle_(localize('clear_all_locks'))
        self.clearAllButton.setTarget_(self)
        self.clearAllButton.setAction_("clearAllFields:")
        self.clearAllButton.setToolTip_(localize('tooltip_clear_all_locks'))
        self.addSubview_(self.clearAllButton)
    
    def _create_lock_grid(self, bounds):
        """建立九宮格佈局 - 基於平面座標系統 (0-8)"""
        grid_spacing = LOCK_FIELDS_INTERNAL_GRID_SPACING
        button_height = LOCK_FIELDS_CLEAR_BUTTON_HEIGHT
        spacing = LOCK_FIELDS_SPACING_ABOVE_BUTTON
        
        available_width = bounds.size.width
        
        # 佈局計算：高度固定，寬度自動適應
        cell_height = LOCK_FIELD_HEIGHT
        cell_width = (available_width - 2 * grid_spacing) / 3
        grid_start_x = 0
        current_y = button_height + spacing
        
        # 建立九宮格各位置 (0-8)
        # 0 1 2  (上排)
        # 3 4 5  (中排，4=中央)
        # 6 7 8  (下排)
        for row in range(3):
            for col in range(3):
                grid_position = row * 3 + col  # 平面座標 0-8
                x = grid_start_x + col * (cell_width + grid_spacing)
                y = current_y + (2 - row) * (cell_height + grid_spacing)  # 反轉Y軸
                
                if grid_position == CENTER_POSITION:  # 位置 4 = 中央鎖頭按鈕
                    self._create_lock_button(x, y, cell_width, cell_height)
                else:  # 位置 0,1,2,3,5,6,7,8 = 鎖定輸入框
                    self._create_lock_field(x, y, cell_width, cell_height, grid_position)
    
    def _update_layout_positions(self):
        """更新元件位置 - 不重建元件，只調整位置"""
        try:
            bounds = self.bounds()
            
            # 更新清除按鈕位置
            if self.clearAllButton:
                clear_rect = NSMakeRect(0, 0, bounds.size.width, LOCK_FIELDS_CLEAR_BUTTON_HEIGHT)
                self.clearAllButton.setFrame_(clear_rect)
            
            # 更新九宮格位置
            self._update_grid_positions(bounds)
            
        except Exception:
            print(traceback.format_exc())
    
    def _update_grid_positions(self, bounds):
        """更新九宮格位置"""
        grid_spacing = LOCK_FIELDS_INTERNAL_GRID_SPACING
        button_height = LOCK_FIELDS_CLEAR_BUTTON_HEIGHT
        spacing = LOCK_FIELDS_SPACING_ABOVE_BUTTON
        
        available_width = bounds.size.width
        cell_height = LOCK_FIELD_HEIGHT
        cell_width = (available_width - 2 * grid_spacing) / 3
        grid_start_x = 0
        current_y = button_height + spacing
        
        # 更新各位置元件的 frame
        for row in range(3):
            for col in range(3):
                grid_position = row * 3 + col
                x = grid_start_x + col * (cell_width + grid_spacing)
                y = current_y + (2 - row) * (cell_height + grid_spacing)
                
                if grid_position == CENTER_POSITION and self.lockButton:
                    button_padding = LOCK_BUTTON_PADDING
                    lock_rect = NSMakeRect(
                        x + button_padding, y + button_padding,
                        cell_width - 2 * button_padding, cell_height - 2 * button_padding
                    )
                    self.lockButton.setFrame_(lock_rect)
                elif grid_position in self.lockFields:
                    field_rect = NSMakeRect(x, y, cell_width, cell_height)
                    self.lockFields[grid_position].setFrame_(field_rect)
    
    def _create_lock_field(self, x, y, cell_width, cell_height, position):
        """建立單一鎖定輸入框"""
        try:
            fieldRect = NSMakeRect(x, y, cell_width, cell_height)
            lockField = LockCharacterField.alloc().initWithFrame_position_plugin_(
                fieldRect, position, self.plugin
            )
            
            # 設定 autoresizing mask（簡化版本）
            lockField.setAutoresizingMask_(0)  # 不自動調整
            
            self.lockFields[position] = lockField
            self.addSubview_(lockField)
            
        except Exception:
            print(traceback.format_exc())
    
    def _create_lock_button(self, x, y, width, height):
        """建立中央鎖頭按鈕"""
        try:
            button_padding = LOCK_BUTTON_PADDING
            lockRect = NSMakeRect(
                x + button_padding, y + button_padding, 
                width - 2 * button_padding, height - 2 * button_padding
            )
            
            self.lockButton = NSButton.alloc().initWithFrame_(lockRect)
            
            # 設定 autoresizing mask（簡化版本）
            self.lockButton.setAutoresizingMask_(0)  # 不自動調整
            
            self.lockButton.setTarget_(self)
            self.lockButton.setAction_("toggleLockMode:")
            
            # 基礎配置
            self.lockButton.setBezelStyle_(NSBezelStyleRegularSquare)
            self.lockButton.setButtonType_(NSButtonTypeToggle)
            self.lockButton.setBordered_(False)
            self.lockButton.setAlignment_(NSCenterTextAlignment)
            
            # 圓角樣式
            if hasattr(self.lockButton, 'setWantsLayer_'):
                self.lockButton.setWantsLayer_(True)
                if hasattr(self.lockButton, 'layer'):
                    layer = self.lockButton.layer()
                    if layer:
                        layer.setCornerRadius_(LOCK_BUTTON_CORNER_RADIUS)
                        layer.setShadowOpacity_(0)
            
            # 套用初始樣式
            self._apply_unified_lock_button_styling()
            self.addSubview_(self.lockButton)
            
        except Exception:
            print(traceback.format_exc())
    
    # =============================================================================
    # 統一的鎖頭按鈕管理方法
    # =============================================================================
    
    def update_lock_button_display(self):
        """統一的鎖頭按鈕顯示更新方法"""
        try:
            if not hasattr(self, 'lockButton') or not self.lockButton:
                return
            self._apply_unified_lock_button_styling()
        except Exception:
            print(traceback.format_exc())
    
    def _apply_unified_lock_button_styling(self):
        """統一的鎖頭按鈕樣式套用方法"""
        try:
            # 確定當前鎖定狀態
            is_locked = self.isLockFieldsActive
            
            # === 建立鎖頭圖示 ===
            imageSize = LOCK_IMAGE_SIZE
            lockImage = NSImage.alloc().initWithSize_((imageSize, imageSize))
            lockImage.lockFocus()
            
            # 清除背景並設定字體
            NSColor.clearColor().set()
            import AppKit
            AppKit.NSRectFill(((0, 0), (imageSize, imageSize)))
            
            fontSize = LOCK_IMAGE_FONT_SIZE
            font = NSFont.systemFontOfSize_(fontSize)
            attrs = {
                NSFontAttributeName: font, 
                NSForegroundColorAttributeName: NSColor.selectedControlTextColor()
            }
            
            # 選擇並居中繪製符號
            symbol = "🔒" if is_locked else "🔓"
            from Foundation import NSString
            string = NSString.stringWithString_(symbol)
            stringSize = string.sizeWithAttributes_(attrs)
            x = (imageSize - stringSize.width) / 2
            y = (imageSize - stringSize.height) / 2
            from AppKit import NSMakePoint
            string.drawAtPoint_withAttributes_(NSMakePoint(x, y), attrs)
            
            lockImage.unlockFocus()
            lockImage.setTemplate_(True)
            
            # === 配置按鈕顯示 ===
            self.lockButton.setImage_(lockImage)
            self.lockButton.setTitle_("")
            self.lockButton.setState_(1 if is_locked else 0)
            
            # === 套用色彩樣式 ===
            if is_locked:
                self.lockButton.setContentTintColor_(NSColor.selectedControlTextColor())
                self.lockButton.setBackgroundColor_(NSColor.selectedControlColor())
            else:
                self.lockButton.setContentTintColor_(NSColor.controlTextColor())
                self.lockButton.setBackgroundColor_(NSColor.controlColor())
            
            # === 工具提示設定 ===
            tooltip = localize('tooltip_toggle_to_unlock') if is_locked else localize('tooltip_toggle_to_lock')
            self.lockButton.setToolTip_(tooltip)
            
            # === 觸發重繪 ===
            # lockButton 是標準 NSButton，使用系統原生重繪方法
            self.lockButton.setNeedsDisplay_(True)
            
        except Exception:
            print(traceback.format_exc())
    
    def toggleLockMode_(self, sender):
        """切換鎖定欄位模式 - 減法重構：純粹的顯示狀態切換"""            
        # 純粹的狀態切換，不進行任何資料同步
        self.isLockFieldsActive = not self.isLockFieldsActive
        self.plugin.isLockFieldsActive = self.isLockFieldsActive
        
        self.update_lock_button_display()
        
        if self._validate_event_handler('update_lock_mode_display'):
            self.plugin.event_handler.update_lock_mode_display()
        
        if hasattr(self.plugin, 'savePreferences'):
            self.plugin.savePreferences()
    
    def clearAllFields_(self, sender):
        """清空所有鎖定輸入框 - 委派給事件處理器"""
        if hasattr(self, 'lockFields') and self.lockFields:
            for field in self.lockFields.values():
                field.setStringValue_("")
        
        if self._validate_event_handler('clear_locked_positions'):
            self.plugin.event_handler.clear_locked_positions()
    
    def updatePanelUI_(self, plugin):
        """更新 UI 狀態（平面架構版本）"""
        if not hasattr(plugin, 'lock_inputs'):
            plugin.lock_inputs = [''] * GRID_SIZE_TOTAL
        
        for position, field in self.lockFields.items():
            displayed_char = ""
            
            if position != CENTER_POSITION:
                displayed_char = plugin.lock_inputs[position]
            
            # 設定程式化更新標記，避免觸發視覺標注
            if hasattr(field, '_programmatic_update'):
                field._programmatic_update = True
            
            try:
                field.setStringValue_(displayed_char)
            finally:
                # 確保標記被清除
                if hasattr(field, '_programmatic_update'):
                    field._programmatic_update = False
                
                # 程式化更新完成後手動觸發視覺標注
                try:
                    from ..core.input_recognition import VisualFeedbackService
                    VisualFeedbackService.apply_visual_feedback_to_text(field)
                except Exception:
                    print(traceback.format_exc())
                    
    def set_lock_state(self, is_lock_active):
        """設定鎖定狀態"""
        self.isLockFieldsActive = is_lock_active
        self.update_lock_button_display()
    
    def setFrame_(self, frame):
        """設定 frame"""
        try:
            # 呼叫父類設定 frame
            objc.super(LockFieldsPanel, self).setFrame_(frame)
            
            # 更新元件位置（不重建元件）
            self._update_layout_positions()
            
        except Exception:
            print(traceback.format_exc())
    
    def _validate_event_handler(self, method_name):
        """統一的事件處理器驗證"""
        return (hasattr(self.plugin, 'event_handler') and self.plugin.event_handler and
                hasattr(self.plugin.event_handler, method_name))
    
    def dealloc(self):
        """解構式"""
        try:
            for field in self.lockFields.values():
                if hasattr(field, 'dealloc'):
                    field.dealloc()
        except:
            pass
        objc.super(LockFieldsPanel, self).dealloc()