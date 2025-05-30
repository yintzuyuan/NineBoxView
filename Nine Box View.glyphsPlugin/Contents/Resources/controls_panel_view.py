# encoding: utf-8
"""
九宮格預覽外掛 - 控制面板視圖
Nine Box Preview Plugin - Controls Panel View
"""

from __future__ import division, print_function, unicode_literals
import traceback
import objc
from GlyphsApp import Glyphs
from AppKit import (
    NSView, NSColor, NSRectFill, NSBezierPath, NSFont, 
    NSFontAttributeName, NSForegroundColorAttributeName,
    NSMutableDictionary, NSString, NSMakeRect, NSTextField,
    NSMakePoint, NSButton, NSBezelStyleRounded,
    NSTexturedRoundedBezelStyle, NSButtonTypeMomentaryPushIn,
    NSAttributedString, NSCenterTextAlignment, NSSearchField,
    NSButtonTypeToggle, NSFocusRingTypeNone, 
    NSCompositingOperationSourceOver, NSBorderlessWindowMask,
    NSUserDefaults, NSNotificationCenter, NSUserDefaultsDidChangeNotification,
    NSApp, NSViewWidthSizable, NSViewHeightSizable, NSViewMinYMargin, NSViewMaxYMargin,
    NSMenu, NSMenuItem, NSApplication, NSEventMask, NSEventTypeRightMouseDown,
    NSPointInRect, NSImage, NSBezelStyleRegularSquare, NSImageOnly
)
from Foundation import NSObject

# 修改 CustomTextField 類別，添加文字變更監聽功能
class CustomTextField(NSTextField):
    """支援右鍵選單的文本框類別"""
    
    def initWithFrame_plugin_(self, frame, plugin):
        """初始化文本框"""
        self = objc.super(CustomTextField, self).initWithFrame_(frame)
        if self:
            self.plugin = plugin
            # 設定右鍵選單
            self.setupContextMenu()
            
            # 註冊文本變更通知，實現即時更新
            NSNotificationCenter.defaultCenter().addObserver_selector_name_object_(
                self,
                "textDidChange:",
                "NSControlTextDidChangeNotification",
                self
            )
        return self
    
    def setupContextMenu(self):
        """設定右鍵選單"""
        try:
            # 創建選單
            contextMenu = NSMenu.alloc().init()
            
            # 添加選擇字符選單項
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
            
            # 設定選單
            self.setMenu_(contextMenu)
            
        except Exception as e:
            print(f"設定右鍵選單時發生錯誤: {e}")
            print(traceback.format_exc())
    
    def pickGlyphAction_(self, sender):
        """選擇字符功能的回調函數"""
        if hasattr(self, 'plugin') and self.plugin:
            self.plugin.pickGlyphCallback(sender)
    
    def textDidChange_(self, notification):
        """文本變更時的回調函數"""
        try:
            # 呼叫外掛的搜尋欄位回調函數
            if hasattr(self, 'plugin') and self.plugin:
                self.plugin.searchFieldCallback(self)
        except Exception as e:
            print(f"文本變更處理時發生錯誤: {e}")
            print(traceback.format_exc())
    
    def dealloc(self):
        """析構函數"""
        # 移除通知觀察者
        NSNotificationCenter.defaultCenter().removeObserver_(self)
        objc.super(CustomTextField, self).dealloc()


# 添加單字符輸入框類別
class LockCharacterField(NSTextField):
    """單字符鎖定輸入框類別"""
    
    def initWithFrame_position_plugin_(self, frame, position, plugin):
        """初始化單字符輸入框"""
        self = objc.super(LockCharacterField, self).initWithFrame_(frame)
        if self:
            self.plugin = plugin
            self.position = position  # 儲存位置索引 (0-7)
            
            # 設定文本框外觀
            self.setFont_(NSFont.systemFontOfSize_(14.0))
            self.setFocusRingType_(NSFocusRingTypeNone)
            self.setBezeled_(True)
            self.setEditable_(True)
            
            # 關鍵修改：設置為可接受多行輸入
            self.setUsesSingleLineMode_(True)
            
            # 設置居中對齊
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
            
            # 註冊右鍵選單
            self.setupContextMenu()
            
            # 註冊文本變更通知，實現即時智能辨識
            NSNotificationCenter.defaultCenter().addObserver_selector_name_object_(
                self,
                "textDidChange:",
                "NSControlTextDidChangeNotification",
                self
            )
        return self
    
    def setupContextMenu(self):
        """設定右鍵選單"""
        try:
            # 創建選單
            contextMenu = NSMenu.alloc().init()
            
            # 添加選擇字符選單項
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
            
            # 設定選單
            self.setMenu_(contextMenu)
            
        except Exception as e:
            print(f"設定右鍵選單時發生錯誤: {e}")
            print(traceback.format_exc())
    
    def pickGlyphAction_(self, sender):
        """選擇字符功能的回調函數"""
        if hasattr(self, 'plugin') and self.plugin:
            self.plugin.pickGlyphCallback(sender)
    
    def textDidChange_(self, notification):
        """文本變更時的智能回調函數"""
        try:
            # 呼叫外掛的智能鎖定字符回調函數
            if hasattr(self, 'plugin') and self.plugin:
                self.plugin.smartLockCharacterCallback(self)
        except Exception as e:
            print(f"智能鎖定字符處理時發生錯誤: {e}")
            print(traceback.format_exc())
    
    def dealloc(self):
        """析構函數"""
        # 移除通知觀察者
        NSNotificationCenter.defaultCenter().removeObserver_(self)
        objc.super(LockCharacterField, self).dealloc()


class ControlsPanelView(NSView):
    """
    控制面板視圖類別，作為獨立子視窗的內容視圖
    Controls Panel View class, serves as content view for independent sub-window
    """
    
    def initWithFrame_plugin_(self, frame, plugin):
        """
        初始化控制面板視圖
        Initialize the controls panel view
        
        Args:
            frame: 視圖框架
            plugin: 外掛主類別實例
            
        Returns:
            self: 初始化後的視圖實例
        """
        try:
            self = objc.super(ControlsPanelView, self).initWithFrame_(frame)
            if self:
                self.plugin = plugin
                self.lockFields = {}  # 儲存鎖定輸入框
                self.isInClearMode = True  # 鎖頭狀態：True=解鎖，False=上鎖
                
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
            print(f"初始化控制面板視圖時發生錯誤: {e}")
            print(traceback.format_exc())
            return None
    
    def setupUI(self):
        """設定使用者介面元件"""
        try:
            # 清除現有子視圖
            for subview in self.subviews():
                subview.removeFromSuperview()
            
            # 獲取視圖尺寸
            bounds = self.bounds()
            width = bounds.size.width
            height = bounds.size.height
            
            # 設定邊距和間距
            margin = 10
            spacing = 8
            current_y = height - margin
            
            # 1. 長文本輸入框
            search_height = 60
            current_y -= search_height
            searchRect = NSMakeRect(margin, current_y, width - 2 * margin, search_height)
            self.searchField = CustomTextField.alloc().initWithFrame_plugin_(searchRect, self.plugin)
            self.searchField.setAutoresizingMask_(NSViewWidthSizable | NSViewMaxYMargin)
            
            # 設定搜尋欄位屬性
            self.searchField.setFont_(NSFont.systemFontOfSize_(14.0))
            self.searchField.setFocusRingType_(NSFocusRingTypeNone)
            self.searchField.setBezeled_(True)
            self.searchField.setEditable_(True)
            
            # 設定提示文字
            searchPlaceholder = Glyphs.localize({
                'en': u'Enter characters or Nice Names...',
                'zh-Hant': u'輸入字符或 Nice Names...',
                'zh-Hans': u'输入字符或 Nice Names...',
                'ja': u'文字または Nice Names を入力...',
                'ko': u'문자 또는 Nice Names 입력...',
            })
            self.searchField.setPlaceholderString_(searchPlaceholder)
            
            # 設定提示
            searchTooltip = Glyphs.localize({
                'en': u'Enter multiple characters or Nice Names separated by spaces',
                'zh-Hant': u'輸入多個字符或以空格分隔的 Nice Names',
                'zh-Hans': u'输入多个字符或以空格分隔的 Nice Names',
                'ja': u'複数の文字またはスペースで区切られた Nice Names を入力',
                'ko': u'여러 문자 또는 공백으로 구분된 Nice Names 입력',
            })
            self.searchField.setToolTip_(searchTooltip)
            
            self.addSubview_(self.searchField)
            
            # 2. 隨機排列按鈕
            current_y -= spacing + 30
            randomizeRect = NSMakeRect(margin, current_y, width - 2 * margin, 30)
            self.randomizeButton = NSButton.alloc().initWithFrame_(randomizeRect)
            self.randomizeButton.setAutoresizingMask_(NSViewWidthSizable | NSViewMaxYMargin)
            self.randomizeButton.setTitle_(Glyphs.localize({
                'en': u'Randomize',
                'zh-Hant': u'隨機排列',
                'zh-Hans': u'随机排列',
                'ja': u'ランダム配置',
                'ko': u'무작위 배치',
            }))
            self.randomizeButton.setTarget_(self.plugin)
            self.randomizeButton.setAction_("randomizeCallback:")
            self.randomizeButton.setBezelStyle_(NSBezelStyleRounded)
            self.randomizeButton.setButtonType_(NSButtonTypeMomentaryPushIn)
            
            # 設定提示
            randomizeTooltip = Glyphs.localize({
                'en': u'Generate a new random arrangement',
                'zh-Hant': u'產生新的隨機排列',
                'zh-Hans': u'生成新的随机排列',
                'ja': u'新しいランダム配置を生成',
                'ko': u'새로운 무작위 배치 생성',
            })
            self.randomizeButton.setToolTip_(randomizeTooltip)
            
            self.addSubview_(self.randomizeButton)
            
            # 3. 鎖頭按鈕
            current_y -= spacing + 30
            lockRect = NSMakeRect(margin, current_y, width - 2 * margin, 30)
            self.lockButton = NSButton.alloc().initWithFrame_(lockRect)
            self.lockButton.setAutoresizingMask_(NSViewWidthSizable | NSViewMaxYMargin)
            self.lockButton.setTarget_(self)
            self.lockButton.setAction_("toggleLockMode:")
            self.lockButton.setBezelStyle_(NSBezelStyleRounded)
            self.lockButton.setButtonType_(NSButtonTypeToggle)
            
            # 更新鎖頭按鈕狀態
            self.updateLockButton()
            
            self.addSubview_(self.lockButton)
            
            # 4. 鎖定輸入框標題
            current_y -= spacing + 20
            titleRect = NSMakeRect(margin, current_y, width - 2 * margin, 20)
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
            
            # 5. 鎖定輸入框（3x3網格，排除中央）
            current_y -= spacing + 10
            field_size = 30
            field_spacing = 5
            grid_width = 3 * field_size + 2 * field_spacing
            start_x = (width - grid_width) / 2
            
            # 創建3x3網格的鎖定輸入框（跳過中央位置）
            position = 0
            for row in range(3):
                for col in range(3):
                    if row == 1 and col == 1:  # 跳過中央位置
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
            
            # 6. 控制按鈕區域
            current_y -= 3 * (field_size + field_spacing) + spacing
            
            # 鎖定所有按鈕
            button_height = 25
            current_y -= button_height
            lockAllRect = NSMakeRect(margin, current_y, width - 2 * margin, button_height)
            self.lockAllButton = NSButton.alloc().initWithFrame_(lockAllRect)
            self.lockAllButton.setAutoresizingMask_(NSViewWidthSizable | NSViewMaxYMargin)
            self.lockAllButton.setTitle_(Glyphs.localize({
                'en': u'Lock All',
                'zh-Hant': u'鎖定全部',
                'zh-Hans': u'锁定全部',
                'ja': u'すべてロック',
                'ko': u'모두 고정',
            }))
            self.lockAllButton.setTarget_(self.plugin)
            self.lockAllButton.setAction_("clearAllLockFieldsCallback:")
            self.lockAllButton.setBezelStyle_(NSBezelStyleRounded)
            self.lockAllButton.setButtonType_(NSButtonTypeMomentaryPushIn)
            self.lockAllButton.setFont_(NSFont.systemFontOfSize_(11.0))
            
            self.addSubview_(self.lockAllButton)
            
            # 解鎖所有按鈕
            current_y -= spacing + button_height
            unlockAllRect = NSMakeRect(margin, current_y, width - 2 * margin, button_height)
            self.unlockAllButton = NSButton.alloc().initWithFrame_(unlockAllRect)
            self.unlockAllButton.setAutoresizingMask_(NSViewWidthSizable | NSViewMaxYMargin)
            self.unlockAllButton.setTitle_(Glyphs.localize({
                'en': u'Unlock All',
                'zh-Hant': u'解鎖全部',
                'zh-Hans': u'解锁全部',
                'ja': u'すべてアンロック',
                'ko': u'모두 해제',
            }))
            self.unlockAllButton.setTarget_(self.plugin)
            self.unlockAllButton.setAction_("restoreAllLockFieldsCallback:")
            self.unlockAllButton.setBezelStyle_(NSBezelStyleRounded)
            self.unlockAllButton.setButtonType_(NSButtonTypeMomentaryPushIn)
            self.unlockAllButton.setFont_(NSFont.systemFontOfSize_(11.0))
            
            self.addSubview_(self.unlockAllButton)
            
            # 更新搜尋欄位內容
            self.updateSearchField()
            
        except Exception as e:
            print(f"設定UI時發生錯誤: {e}")
            print(traceback.format_exc())
    
    def toggleLockMode_(self, sender):
        """切換鎖頭模式"""
        try:
            self.isInClearMode = not self.isInClearMode
            self.updateLockButton()
            
            # 根據鎖頭狀態更新輸入框的啟用狀態
            for field in self.lockFields.values():
                field.setEnabled_(not self.isInClearMode)
            
            print(f"鎖頭模式切換為: {'解鎖' if self.isInClearMode else '上鎖'}")
            
        except Exception as e:
            print(f"切換鎖頭模式時發生錯誤: {e}")
            print(traceback.format_exc())
    
    def updateLockButton(self):
        """更新鎖頭按鈕的顯示"""
        try:
            if self.isInClearMode:
                # 解鎖狀態
                self.lockButton.setTitle_("🔓 " + Glyphs.localize({
                    'en': u'Unlocked',
                    'zh-Hant': u'解鎖',
                    'zh-Hans': u'解锁',
                    'ja': u'アンロック',
                    'ko': u'잠금 해제',
                }))
                self.lockButton.setState_(0)
                tooltip = Glyphs.localize({
                    'en': u'Click to lock positions (enable position locking)',
                    'zh-Hant': u'點擊以鎖定位置（啟用位置鎖定）',
                    'zh-Hans': u'点击以锁定位置（启用位置锁定）',
                    'ja': u'クリックして位置をロック（位置ロックを有効にする）',
                    'ko': u'클릭하여 위치 고정 (위치 고정 활성화)',
                })
            else:
                # 上鎖狀態
                self.lockButton.setTitle_("🔒 " + Glyphs.localize({
                    'en': u'Locked',
                    'zh-Hant': u'上鎖',
                    'zh-Hans': u'上锁',
                    'ja': u'ロック',
                    'ko': u'잠금',
                }))
                self.lockButton.setState_(1)
                tooltip = Glyphs.localize({
                    'en': u'Click to unlock positions (disable position locking)',
                    'zh-Hant': u'點擊以解鎖位置（停用位置鎖定）',
                    'zh-Hans': u'点击以解锁位置（停用位置锁定）',
                    'ja': u'クリックして位置をアンロック（位置ロックを無効にする）',
                    'ko': u'클릭하여 위치 해제 (위치 고정 비활성화)',
                })
            
            self.lockButton.setToolTip_(tooltip)
            
        except Exception as e:
            print(f"更新鎖頭按鈕時發生錯誤: {e}")
            print(traceback.format_exc())
    
    def updateSearchField(self):
        """更新搜尋欄位內容"""
        try:
            if hasattr(self.plugin, 'lastInput') and self.plugin.lastInput:
                self.searchField.setStringValue_(self.plugin.lastInput)
        except Exception as e:
            print(f"更新搜尋欄位時發生錯誤: {e}")
            print(traceback.format_exc())
    
    def update_ui(self, plugin_state):
        """根據外掛狀態更新UI元素"""
        try:
            # 更新搜尋欄位
            if hasattr(plugin_state, 'lastInput'):
                self.searchField.setStringValue_(plugin_state.lastInput or "")
            
            # 更新鎖定輸入框
            if hasattr(plugin_state, 'lockedChars'):
                for position, field in self.lockFields.items():
                    if position in plugin_state.lockedChars:
                        field.setStringValue_(plugin_state.lockedChars[position])
                    else:
                        field.setStringValue_("")
            
        except Exception as e:
            print(f"更新UI時發生錯誤: {e}")
            print(traceback.format_exc())
    
    def themeChanged_(self, notification):
        """主題變更時的處理"""
        try:
            # 重新設定顏色
            self.setNeedsDisplay_(True)
        except Exception as e:
            print(f"主題變更處理時發生錯誤: {e}")
            print(traceback.format_exc())
    
    def drawRect_(self, rect):
        """繪製背景"""
        try:
            # 根據系統主題設定背景顏色
            if NSApp.effectiveAppearance().name().containsString_("Dark"):
                backgroundColor = NSColor.colorWithRed_green_blue_alpha_(0.2, 0.2, 0.2, 1.0)
            else:
                backgroundColor = NSColor.colorWithRed_green_blue_alpha_(0.95, 0.95, 0.95, 1.0)
            
            backgroundColor.set()
            NSRectFill(rect)
            
        except Exception as e:
            print(f"繪製背景時發生錯誤: {e}")
            print(traceback.format_exc())
    
    def dealloc(self):
        """析構函數"""
        try:
            # 移除通知觀察者
            NSNotificationCenter.defaultCenter().removeObserver_(self)
        except:
            pass
        objc.super(ControlsPanelView, self).dealloc() 