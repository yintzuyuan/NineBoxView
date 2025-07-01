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
    NSCenterTextAlignment,
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
            # self._setup_context_menu()
            self._register_notifications()
        return self
    
    def _setup_appearance(self):
        """設定外觀"""
        self.setFont_(NSFont.systemFontOfSize_(16.0))
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
    
    # def _setup_context_menu(self):
    #     """設定右鍵選單"""
    #     try:
    #         contextMenu = NSMenu.alloc().init()
            
    #         pickGlyphItem = NSMenuItem.alloc().initWithTitle_action_keyEquivalent_(
    #             Glyphs.localize({
    #                 'en': u'Select Glyphs from Font...',
    #                 'zh-Hant': u'從字型中選擇字符...',
    #                 'zh-Hans': u'从字体中选择字符...',
    #                 'ja': u'フォントから文字を選択...',
    #                 'ko': u'글꼴에서 글자 선택...',
    #             }),
    #             "pickGlyphAction:",
    #             ""
    #         )
    #         contextMenu.addItem_(pickGlyphItem)
    #         self.setMenu_(contextMenu)
            
    #     except Exception as e:
    #         error_log("設定右鍵選單錯誤", e)
    
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
        # 功能暫未實作
    
    def textDidChange_(self, notification):
        """文字變更時的智慧回呼"""
        try:
            debug_log(f"鎖定欄位 {self.position} 文字變更: {self.stringValue()}")
            if hasattr(self, 'plugin') and self.plugin:
                self.plugin.smartLockCharacterCallback(self)
        except Exception as e:
            error_log("智慧鎖定字符處理錯誤", e)
    
    def dealloc(self):
        """解構式"""
        NSNotificationCenter.defaultCenter().removeObserver_(self)
        objc.super(LockCharacterField, self).dealloc()


class LockFieldsPanel(NSView):
    """鎖定欄位面板畫面"""
    
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
        
        # 建立清除按鈕（底部）
        self._create_clear_button(bounds)
        
        # 建立鎖定輸入框九宮格（上方）
        self._create_lock_fields(bounds)
    
    def _create_lock_fields(self, bounds):
        """建立鎖定輸入框和鎖頭按鈕"""
        grid_spacing = 4
        button_height = 22
        spacing = 8
        
        # 計算每個輸入框的寬度
        available_width = bounds.size.width
        cell_width = (available_width - 2 * grid_spacing) / 3
        cell_height = min(cell_width, self.LOCK_FIELD_HEIGHT)
        
        # 從頂部開始（清除按鈕上方）
        current_y = button_height + spacing
        
        # 建立3x3網格，8個鎖定框 + 1個中央鎖頭按鈕
        # 九宮格位置映射：0,1,2,3,4,5,6,7,8 → 鎖定框映射：0,1,2,3,skip,5,6,7,8
        for row in range(3):
            for col in range(3):
                # 計算九宮格位置索引（0-8）
                grid_position = row * 3 + col
                
                # 計算每個單元格的位置（從底部向上）
                x = col * (cell_width + grid_spacing)
                y = current_y + (2 - row) * (cell_height + grid_spacing)
                
                if grid_position == 4:  # 中央位置（九宮格位置4）：放置鎖頭按鈕
                    self._create_lock_button(x, y, cell_width, cell_height)
                else:
                    # 其他位置：鎖定輸入框，使用九宮格位置作為 lockField 的鍵
                    fieldRect = NSMakeRect(x, y, cell_width, cell_height)
                    lockField = LockCharacterField.alloc().initWithFrame_position_plugin_(
                        fieldRect, grid_position, self.plugin
                    )
                    lockField.setAutoresizingMask_(NSViewWidthSizable | NSViewMaxYMargin)
                    lockField.setFont_(NSFont.systemFontOfSize_(16.0))
                    
                    # 使用九宮格位置索引 (0,1,2,3,5,6,7,8) 作為鍵
                    self.lockFields[grid_position] = lockField
                    self.addSubview_(lockField)
                    debug_log(f"創建鎖定框：九宮格位置 {grid_position}")
    
    def _create_lock_button(self, x, y, width, height):
        """建立鎖頭按鈕"""
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
        
        # 設定字型與對齊
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
        """建立清除按鈕"""
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
        """切換鎖頭模式（鎖定模式切換使用細粒度更新）"""
        try:
            # 先儲存目前狀態
            was_in_clear_mode = self.isInClearMode
            
            # 檢查必要的物件和方法
            if not hasattr(self.plugin, 'event_handlers'):
                debug_log("警告：event_handlers 未初始化")
                return
            
            debug_log(f"[鎖頭切換] 從 {'🔓 解鎖' if was_in_clear_mode else '🔒 上鎖'} 模式開始切換")
            
            # === 從解鎖切換到上鎖時，儲存目前的隨機排列 ===
            if was_in_clear_mode and hasattr(self.plugin, 'currentArrangement'):
                # 儲存目前的隨機排列，供之後回復使用
                self.plugin.originalArrangement = list(self.plugin.currentArrangement)
                debug_log(f"[鎖頭切換] 儲存原始隨機排列: {self.plugin.originalArrangement}")
            
            # 從解鎖切換到上鎖時同步輸入框內容到 lockedChars
            if was_in_clear_mode:
                debug_log("[鎖頭切換] 從🔓解鎖切換到🔒鎖定：同步鎖定字符")
                self._sync_input_fields_to_locked_chars_without_regenerate()
            
            # 更新狀態
            self.isInClearMode = not self.isInClearMode
            debug_log(f"[鎖頭切換] 鎖頭模式切換完成：{'🔓 解鎖' if self.isInClearMode else '🔒 上鎖'}")
            
            # 更新 UI
            self.updateLockButton()
            
            # 同步到 plugin 對象
            if hasattr(self, 'plugin') and self.plugin:
                # 更新 plugin 的狀態
                self.plugin.isInClearMode = self.isInClearMode
                debug_log(f"[鎖頭切換] 已同步鎖頭狀態到 plugin.isInClearMode = {self.isInClearMode}")
                
                # === 使用細粒度更新，只影響鎖定格顯示，保持其他位置不變 ===
                debug_log("[鎖頭切換] 使用細粒度鎖定模式更新，保持其他位置穩定")
                self.plugin.event_handlers.update_lock_mode_display()
                
                # 儲存偏好設定
                self.plugin.savePreferences()
                debug_log("[鎖頭切換] 已儲存鎖頭狀態到偏好設定")
            
        except Exception as e:
            error_log("切換鎖頭模式錯誤", e)
            if hasattr(self, 'lockButton'):
                self.updateLockButton()

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
        """建立極簡鎖頭圖示"""
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
            
            debug_log(f"已建立極簡{'鎖定' if locked else '解鎖'}圖示")
            
        except Exception as e:
            error_log("建立極簡鎖頭圖示時發生錯誤", e)
            
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
                
                # 設定背景色（如果有 layer）
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
                
                # 設定圖示顏色
                if hasattr(self.lockButton, 'setContentTintColor_'):
                    if is_locked:
                        self.lockButton.setContentTintColor_(NSColor.controlAccentColor())
                    else:
                        if isDarkMode:
                            self.lockButton.setContentTintColor_(NSColor.secondaryLabelColor())
                        else:
                            self.lockButton.setContentTintColor_(NSColor.labelColor())
                
                # 設定工具提示
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
                debug_log("圖示建立失敗，使用極簡文字後備方案")
                
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
        """清空所有鎖定輸入框（細粒度清除並觸發主視窗重繪）"""
        try:
            debug_log("清空所有欄位按鈕被點擊")
            
            # 清空所有鎖定輸入框的顯示
            if hasattr(self, 'lockFields') and self.lockFields:
                for field in self.lockFields.values():
                    field.setStringValue_("")

            # 細粒度清除鎖定狀態並觸發主視窗重繪
            if hasattr(self, 'plugin') and self.plugin:
                # 備份目前狀態（如果需要）
                if hasattr(self.plugin, 'previousLockedChars'):
                    self.plugin.previousLockedChars = getattr(self.plugin, 'lockedChars', {}).copy()
                
                # 細粒度清除（會自動清空 lockedChars 並恢復排列）
                if hasattr(self.plugin, 'event_handlers'):
                    debug_log("使用細粒度清除鎖定位置，保持其他位置穩定並觸發主視窗重繪")
                    self.plugin.event_handlers.clear_locked_positions()
                
                # 儲存偏好設定
                self.plugin.savePreferences()
            
            debug_log("完成清空所有輸入框（細粒度清除+主視窗重繪）")
            
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
        """解構式"""
        objc.super(LockFieldsPanel, self).dealloc()
