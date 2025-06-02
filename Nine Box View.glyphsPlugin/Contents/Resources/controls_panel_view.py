# encoding: utf-8
"""
九宮格預覽外掛 - 控制面板視圖（優化版）
Nine Box Preview Plugin - Controls Panel View (Optimized)
"""

from __future__ import division, print_function, unicode_literals
import traceback
import objc
from GlyphsApp import Glyphs
from AppKit import (
    NSView, NSColor, NSRectFill, NSBezierPath, NSFont, 
    NSTextField, NSButton, NSBezelStyleRounded,
    NSButtonTypeMomentaryPushIn, NSButtonTypeToggle,
    NSCenterTextAlignment, NSFocusRingTypeNone,
    NSNotificationCenter, NSMenu, NSMenuItem,
    NSApp, NSViewWidthSizable, NSViewHeightSizable,
    NSViewMinYMargin, NSViewMaxYMargin, NSMakeRect,
    NSUserDefaultsDidChangeNotification, NSImage,
    NSFontAttributeName, NSForegroundColorAttributeName,
    NSString, NSMakePoint, NSCompositingOperationSourceOver,
    NSBezelStyleRegularSquare
)
from Foundation import NSObject
try:
    # 導入 Quartz 以正確處理 CGColor
    from Quartz import CGColorCreateGenericRGB
except ImportError:
    CGColorCreateGenericRGB = None

from constants import DEBUG_MODE, MAX_LOCKED_POSITIONS
from utils import debug_log, get_cached_glyph


class BaseTextField(NSTextField):
    """基礎文本框類別（優化版）"""
    
    def setupWithPlugin_(self, plugin):
        """基礎設定"""
        self.plugin = plugin
        self._setup_context_menu()
        self._register_notifications()
        return self
    
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
            debug_log(f"設定右鍵選單錯誤: {e}")
    
    def _register_notifications(self):
        """註冊通知"""
        NSNotificationCenter.defaultCenter().addObserver_selector_name_object_(
            self,
            "textDidChange:",
            "NSControlTextDidChangeNotification",
            self
        )
    
    def pickGlyphAction_(self, sender):
        """選擇字符功能（階段1.2：僅記錄）"""
        debug_log("[階段1.2] 選擇字符選單被點擊")
        # === 階段1.2：功能暫未實現 ===
        # if hasattr(self, 'plugin') and self.plugin:
        #     self.plugin.pickGlyphCallback(sender)
    
    def dealloc(self):
        """析構函數"""
        NSNotificationCenter.defaultCenter().removeObserver_(self)
        objc.super(BaseTextField, self).dealloc()


class CustomTextField(BaseTextField):
    """支援右鍵選單的文本框類別（優化版）"""
    
    def initWithFrame_plugin_(self, frame, plugin):
        """初始化文本框"""
        self = objc.super(CustomTextField, self).initWithFrame_(frame)
        if self:
            self.setupWithPlugin_(plugin)
        return self
    
    def textDidChange_(self, notification):
        """文本變更時的回調（階段2.1：啟用搜尋功能）"""
        try:
            debug_log(f"[階段2.1] 搜尋欄位文本變更: {self.stringValue()}")
            # === 階段2.1：啟用搜尋欄位功能 ===
            if hasattr(self, 'plugin') and self.plugin:
                self.plugin.searchFieldCallback(self)
        except Exception as e:
            debug_log(f"[階段2.1] 文本變更處理錯誤: {e}")


class LockCharacterField(BaseTextField):
    """單字符鎖定輸入框類別（優化版）"""
    
    def initWithFrame_position_plugin_(self, frame, position, plugin):
        """初始化單字符輸入框"""
        self = objc.super(LockCharacterField, self).initWithFrame_(frame)
        if self:
            self.position = position
            self.setupWithPlugin_(plugin)
            self._setup_appearance()
        return self
    
    def _setup_appearance(self):
        """設定外觀"""
        # 使用較大的字體，提高可讀性
        self.setFont_(NSFont.systemFontOfSize_(14.0))
        self.setFocusRingType_(NSFocusRingTypeNone)
        self.setBezeled_(True)
        self.setEditable_(True)
        self.setUsesSingleLineMode_(True)
        self.setAlignment_(NSCenterTextAlignment)
        
        # 使用更符合 macOS 標準的輸入框顏色
        isDarkMode = NSApp.effectiveAppearance().name().containsString_("Dark")
        if isDarkMode:
            # 深色模式使用系統文字輸入框背景色
            self.setBackgroundColor_(NSColor.textBackgroundColor())
        else:
            # 亮色模式使用純白色，符合 macOS 標準輸入框外觀
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
    
    def textDidChange_(self, notification):
        """文本變更時的智能回調（階段2.2：資料處理）"""
        try:
            debug_log(f"[階段2.2] 鎖定欄位 {self.position} 文本變更: {self.stringValue()}")
            # === 階段2.2：啟用智能鎖定字符功能 ===
            if hasattr(self, 'plugin') and self.plugin:
                self.plugin.smartLockCharacterCallback(self)
        except Exception as e:
            debug_log(f"[階段2.2] 智能鎖定字符處理錯誤: {e}")


class ControlsPanelView(NSView):
    """
    控制面板視圖類別（優化版）
    Controls Panel View class (Optimized)
    """
    
    def initWithFrame_plugin_(self, frame, plugin):
        """初始化控制面板視圖（階段1.3：基礎版）"""
        try:
            self = objc.super(ControlsPanelView, self).initWithFrame_(frame)
            if self:
                self.plugin = plugin
                self.lockFields = {}
                self.isInClearMode = False  # True=解鎖，False=上鎖（預設為上鎖）
                
                # UI 元件快取
                self._ui_components = {}
                
                # 設定視圖屬性
                self.setAutoresizingMask_(NSViewWidthSizable | NSViewHeightSizable)
                
                # 創建UI元件
                self.setupUI()
                
                # 監聽主題變更
                NSNotificationCenter.defaultCenter().addObserver_selector_name_object_(
                    self,
                    "themeChanged:",
                    NSUserDefaultsDidChangeNotification,
                    None
                )
                
                debug_log("[階段1.3] 控制面板視圖初始化完成")
                
            return self
        except Exception as e:
            print(f"[階段1.3] 初始化控制面板視圖錯誤: {e}")
            if DEBUG_MODE:
                print(traceback.format_exc())
            return None
    
    def _create_search_field(self, bounds):
        """創建搜尋欄位（動態高度）"""
        margin = 10  # 邊距
        spacing = 12  # 間距
        min_search_height = 50  # 最小高度
        
        # 預留給底部元素的固定高度
        # 九宮格高度 + 清除按鈕高度 + 間距
        bottom_reserved_height = (3 * 40 + 2 * 4) + 22 + spacing * 3
        
        # 計算搜尋欄可用的高度（動態適應）
        available_height = bounds.size.height - margin * 2 - bottom_reserved_height
        search_height = max(available_height, min_search_height)  # 確保最小高度
        
        # 固定在頂部位置
        searchRect = NSMakeRect(margin, bounds.size.height - margin - search_height, 
                                bounds.size.width - 2 * margin, search_height)
        
        searchField = CustomTextField.alloc().initWithFrame_plugin_(searchRect, self.plugin)
        searchField.setAutoresizingMask_(NSViewWidthSizable | NSViewHeightSizable)  # 允許高度調整
        searchField.setFont_(NSFont.systemFontOfSize_(14.0))
        searchField.setFocusRingType_(NSFocusRingTypeNone)
        searchField.setBezeled_(True)
        searchField.setEditable_(True)
        
        # 設定符合 macOS 標準的背景顏色
        isDarkMode = NSApp.effectiveAppearance().name().containsString_("Dark")
        if isDarkMode:
            # 深色模式使用系統文字輸入框背景色
            searchField.setBackgroundColor_(NSColor.textBackgroundColor())
        else:
            # 亮色模式使用純白色，符合 macOS 標準輸入框外觀
            searchField.setBackgroundColor_(NSColor.whiteColor())
        
        # 設定提示文字
        searchPlaceholder = Glyphs.localize({
            'en': u'Enter characters or Nice Names...',
            'zh-Hant': u'輸入字符或 Nice Names...',
            'zh-Hans': u'输入字符或 Nice Names...',
            'ja': u'文字または Nice Names を入力...',
            'ko': u'문자 또는 Nice Names 입력...',
        })
        searchField.setPlaceholderString_(searchPlaceholder)
        
        # 設定提示
        searchTooltip = Glyphs.localize({
            'en': u'Enter multiple characters or Nice Names separated by spaces',
            'zh-Hant': u'輸入多個字符或以空格分隔的 Nice Names',
            'zh-Hans': u'输入多个字符或以空格分隔的 Nice Names',
            'ja': u'複数の文字またはスペースで区切られた Nice Names を入力',
            'ko': u'여러 문자 또는 공백으로 구분된 Nice Names 입력',
        })
        searchField.setToolTip_(searchTooltip)
        
        self.searchField = searchField
        self._ui_components['searchField'] = searchField
        self.addSubview_(searchField)
        
        # 不返回下一個元素的垂直位置，因為布局已改變
        return search_height + margin
    
    def _create_buttons(self, bounds, current_y):
        """創建按鈕區域"""
        margin = 10
        spacing = 8
        button_height = 30
        
        # === UI調整：隱藏隨機排列按鈕 ===
        # 隨機排列按鈕（隱藏）
        # current_y -= button_height
        # randomizeRect = NSMakeRect(margin, current_y, bounds.size.width - 2 * margin, button_height)
        # randomizeButton = self._create_button(
        #     randomizeRect,
        #     Glyphs.localize({
        #         'en': u'Randomize',
        #         'zh-Hant': u'隨機排列',
        #         'zh-Hans': u'随机排列',
        #         'ja': u'ランダム配置',
        #         'ko': u'무작위 배치',
        #     }),
        #     self,  # 階段1.2：使用self作為target
        #     "randomizeStub:",  # 階段1.2：使用存根方法
        #     Glyphs.localize({
        #         'en': u'Generate a new random arrangement',
        #         'zh-Hant': u'產生新的隨機排列',
        #         'zh-Hans': u'生成新的随机排列',
        #         'ja': u'新しいランダム配置を生成',
        #         'ko': u'새로운 무작위 배치 생성',
        #     })
        # )
        # self.randomizeButton = randomizeButton
        # self._ui_components['randomizeButton'] = randomizeButton
        # self.addSubview_(randomizeButton)
        
        # 鎖頭按鈕將在 _create_lock_fields 中創建（在九宮格中央）
        
        # === UI調整：由於隱藏了隨機排列按鈕，不需要額外間距 ===
        return current_y
    
    def _create_button(self, rect, title, target, action, tooltip):
        """創建單個按鈕的輔助方法"""
        button = NSButton.alloc().initWithFrame_(rect)
        button.setAutoresizingMask_(NSViewWidthSizable | NSViewMaxYMargin)
        button.setTitle_(title)
        button.setTarget_(target)
        button.setAction_(action)
        button.setBezelStyle_(NSBezelStyleRounded)
        button.setButtonType_(NSButtonTypeMomentaryPushIn)
        button.setToolTip_(tooltip)
        return button
    
    def _create_lock_fields(self, bounds, current_y):
        """創建鎖定輸入框和鎖頭按鈕（固定在底部）"""
        margin = 10
        grid_spacing = 4
        spacing = 8  # 定義 spacing 變數
        
        # 計算每個輸入框的寬度
        available_width = bounds.size.width - 2 * margin
        cell_width = (available_width - 2 * grid_spacing) / 3
        cell_height = min(cell_width, 40)
        
        # 創建3x3網格
        position = 0
        for row in range(3):
            for col in range(3):
                # 計算每個單元格的位置（從底部向上）
                x = margin + col * (cell_width + grid_spacing)
                y = current_y + (2 - row) * (cell_height + grid_spacing)
                
                if row == 1 and col == 1:  # 中央位置：放置鎖頭按鈕
                    button_padding = 1
                    lockRect = NSMakeRect(
                        x + button_padding, 
                        y + button_padding, 
                        cell_width - 2 * button_padding, 
                        cell_height - 2 * button_padding
                    )
                    
                    lockButton = NSButton.alloc().initWithFrame_(lockRect)
                    lockButton.setAutoresizingMask_(NSViewWidthSizable | NSViewMaxYMargin)
                    lockButton.setTarget_(self)
                    lockButton.setAction_("toggleLockMode:")
                    
                    # 使用極簡按鈕樣式
                    lockButton.setBezelStyle_(NSBezelStyleRegularSquare)
                    lockButton.setButtonType_(NSButtonTypeToggle)
                    lockButton.setBordered_(False)  # 無邊框更簡潔
                    
                    # 設定字體與對齊
                    lockButton.setFont_(NSFont.systemFontOfSize_(14.0))
                    lockButton.setAlignment_(NSCenterTextAlignment)
                    
                    # 設定Layer屬性
                    if hasattr(lockButton, 'setWantsLayer_'):
                        lockButton.setWantsLayer_(True)
                        if hasattr(lockButton, 'layer'):
                            layer = lockButton.layer()
                            if layer:
                                # 輕微的圓角
                                layer.setCornerRadius_(4.0)
                                # 移除陰影效果
                                layer.setShadowOpacity_(0)
                    
                    self.lockButton = lockButton
                    self._ui_components['lockButton'] = lockButton
                    self.updateLockButton()
                    self.addSubview_(lockButton)
                else:
                    # 其他位置：鎖定輸入框
                    fieldRect = NSMakeRect(x, y, cell_width, cell_height)
                    lockField = LockCharacterField.alloc().initWithFrame_position_plugin_(
                        fieldRect, position, self.plugin
                    )
                    lockField.setAutoresizingMask_(NSViewWidthSizable | NSViewMaxYMargin)
                    lockField.setFont_(NSFont.systemFontOfSize_(14.0))
                    
                    self.lockFields[position] = lockField
                    self.addSubview_(lockField)
                    position += 1
        
        # 返回鎖定輸入框區域高度，用於後續布局
        grid_container_height = 3 * cell_height + 2 * grid_spacing
        return current_y + grid_container_height + spacing
    
    def _create_control_buttons(self, bounds, bottom_margin):
        """創建控制按鈕（固定在底部）"""
        margin = 10
        button_height = 22
        
        # 清空欄位按鈕，固定在底部
        clearAllRect = NSMakeRect(margin, bottom_margin, bounds.size.width - 2 * margin, button_height)
        clearAllButton = NSButton.alloc().initWithFrame_(clearAllRect)
        clearAllButton.setAutoresizingMask_(NSViewWidthSizable | NSViewMaxYMargin)
        
        # 極簡標題
        clearButtonTitle = Glyphs.localize({
            'en': u'Clear All',
            'zh-Hant': u'清空全部',
            'zh-Hans': u'清空全部',
            'ja': u'すべてクリア',
            'ko': u'모두 지우기',
        })
        
        clearAllButton.setTitle_(clearButtonTitle)
        clearAllButton.setTarget_(self)
        clearAllButton.setAction_("clearAllFields:")
        clearAllButton.setBezelStyle_(NSBezelStyleRounded)
        clearAllButton.setButtonType_(NSButtonTypeMomentaryPushIn)
        clearAllButton.setFont_(NSFont.systemFontOfSize_(12.0))
        
        # 確保按鈕在亮色模式下有正確的顏色
        isDarkMode = NSApp.effectiveAppearance().name().containsString_("Dark")
        if hasattr(clearAllButton, 'setContentTintColor_'):
            if isDarkMode:
                clearAllButton.setContentTintColor_(NSColor.controlTextColor())
            else:
                clearAllButton.setContentTintColor_(NSColor.controlTextColor())
        
        # 設定提示文字
        clearTooltip = Glyphs.localize({
            'en': u'Clear all lock fields',
            'zh-Hant': u'清空所有鎖定欄位',
            'zh-Hans': u'清空所有锁定栏位',
            'ja': u'すべてのロックフィールドをクリア',
            'ko': u'모든 잠금 필드 지우기',
        })
        clearAllButton.setToolTip_(clearTooltip)
        
        self.clearAllButton = clearAllButton
        self._ui_components['clearAllButton'] = clearAllButton
        self.addSubview_(clearAllButton)
        
        return button_height + bottom_margin
    
    def setFrame_(self, frame):
        """覆寫 setFrame_ 方法（階段1.3：新增）"""
        # 記錄舊框架
        oldFrame = self.frame()
        
        # 呼叫父類方法
        objc.super(ControlsPanelView, self).setFrame_(frame)
        
        # 如果框架大小改變，重新佈局 UI
        if (oldFrame.size.width != frame.size.width or 
            oldFrame.size.height != frame.size.height):
            debug_log(f"[階段1.3] 控制面板框架變更：{oldFrame.size.width}x{oldFrame.size.height} -> {frame.size.width}x{frame.size.height}")
            
            # 重新佈局 UI（不重建）
            self.layoutUI()
            
            # 觸發重繪
            self.setNeedsDisplay_(True)
    
    def setupUI(self):
        """設定使用者介面元件（固定底部元素）"""
        try:
            # 清除現有子視圖
            for subview in self.subviews():
                subview.removeFromSuperview()
            
            # 清除參照
            self.lockFields = {}
            self._ui_components = {}
            
            # 獲取視圖尺寸
            bounds = self.bounds()
            
            # 先創建頂部的搜尋欄位
            search_height = self._create_search_field(bounds)
            
            # 從底部開始計算底部元素的位置
            margin = 10
            spacing = 8
            button_height = 22
            
            # 先創建底部的清除按鈕（固定在最底部）
            self._create_control_buttons(bounds, margin)
            
            # 然後創建鎖定輸入框（在清除按鈕上方）
            lock_fields_start_y = margin + button_height + spacing
            self._create_lock_fields(bounds, lock_fields_start_y)
            
            # 更新內容
            self._update_content()
            
        except Exception as e:
            print(f"設定UI時發生錯誤: {e}")
            if DEBUG_MODE:
                print(traceback.format_exc())
    
    def layoutUI(self):
        """重新佈局 UI 元件（固定底部元素）"""
        try:
            bounds = self.bounds()
            margin = 10
            spacing = 8
            button_height = 22
            
            # 預留給底部元素的固定高度
            # 九宮格高度 + 清除按鈕高度 + 間距
            bottom_reserved_height = (3 * 40 + 2 * 4) + button_height + spacing * 3
            
            # 1. 調整搜尋欄位位置（頂部，動態高度）
            if hasattr(self, 'searchField'):
                # 計算搜尋欄可用的高度（動態適應）
                min_search_height = 50
                available_height = bounds.size.height - margin * 2 - bottom_reserved_height
                search_height = max(available_height, min_search_height)  # 確保最小高度
                
                searchRect = NSMakeRect(margin, bounds.size.height - margin - search_height, 
                                       bounds.size.width - 2 * margin, search_height)
                self.searchField.setFrame_(searchRect)
            
            # 2. 調整底部清除按鈕位置（固定在最底部）
            if hasattr(self, 'clearAllButton'):
                buttonRect = NSMakeRect(margin, margin, bounds.size.width - 2 * margin, button_height)
                self.clearAllButton.setFrame_(buttonRect)
            
            # 3. 調整鎖定輸入框位置（固定在底部，清除按鈕上方）
            if hasattr(self, 'lockFields') and self.lockFields:
                # 起始垂直位置（清除按鈕上方）
                current_y = margin + button_height + spacing
                
                # 計算每個輸入框的寬度
                available_width = bounds.size.width - 2 * margin
                grid_spacing = 4
                cell_width = (available_width - 2 * grid_spacing) / 3
                cell_height = min(cell_width, 40)
                
                # 創建3x3網格
                position = 0
                for row in range(3):
                    for col in range(3):
                        # 計算每個單元格的位置（從底部向上）
                        x = margin + col * (cell_width + grid_spacing)
                        y = current_y + (2 - row) * (cell_height + grid_spacing)
                        
                        if row == 1 and col == 1:  # 中央位置：鎖頭按鈕
                            if hasattr(self, 'lockButton'):
                                button_padding = 1
                                lockRect = NSMakeRect(
                                    x + button_padding, 
                                    y + button_padding, 
                                    cell_width - 2 * button_padding, 
                                    cell_height - 2 * button_padding
                                )
                                self.lockButton.setFrame_(lockRect)
                        else:
                            # 其他位置：鎖定輸入框
                            if position in self.lockFields:
                                fieldRect = NSMakeRect(x, y, cell_width, cell_height)
                                self.lockFields[position].setFrame_(fieldRect)
                            position += 1
            
            debug_log(f"[階段1.3] 完成 UI 佈局調整")
            
        except Exception as e:
            debug_log(f"[階段1.3] 重新佈局 UI 錯誤: {e}")
            if DEBUG_MODE:
                print(traceback.format_exc())
    
    def _update_content(self):
        """更新UI內容"""
        # 更新搜尋欄位
        if hasattr(self.plugin, 'lastInput') and self.plugin.lastInput:
            self.searchField.setStringValue_(self.plugin.lastInput)
        
        # 更新鎖定輸入框
        if hasattr(self.plugin, 'lockedChars') and self.plugin.lockedChars:
            for position, char_or_name in self.plugin.lockedChars.items():
                if position in self.lockFields:
                    self.lockFields[position].setStringValue_(char_or_name)
    
    def toggleLockMode_(self, sender):
        """切換鎖頭模式（極簡版）"""
        try:
            # 記錄之前的狀態
            was_in_clear_mode = self.isInClearMode
            
            # 切換狀態
            self.isInClearMode = not self.isInClearMode
            
            # 立即更新按鈕外觀
            self.updateLockButton()
            
            debug_log(f"[3.1] 鎖頭模式切換：{'🔓 解鎖' if self.isInClearMode else '🔒 上鎖'}")
            
            # === 修正：從解鎖切換到鎖定時，同步所有輸入欄內容到 plugin.lockedChars ===
            if was_in_clear_mode and not self.isInClearMode:
                # 從解鎖狀態切換到鎖定狀態：讀取並同步所有輸入欄內容
                debug_log("[3.1] 從🔓解鎖切換到🔒鎖定：同步輸入欄內容到 lockedChars")
                self._sync_input_fields_to_locked_chars()
            
            # === 階段 3.1：立即重繪預覽 ===
            if hasattr(self, 'plugin') and self.plugin:
                # 重新生成排列（會根據鎖定狀態決定是否應用 lockedChars）
                self.plugin.generateNewArrangement()
                # 觸發預覽更新
                self.plugin.updateInterface(None)
            
        except Exception as e:
            debug_log(f"[3.1] 切換鎖頭模式錯誤: {e}")
            # 確保狀態一致性
            if hasattr(self, 'lockButton'):
                self.updateLockButton()
    
    def _sync_input_fields_to_locked_chars(self):
        """同步輸入欄內容到 plugin.lockedChars"""
        try:
            if not hasattr(self, 'plugin') or not self.plugin:
                debug_log("警告：無法取得 plugin 實例")
                return
            
            if not hasattr(self.plugin, 'lockedChars'):
                self.plugin.lockedChars = {}
            
            # 清除現有的 lockedChars（確保完全同步）
            self.plugin.lockedChars.clear()
            
            # 遍歷所有鎖定輸入欄
            for position, field in self.lockFields.items():
                input_text = field.stringValue().strip()
                if input_text:
                    # 使用與 smartLockCharacterCallback 相同的辨識邏輯
                    recognized_char = self.plugin._recognize_character(input_text)
                    if recognized_char:
                        self.plugin.lockedChars[position] = recognized_char
                        debug_log(f"[同步] 位置 {position}: '{input_text}' → '{recognized_char}'")
                else:
                    # 空輸入則不設定鎖定
                    debug_log(f"[同步] 位置 {position}: 空輸入，不設定鎖定")
            
            # 儲存偏好設定
            if hasattr(self.plugin, 'savePreferences'):
                self.plugin.savePreferences()
                debug_log(f"[同步] 已儲存 {len(self.plugin.lockedChars)} 個鎖定字符到偏好設定")
            
        except Exception as e:
            debug_log(f"同步輸入欄內容錯誤: {e}")
            import traceback
            debug_log(traceback.format_exc())
    
    def createLockImage(self, locked=True):
        """
        創建極簡鎖頭圖示，符合Glyphs設計風格
        
        Args:
            locked: 是否為鎖定狀態
            
        Returns:
            NSImage: 極簡風格的鎖頭圖示
        """
        # 設定圖像大小
        imageSize = 18  # 稍小一點更符合Glyphs的風格
        
        # 創建空白圖像
        lockImage = NSImage.alloc().initWithSize_((imageSize, imageSize))
        
        # 開始編輯圖像
        lockImage.lockFocus()
        
        try:
            # 清除背景 (透明)
            NSColor.clearColor().set()
            NSBezierPath.fillRect_(((0, 0), (imageSize, imageSize)))
            
            # 設定文字屬性 - 使用系統字體
            fontSize = 13.0  # 稍小一點的字體更符合Glyphs風格
            font = NSFont.systemFontOfSize_(fontSize)
            
            # 使用系統控制文字顏色 - 完全符合Glyphs的顏色方案
            attrs = {
                NSFontAttributeName: font, 
                NSForegroundColorAttributeName: NSColor.controlTextColor()
            }
            
            # 使用標準Unicode符號 - 保持簡潔
            symbol = "🔒" if locked else "🔓"
            
            # 創建文字並計算尺寸
            string = NSString.stringWithString_(symbol)
            stringSize = string.sizeWithAttributes_(attrs)
            
            # 計算居中位置
            x = (imageSize - stringSize.width) / 2
            y = (imageSize - stringSize.height) / 2
            
            # 繪製符號
            string.drawAtPoint_withAttributes_(NSMakePoint(x, y), attrs)
            
            debug_log(f"已創建極簡{'鎖定' if locked else '解鎖'}圖示")
            
        except Exception as e:
            debug_log(f"創建極簡鎖頭圖示時發生錯誤: {e}")
            
            # 嘗試使用系統提供的圖示
            try:
                # 在macOS上嘗試使用系統提供的圖示
                systemIcon = None
                
                if locked:
                    systemIcon = NSImage.imageNamed_("NSLockLockedTemplate")
                else:
                    systemIcon = NSImage.imageNamed_("NSLockUnlockedTemplate")
                
                # 如果找到系統圖示，使用它
                if systemIcon:
                    lockImage.unlockFocus()
                    return systemIcon
            except:
                pass
            
        finally:
            # 結束編輯
            lockImage.unlockFocus()
        
        # 設置為模板圖像以支援暗色模式
        lockImage.setTemplate_(True)
        
        return lockImage
    
    def updateLockButton(self):
        """更新鎖頭按鈕顯示（極簡設計版）"""
        try:
            if not hasattr(self, 'lockButton'):
                return
            
            # 創建自定義鎖頭圖示
            is_locked = not self.isInClearMode  # False=解鎖，True=上鎖
            lockImage = self.createLockImage(is_locked)
            
            # 檢測系統主題
            isDarkMode = NSApp.effectiveAppearance().name().containsString_("Dark")
            
            if lockImage:
                # 設置圖示
                self.lockButton.setImage_(lockImage)
                self.lockButton.setTitle_("")  # 清除文字標題
                
                # 設置按鈕狀態
                self.lockButton.setState_(1 if is_locked else 0)
                
                # === 極簡設計：簡潔的背景色（修復 PyObjC 警告）===
                if hasattr(self.lockButton, 'layer') and self.lockButton.layer():
                    layer = self.lockButton.layer()
                    
                    # 使用更安全的方式處理 CGColor
                    try:
                        if is_locked:
                            # 上鎖狀態：使用控制強調色
                            if CGColorCreateGenericRGB:
                                # 使用 Quartz 創建 CGColor
                                color = NSColor.controlAccentColor().colorWithAlphaComponent_(0.3)
                                r, g, b, a = color.redComponent(), color.greenComponent(), color.blueComponent(), color.alphaComponent()
                                cgColor = CGColorCreateGenericRGB(r, g, b, a)
                                layer.setBackgroundColor_(cgColor)
                            else:
                                # 備用方案：不設定背景色
                                pass
                        else:
                            # 解鎖狀態：使用灰色
                            if CGColorCreateGenericRGB:
                                if isDarkMode:
                                    # 深色模式下使用稍亮的灰色
                                    cgColor = CGColorCreateGenericRGB(0.25, 0.25, 0.25, 0.5)
                                else:
                                    # 淺色模式下使用稍暗的灰色
                                    cgColor = CGColorCreateGenericRGB(0.85, 0.85, 0.85, 0.5)
                                layer.setBackgroundColor_(cgColor)
                            else:
                                # 備用方案：不設定背景色
                                pass
                    except Exception as e:
                        # 如果仍然出錯，忽略背景色設定
                        debug_log(f"設定鎖頭按鈕背景色時發生錯誤（可忽略）: {e}")
                    
                    # 極簡設計：移除邊框
                    layer.setBorderWidth_(0.0)
                
                # === 極簡設計：簡潔的圖示顏色 ===
                if hasattr(self.lockButton, 'setContentTintColor_'):
                    # 使用系統控制顏色，保持一致性
                    if is_locked:
                        # 上鎖狀態：使用系統強調色
                        self.lockButton.setContentTintColor_(NSColor.controlAccentColor())
                    else:
                        # 解鎖狀態：使用更明顯的顏色
                        if isDarkMode:
                            # 深色模式使用較亮的顏色
                            self.lockButton.setContentTintColor_(NSColor.secondaryLabelColor())
                        else:
                            # 淺色模式使用較深的顏色，確保可見性
                            self.lockButton.setContentTintColor_(NSColor.labelColor())
                
                # 設置工具提示 - 保持簡潔
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
                
                # 強制重繪按鈕
                self.lockButton.setNeedsDisplay_(True)
                
                debug_log(f"已更新鎖頭按鈕外觀：{'🔒 鎖定' if is_locked else '🔓 解鎖'}")
            else:
                # 後備方案：極簡文字按鈕
                debug_log("圖示創建失敗，使用極簡文字後備方案")
                
                # 設定文字
                title = "🔒" if not self.isInClearMode else "🔓"
                self.lockButton.setTitle_(title)
                self.lockButton.setImage_(None)
                
                # 設定系統字體
                self.lockButton.setFont_(NSFont.systemFontOfSize_(14.0))
                
                # 設定顏色 - 使用系統顏色
                if hasattr(self.lockButton, 'setContentTintColor_'):
                    self.lockButton.setContentTintColor_(NSColor.controlTextColor())
            
        except Exception as e:
            debug_log(f"更新鎖頭按鈕錯誤: {e}")
            # 最基本的後備方案
            if hasattr(self, 'lockButton'):
                title = "🔒" if not self.isInClearMode else "🔓"
                self.lockButton.setTitle_(title)
                self.lockButton.setImage_(None)
    
    def updateSearchField(self):
        """更新搜尋欄位內容"""
        try:
            if hasattr(self.plugin, 'lastInput') and self.plugin.lastInput:
                self.searchField.setStringValue_(self.plugin.lastInput)
        except Exception as e:
            debug_log(f"更新搜尋欄位錯誤: {e}")
    
    def update_ui(self, plugin_state, update_lock_fields=True):
        """根據外掛狀態更新UI元素（階段2.2：增強版）
        
        Args:
            plugin_state: 外掛狀態物件
            update_lock_fields: 是否更新鎖定輸入框（預設True）
        """
        try:
            debug_log(f"[階段2.2] 更新控制面板 UI，update_lock_fields={update_lock_fields}")
            
            # 批次更新UI元件
            if hasattr(plugin_state, 'lastInput') and hasattr(self, 'searchField'):
                input_value = plugin_state.lastInput or ""
                self.searchField.setStringValue_(input_value)
            
            # === 修正：僅在需要時更新鎖定字符 ===
            if update_lock_fields and hasattr(plugin_state, 'lockedChars') and hasattr(self, 'lockFields'):
                # 先清空所有欄位
                for field in self.lockFields.values():
                    field.setStringValue_("")
                
                # 再填入已儲存的鎖定字符
                for position, char_or_name in plugin_state.lockedChars.items():
                    if position in self.lockFields:
                        self.lockFields[position].setStringValue_(char_or_name)
                        debug_log(f"[階段2.2] 填入位置 {position}: '{char_or_name}'")
            elif not update_lock_fields:
                debug_log("[階段2.2] 跳過鎖定輸入框更新，保持用戶輸入")
            
            # 觸發重繪
            self.setNeedsDisplay_(True)
            
        except Exception as e:
            debug_log(f"[階段2.2] 更新UI錯誤: {e}")
    
    def themeChanged_(self, notification):
        """主題變更處理"""
        try:
            self.setNeedsDisplay_(True)
        except Exception as e:
            debug_log(f"主題變更處理錯誤: {e}")
    
    # === 階段 3.1：按鈕動作 ===
    def randomizeStub_(self, sender):
        """隨機排列按鈕（階段 3.1：啟用）"""
        debug_log("[3.1] 隨機排列按鈕被點擊")
        # 呼叫 plugin 的隨機排列功能
        if hasattr(self, 'plugin') and self.plugin:
            self.plugin.randomizeCallback(sender)
    
    # === 階段 3-2：清空所有欄位 ===
    def clearAllFields_(self, sender):
        """清空所有鎖定輸入框（階段 3-2）"""
        try:
            debug_log("[3.2] 清空所有欄位按鈕被點擊")
            
            # 清空所有鎖定輸入框
            if hasattr(self, 'lockFields') and self.lockFields:
                for position, field in self.lockFields.items():
                    field.setStringValue_("")
                    debug_log(f"[3.2] 清空位置 {position} 的輸入框")
            
            # 更新 plugin 的 lockedChars
            if hasattr(self, 'plugin') and self.plugin:
                if hasattr(self.plugin, 'lockedChars'):
                    # 備份當前狀態（如果需要）
                    if hasattr(self.plugin, 'previousLockedChars'):
                        self.plugin.previousLockedChars = self.plugin.lockedChars.copy()
                    
                    # 清空鎖定字符
                    self.plugin.lockedChars.clear()
                    debug_log("[3.2] 已清空 plugin.lockedChars")
                    
                    # 儲存偏好設定
                    self.plugin.savePreferences()
                    
                    # 重新生成排列（如果在上鎖狀態）
                    if not self.isInClearMode:  # 上鎖狀態
                        debug_log("[3.2] 🔒 上鎖狀態 - 重新生成排列")
                        self.plugin.generateNewArrangement()
                        # 觸發預覽更新
                        self.plugin.updateInterface(None)
                    else:
                        debug_log("[3.2] 🔓 解鎖狀態 - 不需要更新預覽")
            
            debug_log("[3.2] 完成清空所有輸入框")
            
        except Exception as e:
            debug_log(f"[3.2] 清空所有欄位錯誤: {e}")
            import traceback
            debug_log(traceback.format_exc())
    
    def lockAllStub_(self, sender):
        """鎖定全部按鈕存根（階段1.3）"""
        debug_log("[階段1.3] 鎖定全部按鈕被點擊")
    
    def unlockAllStub_(self, sender):
        """解鎖全部按鈕存根（階段1.3）"""
        debug_log("[階段1.3] 解鎖全部按鈕被點擊")
    
    def drawRect_(self, rect):
        """繪製背景（使用更符合 macOS 標準的顏色）"""
        try:
            # 使用更符合 macOS 標準的背景顏色
            isDarkMode = NSApp.effectiveAppearance().name().containsString_("Dark")
            if isDarkMode:
                backgroundColor = NSColor.windowBackgroundColor()
            else:
                # 在亮色模式下使用淺灰色，更符合 macOS 標準
                backgroundColor = NSColor.colorWithCalibratedWhite_alpha_(0.93, 1.0)
            
            backgroundColor.set()
            NSRectFill(rect)
            
            # 繪製上部細微分隔線
            bounds = self.bounds()
            margin = 12
            
            if hasattr(self, 'searchField'):
                searchBottom = self.searchField.frame().origin.y
                lineY = searchBottom - 8  # 在搜尋欄位下方稍微偏下的位置
                
                # 繪製微妙的分隔線，使用系統分隔線顏色
                lineRect = NSMakeRect(margin, lineY, bounds.size.width - 2 * margin, 1)
                NSColor.separatorColor().set()
                NSRectFill(lineRect)
            
            # 繪製底部細微分隔線
            if hasattr(self, 'clearAllButton'):
                buttonTop = self.clearAllButton.frame().origin.y + self.clearAllButton.frame().size.height
                lineY = buttonTop + 8  # 在按鈕上方稍微偏上的位置
                
                # 繪製微妙的分隔線，使用系統分隔線顏色
                lineRect = NSMakeRect(margin, lineY, bounds.size.width - 2 * margin, 1)
                NSColor.separatorColor().set()
                NSRectFill(lineRect)
            
        except Exception as e:
            debug_log(f"繪製背景錯誤: {e}")
    
    def dealloc(self):
        """析構函數"""
        try:
            NSNotificationCenter.defaultCenter().removeObserver_(self)
        except:
            pass
        objc.super(ControlsPanelView, self).dealloc()