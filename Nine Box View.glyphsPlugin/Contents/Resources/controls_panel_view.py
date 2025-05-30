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
    NSUserDefaultsDidChangeNotification
)
from Foundation import NSObject

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
        """選擇字符功能"""
        if hasattr(self, 'plugin') and self.plugin:
            self.plugin.pickGlyphCallback(sender)
    
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
        """文本變更時的回調"""
        try:
            if hasattr(self, 'plugin') and self.plugin:
                self.plugin.searchFieldCallback(self)
        except Exception as e:
            debug_log(f"文本變更處理錯誤: {e}")


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
        self.setFont_(NSFont.systemFontOfSize_(14.0))
        self.setFocusRingType_(NSFocusRingTypeNone)
        self.setBezeled_(True)
        self.setEditable_(True)
        self.setUsesSingleLineMode_(True)
        self.setAlignment_(NSCenterTextAlignment)
        
        # 設定提示
        lockedTooltip = Glyphs.localize({
            'en': u'Enter a character or Nice Name to lock in this position',
            'zh-Hant': u'輸入要鎖定在此位置的字符或 Nice Name',
            'zh-Hans': u'输入要锁定在此位置的字符或 Nice Name',
            'ja': u'この位置にロックする文字または Nice Name を入力してください',
            'ko': u'이 위치에 고정할 문자 또는 Nice Name을 입력하세요',
        })
        self.setToolTip_(lockedTooltip)
    
    def textDidChange_(self, notification):
        """文本變更時的智能回調"""
        try:
            if hasattr(self, 'plugin') and self.plugin:
                self.plugin.smartLockCharacterCallback(self)
        except Exception as e:
            debug_log(f"智能鎖定字符處理錯誤: {e}")


class ControlsPanelView(NSView):
    """
    控制面板視圖類別（優化版）
    Controls Panel View class (Optimized)
    """
    
    def initWithFrame_plugin_(self, frame, plugin):
        """初始化控制面板視圖"""
        try:
            self = objc.super(ControlsPanelView, self).initWithFrame_(frame)
            if self:
                self.plugin = plugin
                self.lockFields = {}
                self.isInClearMode = True  # True=解鎖，False=上鎖
                
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
                
            return self
        except Exception as e:
            print(f"初始化控制面板視圖錯誤: {e}")
            if DEBUG_MODE:
                print(traceback.format_exc())
            return None
    
    def _create_search_field(self, bounds):
        """創建搜尋欄位"""
        margin = 10
        spacing = 8
        search_height = 60
        
        current_y = bounds.size.height - margin - search_height
        searchRect = NSMakeRect(margin, current_y, bounds.size.width - 2 * margin, search_height)
        
        searchField = CustomTextField.alloc().initWithFrame_plugin_(searchRect, self.plugin)
        searchField.setAutoresizingMask_(NSViewWidthSizable | NSViewMaxYMargin)
        searchField.setFont_(NSFont.systemFontOfSize_(14.0))
        searchField.setFocusRingType_(NSFocusRingTypeNone)
        searchField.setBezeled_(True)
        searchField.setEditable_(True)
        
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
        
        return current_y - spacing
    
    def _create_buttons(self, bounds, current_y):
        """創建按鈕區域"""
        margin = 10
        spacing = 8
        button_height = 30
        
        # 隨機排列按鈕
        current_y -= button_height
        randomizeRect = NSMakeRect(margin, current_y, bounds.size.width - 2 * margin, button_height)
        randomizeButton = self._create_button(
            randomizeRect,
            Glyphs.localize({
                'en': u'Randomize',
                'zh-Hant': u'隨機排列',
                'zh-Hans': u'随机排列',
                'ja': u'ランダム配置',
                'ko': u'무작위 배치',
            }),
            self.plugin,
            "randomizeCallback:",
            Glyphs.localize({
                'en': u'Generate a new random arrangement',
                'zh-Hant': u'產生新的隨機排列',
                'zh-Hans': u'生成新的随机排列',
                'ja': u'新しいランダム配置を生成',
                'ko': u'새로운 무작위 배치 생성',
            })
        )
        self.randomizeButton = randomizeButton
        self._ui_components['randomizeButton'] = randomizeButton
        self.addSubview_(randomizeButton)
        
        # 鎖頭按鈕
        current_y -= spacing + button_height
        lockRect = NSMakeRect(margin, current_y, bounds.size.width - 2 * margin, button_height)
        lockButton = NSButton.alloc().initWithFrame_(lockRect)
        lockButton.setAutoresizingMask_(NSViewWidthSizable | NSViewMaxYMargin)
        lockButton.setTarget_(self)
        lockButton.setAction_("toggleLockMode:")
        lockButton.setBezelStyle_(NSBezelStyleRounded)
        lockButton.setButtonType_(NSButtonTypeToggle)
        
        self.lockButton = lockButton
        self._ui_components['lockButton'] = lockButton
        self.updateLockButton()
        self.addSubview_(lockButton)
        
        return current_y - spacing
    
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
        """創建鎖定輸入框"""
        margin = 10
        spacing = 8
        
        # 標題
        current_y -= 20
        titleRect = NSMakeRect(margin, current_y, bounds.size.width - 2 * margin, 20)
        titleLabel = NSTextField.alloc().initWithFrame_(titleRect)
        titleLabel.setAutoresizingMask_(NSViewWidthSizable | NSViewMaxYMargin)
        titleLabel.setStringValue_(Glyphs.localize({
            'en': u'Lock Positions:',
            'zh-Hant': u'鎖定位置：',
            'zh-Hans': u'锁定位置：',
            'ja': u'位置をロック：',
            'ko': u'위치 고정：',
        }))
        titleLabel.setBezeled_(False)
        titleLabel.setDrawsBackground_(False)
        titleLabel.setEditable_(False)
        titleLabel.setSelectable_(False)
        titleLabel.setFont_(NSFont.boldSystemFontOfSize_(12.0))
        self.addSubview_(titleLabel)
        
        # 鎖定輸入框網格
        current_y -= spacing + 10
        field_size = 30
        field_spacing = 5
        grid_width = 3 * field_size + 2 * field_spacing
        start_x = (bounds.size.width - grid_width) / 2
        
        # 創建3x3網格（跳過中央）
        position = 0
        for row in range(3):
            for col in range(3):
                if row == 1 and col == 1:  # 跳過中央
                    continue
                
                x = start_x + col * (field_size + field_spacing)
                y = current_y - row * (field_size + field_spacing)
                
                fieldRect = NSMakeRect(x, y, field_size, field_size)
                lockField = LockCharacterField.alloc().initWithFrame_position_plugin_(
                    fieldRect, position, self.plugin
                )
                lockField.setAutoresizingMask_(NSViewMaxYMargin)
                
                self.lockFields[position] = lockField
                self.addSubview_(lockField)
                position += 1
        
        return current_y - 3 * (field_size + field_spacing) - spacing
    
    def _create_control_buttons(self, bounds, current_y):
        """創建控制按鈕"""
        margin = 10
        spacing = 8
        button_height = 25
        
        # 鎖定所有按鈕
        current_y -= button_height
        lockAllRect = NSMakeRect(margin, current_y, bounds.size.width - 2 * margin, button_height)
        lockAllButton = self._create_button(
            lockAllRect,
            Glyphs.localize({
                'en': u'Lock All',
                'zh-Hant': u'鎖定全部',
                'zh-Hans': u'锁定全部',
                'ja': u'すべてロック',
                'ko': u'모두 고정',
            }),
            self.plugin,
            "clearAllLockFieldsCallback:",
            ""
        )
        lockAllButton.setFont_(NSFont.systemFontOfSize_(11.0))
        self.lockAllButton = lockAllButton
        self._ui_components['lockAllButton'] = lockAllButton
        self.addSubview_(lockAllButton)
        
        # 解鎖所有按鈕
        current_y -= spacing + button_height
        unlockAllRect = NSMakeRect(margin, current_y, bounds.size.width - 2 * margin, button_height)
        unlockAllButton = self._create_button(
            unlockAllRect,
            Glyphs.localize({
                'en': u'Unlock All',
                'zh-Hant': u'解鎖全部',
                'zh-Hans': u'解锁全部',
                'ja': u'すべてアンロック',
                'ko': u'모두 해제',
            }),
            self.plugin,
            "restoreAllLockFieldsCallback:",
            ""
        )
        unlockAllButton.setFont_(NSFont.systemFontOfSize_(11.0))
        self.unlockAllButton = unlockAllButton
        self._ui_components['unlockAllButton'] = unlockAllButton
        self.addSubview_(unlockAllButton)
    
    def setupUI(self):
        """設定使用者介面元件（優化版）"""
        try:
            # 清除現有子視圖
            for subview in self.subviews():
                subview.removeFromSuperview()
            
            # 清除參照
            self.lockFields = {}
            self._ui_components = {}
            
            # 獲取視圖尺寸
            bounds = self.bounds()
            
            # 依序創建UI元件
            current_y = self._create_search_field(bounds)
            current_y = self._create_buttons(bounds, current_y)
            current_y = self._create_lock_fields(bounds, current_y)
            self._create_control_buttons(bounds, current_y)
            
            # 更新內容
            self._update_content()
            
        except Exception as e:
            print(f"設定UI時發生錯誤: {e}")
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
        """切換鎖頭模式"""
        try:
            self.isInClearMode = not self.isInClearMode
            self.updateLockButton()
            
            # 更新輸入框狀態
            for field in self.lockFields.values():
                field.setEnabled_(not self.isInClearMode)
            
            debug_log(f"鎖頭模式：{'解鎖' if self.isInClearMode else '上鎖'}")
            
        except Exception as e:
            debug_log(f"切換鎖頭模式錯誤: {e}")
    
    def updateLockButton(self):
        """更新鎖頭按鈕顯示"""
        try:
            if self.isInClearMode:
                # 解鎖狀態
                title = "🔓 " + Glyphs.localize({
                    'en': u'Unlocked',
                    'zh-Hant': u'解鎖',
                    'zh-Hans': u'解锁',
                    'ja': u'アンロック',
                    'ko': u'잠금 해제',
                })
                state = 0
                tooltip = Glyphs.localize({
                    'en': u'Click to lock positions (enable position locking)',
                    'zh-Hant': u'點擊以鎖定位置（啟用位置鎖定）',
                    'zh-Hans': u'点击以锁定位置（启用位置锁定）',
                    'ja': u'クリックして位置をロック（位置ロックを有効にする）',
                    'ko': u'클릭하여 위치 고정 (위치 고정 활성화)',
                })
            else:
                # 上鎖狀態
                title = "🔒 " + Glyphs.localize({
                    'en': u'Locked',
                    'zh-Hant': u'上鎖',
                    'zh-Hans': u'上锁',
                    'ja': u'ロック',
                    'ko': u'잠금',
                })
                state = 1
                tooltip = Glyphs.localize({
                    'en': u'Click to unlock positions (disable position locking)',
                    'zh-Hant': u'點擊以解鎖位置（停用位置鎖定）',
                    'zh-Hans': u'点击以解锁位置（停用位置锁定）',
                    'ja': u'クリックして位置をアンロック（位置ロックを無効にする）',
                    'ko': u'클릭하여 위치 해제 (위치 고정 비활성화)',
                })
            
            self.lockButton.setTitle_(title)
            self.lockButton.setState_(state)
            self.lockButton.setToolTip_(tooltip)
            
        except Exception as e:
            debug_log(f"更新鎖頭按鈕錯誤: {e}")
    
    def updateSearchField(self):
        """更新搜尋欄位內容"""
        try:
            if hasattr(self.plugin, 'lastInput') and self.plugin.lastInput:
                self.searchField.setStringValue_(self.plugin.lastInput)
        except Exception as e:
            debug_log(f"更新搜尋欄位錯誤: {e}")
    
    def update_ui(self, plugin_state):
        """根據外掛狀態更新UI元素（優化版）"""
        try:
            debug_log("更新控制面板 UI")
            
            # 批次更新UI元件
            if hasattr(plugin_state, 'lastInput') and hasattr(self, 'searchField'):
                input_value = plugin_state.lastInput or ""
                self.searchField.setStringValue_(input_value)
            
            if hasattr(plugin_state, 'lockedChars') and hasattr(self, 'lockFields'):
                for position, field in self.lockFields.items():
                    value = plugin_state.lockedChars.get(position, "")
                    field.setStringValue_(value)
            
            # 觸發重繪
            self.setNeedsDisplay_(True)
            
        except Exception as e:
            debug_log(f"更新UI錯誤: {e}")
    
    def themeChanged_(self, notification):
        """主題變更處理"""
        try:
            self.setNeedsDisplay_(True)
        except Exception as e:
            debug_log(f"主題變更處理錯誤: {e}")
    
    def drawRect_(self, rect):
        """繪製背景（優化版）"""
        try:
            # 根據系統主題設定背景顏色
            isDarkMode = NSApp.effectiveAppearance().name().containsString_("Dark")
            backgroundColor = (NSColor.colorWithRed_green_blue_alpha_(0.2, 0.2, 0.2, 1.0) 
                             if isDarkMode 
                             else NSColor.colorWithRed_green_blue_alpha_(0.95, 0.95, 0.95, 1.0))
            
            backgroundColor.set()
            NSRectFill(rect)
            
        except Exception as e:
            debug_log(f"繪製背景錯誤: {e}")
    
    def dealloc(self):
        """析構函數"""
        try:
            NSNotificationCenter.defaultCenter().removeObserver_(self)
        except:
            pass
        objc.super(ControlsPanelView, self).dealloc()