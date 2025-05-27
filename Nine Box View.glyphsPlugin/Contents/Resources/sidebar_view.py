# encoding: utf-8
"""
九宮格預覽外掛 - 側邊欄視圖
Nine Box Preview Plugin - Sidebar View
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
    NSPointInRect
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
    
    def textDidChange_(self, notification):
        """文本變更時的回調函數"""
        try:
            if hasattr(self, 'plugin') and self.plugin:
                # 直接調用 plugin 的搜尋欄位回調函數，傳遞自己作為參數
                self.plugin.searchFieldCallback(self)
        except Exception as e:
            print(f"處理文本變更時發生錯誤: {e}")
            print(traceback.format_exc())
    
    def pickGlyphAction_(self, sender):
        """選擇字符功能的回調函數"""
        if hasattr(self, 'plugin') and self.plugin:
            self.plugin.pickGlyphCallback(sender)
            
    def dealloc(self):
        """釋放資源"""
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
            self.setUsesSingleLineMode_(False)
            
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
            # 獲取當前輸入內容
            input_text = self.stringValue()
            
            # 如果輸入為空，立即處理清空事件
            if not input_text:
                if hasattr(self, 'plugin') and hasattr(self.plugin, 'handleLockFieldCleared'):
                    self.plugin.handleLockFieldCleared(self)
                    # 確保欄位保持為空
                    self.setStringValue_("")
                return
            
            # 對於非空輸入，直接處理（不再使用延遲）
            # 讓 smartLockCharacterCallback 自己處理頻率控制
            if hasattr(self, 'plugin') and hasattr(self.plugin, 'smartLockCharacterCallback'):
                self.plugin.smartLockCharacterCallback(self)
            
        except Exception as e:
            print(f"處理文本變更時發生錯誤: {e}")
            print(traceback.format_exc())
    
    def dealloc(self):
        """釋放資源"""
        # 移除通知觀察者
        NSNotificationCenter.defaultCenter().removeObserver_(self)
        objc.super(LockCharacterField, self).dealloc()


class SidebarView(NSView):
    """
    側邊欄視圖類別，顯示額外資訊和控制項
    Sidebar View Class, displays additional information and controls
    """

    def initWithFrame_plugin_(self, frame, plugin):
        """
        初始化側邊欄視圖
        Initialize the sidebar view
        
        Args:
            frame: 視圖尺寸和位置
            plugin: 外掛主類別實例
        
        Returns:
            self: 初始化後的視圖實例
        """
        self = objc.super(SidebarView, self).initWithFrame_(frame)
        if self:
            self.plugin = plugin
            
            # 追蹤清空/還原按鈕的狀態 (True = 清空模式，False = 還原模式)
            self.isInClearMode = True
            
            # 設置側邊欄視圖的自動調整掩碼 - 視圖寬度可調整，高度可調整
            self.setAutoresizingMask_(NSViewWidthSizable | NSViewHeightSizable)
            
            # === 布局常數設定 ===
            margin = 10  # 基本邊距
            totalHeight = frame.size.height  # 側邊欄總高度
            frameWidth = frame.size.width  # 側邊欄寬度
            
            # 計算各區塊的大小比例（使用相對尺寸）
            titleHeightRatio = 0.04  # 標題高度佔總高度的比例
            buttonHeightRatio = 0.06  # 按鈕高度佔總高度的比例
            lockFieldHeightRatio = 0.05  # 鎖定輸入框高度佔總高度的比例
            
            # 計算實際尺寸（但設定最小值避免過小）
            titleHeight = max(20, totalHeight * titleHeightRatio)
            buttonHeight = max(24, totalHeight * buttonHeightRatio)
            fieldHeight = max(20, totalHeight * lockFieldHeightRatio)
            
            # 各元素間距（也使用相對尺寸）
            sectionSpacingRatio = 0.025  # 主要區塊間距佔總高度的比例
            elementSpacingRatio = 0.02  # 元素間距佔總高度的比例
            
            # 計算實際間距（但設定最小值避免過小）
            sectionSpacing = max(10, totalHeight * sectionSpacingRatio)
            elementSpacing = max(8, totalHeight * elementSpacingRatio)
            
            # 確保上邊距也是相對的
            topMarginRatio = 0.02  # 頂部間距佔總高度的比例
            topMargin = max(8, totalHeight * topMarginRatio)
            
            # === 第一部分：標題區域（頂部） ===
            
            # 鎖定字符標題 - 位於頂部
            titleRect = NSMakeRect(
                margin,  # x 座標
                totalHeight - titleHeight - topMargin,  # y 座標，從頂部開始
                frameWidth - margin * 2,  # 寬度
                titleHeight  # 高度
            )
            self.lockTitle = NSTextField.alloc().initWithFrame_(titleRect)
            self.lockTitle.setStringValue_(Glyphs.localize({
                'en': u'Lock Characters (support Nice Name):',
                'zh-Hant': u'鎖定字符（支援 Nice Name）:',
                'zh-Hans': u'锁定字符（支持 Nice Name）:',
                'ja': u'文字をロック（Nice Name対応）:',
                'ko': u'글자 고정 (Nice Name 지원):',
            }))
            self.lockTitle.setBezeled_(False)
            self.lockTitle.setDrawsBackground_(False)
            self.lockTitle.setEditable_(False)
            self.lockTitle.setSelectable_(False)
            self.lockTitle.setFont_(NSFont.boldSystemFontOfSize_(12.0))
            self.lockTitle.setAutoresizingMask_(NSViewWidthSizable | NSViewMinYMargin)
            self.addSubview_(self.lockTitle)
            
            # === 第二部分：清空/還原按鈕（標題下方） ===
            
            # 計算按鈕位置（在標題下方）
            buttonsY = totalHeight - titleHeight - topMargin - buttonHeight - elementSpacing
            
            # 清空/還原按鈕 (兩功能合一)
            self.actionButtonRect = NSMakeRect(
                margin,  # x 座標
                buttonsY,  # y 座標
                frameWidth - margin * 2,  # 寬度
                buttonHeight  # 高度
            )
            self.actionButton = NSButton.alloc().initWithFrame_(self.actionButtonRect)
            self.updateActionButtonTitle()  # 初始化按鈕標題
            self.actionButton.setBezelStyle_(NSBezelStyleRounded)
            self.actionButton.setButtonType_(NSButtonTypeMomentaryPushIn)
            self.actionButton.setTarget_(self)
            self.actionButton.setAction_("actionButtonAction:")
            self.actionButton.setAutoresizingMask_(NSViewWidthSizable | NSViewMinYMargin)
            self.updateActionButtonTooltip()  # 初始化按鈕提示
            self.addSubview_(self.actionButton)
            
            # === 第三部分：鎖定字符輸入框 ===
            
            # 計算九宮格區域的頂部位置（在按鈕下方加上間距）
            lockFieldsTopY = buttonsY - sectionSpacing
            
            # 計算鎖定字符區域所佔用的空間比例
            lockFieldsHeightRatio = 0.38  # 整個鎖定字符區域佔總高度的最大比例
            
            # 根據可用空間計算實際高度（但不超過最大比例）
            availableHeightForLockFields = min(
                lockFieldsTopY - (margin * 2), 
                totalHeight * lockFieldsHeightRatio
            )
            
            # 根據可用空間重新計算字段高度和間距
            # 總共需要3行輸入框和2個間距
            numRows = 3
            numSpaces = 2
            
            # 設定理想尺寸（與原始設計一致）
            idealFieldHeight = 24  # 原始設計中的輸入框高度
            idealSmallMargin = 8   # 原始設計中的間距
            
            # 分配可用空間，但優先使用理想尺寸
            if availableHeightForLockFields >= (idealFieldHeight * numRows + idealSmallMargin * numSpaces):
                # 空間充足，使用理想尺寸
                fieldHeight = idealFieldHeight
                smallMargin = idealSmallMargin
            else:
                # 空間不足，按比例縮小
                # 根據比例分配高度和間距
                fieldHeight = availableHeightForLockFields * 0.8 / numRows  # 高度佔80%
                smallMargin = availableHeightForLockFields * 0.2 / numSpaces  # 間距佔20%
                
                # 確保最小尺寸
                fieldHeight = max(16, fieldHeight)
                smallMargin = max(3, smallMargin)
            
            # 計算九宮格區域的整體高度
            totalFieldsHeight = numRows * fieldHeight + numSpaces * smallMargin
            
            # 計算九宮格區域的底部位置
            lockFieldsBottomY = lockFieldsTopY - totalFieldsHeight
            
            # 計算每個單元格的寬度和橫向間距
            totalCellsPerRow = 3  # 每行最多3個輸入框
            horizontalSpaces = 2  # 每行2個水平間距
            
            # 理想的單元格寬度和間距
            idealCellWidth = (frameWidth - margin * 2 - idealSmallMargin * 2) / 3  # 原始設計的寬度
            idealHorizontalMargin = idealSmallMargin  # 使用相同的間距值
            
            # 可用寬度
            availableWidth = frameWidth - margin * 2
            
            # 優先使用理想尺寸
            if availableWidth >= (idealCellWidth * totalCellsPerRow + idealHorizontalMargin * horizontalSpaces):
                # 空間充足，使用理想尺寸
                cellWidth = idealCellWidth
                horizontalMargin = idealHorizontalMargin
            else:
                # 空間不足，按比例縮小
                cellWidth = availableWidth * 0.8 / totalCellsPerRow  # 單元格佔80%
                horizontalMargin = availableWidth * 0.2 / horizontalSpaces  # 間距佔20%
                
                # 確保最小尺寸
                cellWidth = max(35, cellWidth)
                horizontalMargin = max(4, horizontalMargin)
            
            # 九宮格區域的位置分布 - 使用相對計算
            positions = [
                # 上排三個 - 正確對應預覽畫面的上排
                (margin, lockFieldsTopY - fieldHeight),
                (margin + cellWidth + horizontalMargin, lockFieldsTopY - fieldHeight),
                (margin + cellWidth * 2 + horizontalMargin * 2, lockFieldsTopY - fieldHeight),
                
                # 中排左右兩個
                (margin, lockFieldsTopY - fieldHeight * 2 - smallMargin),
                (margin + cellWidth * 2 + horizontalMargin * 2, lockFieldsTopY - fieldHeight * 2 - smallMargin),
                
                # 下排三個 - 正確對應預覽畫面的下排
                (margin, lockFieldsTopY - fieldHeight * 3 - smallMargin * 2),
                (margin + cellWidth + horizontalMargin, lockFieldsTopY - fieldHeight * 3 - smallMargin * 2),
                (margin + cellWidth * 2 + horizontalMargin * 2, lockFieldsTopY - fieldHeight * 3 - smallMargin * 2)
            ]
            
            # 建立八個鎖定字符輸入框
            self.lockFields = {}  # 使用字典保存所有鎖定框的引用
            for i in range(8):
                fieldRect = NSMakeRect(
                    positions[i][0],  # x 座標
                    positions[i][1],  # y 座標
                    cellWidth,  # 寬度
                    fieldHeight  # 高度
                )
                lockField = LockCharacterField.alloc().initWithFrame_position_plugin_(fieldRect, i, plugin)
                
                # 設置額外的樣式以便於輸入 Nice Name
                lockField.setFont_(NSFont.systemFontOfSize_(12.0))
                
                # 設置自動調整掩碼，確保鎖定框跟著上邊緣移動
                lockField.setAutoresizingMask_(NSViewWidthSizable | NSViewMinYMargin)
                
                self.lockFields[i] = lockField
                self.addSubview_(lockField)
                
                # 如果外掛中已有鎖定字符設定，初始化填入
                if hasattr(plugin, 'lockedChars') and plugin.lockedChars and i in plugin.lockedChars:
                    lockField.setStringValue_(plugin.lockedChars[i])
            
            # === 第四部分：長文本輸入框（底部） ===
            
            # 計算長文本輸入框的位置和大小
            searchFieldTopMargin = sectionSpacing  # 與鎖定字符區域底部的間距
            searchFieldBottomMargin = margin  # 與側邊欄底部的間距
            
            # 計算長文本輸入框的位置
            searchFieldTopY = lockFieldsBottomY - searchFieldTopMargin
            searchFieldHeight = searchFieldTopY - searchFieldBottomMargin
            
            # 確保最小高度
            searchFieldHeight = max(40, searchFieldHeight)
            
            # 搜尋欄位 - 位於底部
            searchFieldRect = NSMakeRect(
                margin,  # x 座標
                searchFieldBottomMargin,  # y 座標
                frameWidth - margin * 2,  # 寬度
                searchFieldHeight  # 高度
            )
            self.searchField = CustomTextField.alloc().initWithFrame_plugin_(searchFieldRect, plugin)
            
            placeholder = Glyphs.localize({
                'en': u'Input glyphs or nice names (only nice names need spaces)',
                'zh-Hant': u'輸入字符或 Nice Name（僅 Nice Name 需要空格分隔）',
                'zh-Hans': u'输入字符或 Nice Name（仅 Nice Name 需要空格分隔）',
                'ja': u'文字または Nice Name を入力してください（Nice Name のみスペースが必要）',
                'ko': u'문자 또는 Nice Name을 입력하세요 (Nice Name만 공백 필요)',
            })
            
            self.searchField.setStringValue_(plugin.lastInput)
            self.searchField.setPlaceholderString_(placeholder)
            
            # 設定文本框外觀
            self.searchField.setFont_(NSFont.systemFontOfSize_(12.0))
            self.searchField.setFocusRingType_(NSFocusRingTypeNone)
            self.searchField.setBezeled_(True)
            self.searchField.setEditable_(True)
            
            # 設定為多行文本框
            self.searchField.setUsesSingleLineMode_(False)
            
            # 設定提示
            searchTooltip = Glyphs.localize({
                'en': u'Enter glyphs or nice names (only nice names need spaces)\nRight-click to select glyphs from font',
                'zh-Hant': u'輸入字符或 Nice Name，只有 Nice Name 需要用空格分隔\n右鍵點擊可從字型中選擇字符',
                'zh-Hans': u'输入字符或 Nice Name，只有 Nice Name 需要用空格分隔\n右键点击可从字体中选择字符',
                'ja': u'文字または Nice Name を入力してください（Nice Name のみスペースが必要）\n右クリックでフォントから文字を選択',
                'ko': u'문자 또는 Nice Name을 입력하세요 (Nice Name만 공백 필요)\n마우스 오른쪽 버튼으로 글꼴에서 글자 선택',
            })
            
            self.searchField.setToolTip_(searchTooltip)
            self.searchField.setTarget_(self)
            self.searchField.setAction_("searchFieldAction:")
            
            # 設置自動調整掩碼，使長文本輸入框的寬度和高度都能自動調整
            self.searchField.setAutoresizingMask_(NSViewWidthSizable | NSViewHeightSizable)
            
            self.addSubview_(self.searchField)
        
        return self
    
    def searchFieldAction_(self, sender):
        """處理輸入框的回調函數 / Callback function for the input field"""
        if self.plugin:
            self.plugin.searchFieldCallback(sender)
    
    def updateSearchField(self):
        """更新搜尋欄位文字 / Update search field text"""
        if hasattr(self, 'searchField') and hasattr(self.plugin, 'lastInput'):
            self.searchField.setStringValue_(self.plugin.lastInput)
    
    def updateLockFields(self):
        """更新鎖定字符欄位"""
        if hasattr(self, 'lockFields') and hasattr(self.plugin, 'lockedChars'):
            for i in range(8):
                if i in self.plugin.lockedChars:
                    self.lockFields[i].setStringValue_(self.plugin.lockedChars[i])
                else:
                    self.lockFields[i].setStringValue_("")
    
    def randomizeAction_(self, sender):
        """隨機按鈕點擊事件 / Randomize button click event"""
        if self.plugin:
            self.plugin.randomizeCallback(sender)
            
    def pickGlyphAction_(self, sender):
        """選擇字符按鈕點擊事件 / Pick glyph button click event"""
        if self.plugin:
            self.plugin.pickGlyphCallback(sender)
            
    def actionButtonAction_(self, sender):
        """清空/還原按鈕點擊事件 / Clear/Restore button click event"""
        if self.plugin:
            if self.isInClearMode:
                # 目前是清空模式，執行清空操作
                self.plugin.clearAllLockFieldsCallback(sender)
                # 切換到還原模式
                self.isInClearMode = False
            else:
                # 目前是還原模式，執行還原操作
                self.plugin.restoreAllLockFieldsCallback(sender)
                # 切換到清空模式
                self.isInClearMode = True
            
            # 更新按鈕標題和提示
            self.updateActionButtonTitle()
            self.updateActionButtonTooltip()
    
    def updateActionButtonTitle(self):
        """根據當前模式更新按鈕標題 / Update button title based on current mode"""
        if hasattr(self, 'actionButton'):
            if self.isInClearMode:
                self.actionButton.setTitle_(Glyphs.localize({
                    'en': u'Clear All',
                    'zh-Hant': u'清空全部',
                    'zh-Hans': u'清空全部',
                    'ja': u'すべてクリア',
                    'ko': u'전체 지우기',
                }))
            else:
                self.actionButton.setTitle_(Glyphs.localize({
                    'en': u'Restore',
                    'zh-Hant': u'還原',
                    'zh-Hans': u'还原',
                    'ja': u'復元',
                    'ko': u'복원',
                }))
    
    def updateActionButtonTooltip(self):
        """根據當前模式更新按鈕提示 / Update button tooltip based on current mode"""
        if hasattr(self, 'actionButton'):
            if self.isInClearMode:
                self.actionButton.setToolTip_(Glyphs.localize({
                    'en': u'Clear all locked characters',
                    'zh-Hant': u'清空所有鎖定字符',
                    'zh-Hans': u'清空所有锁定字符',
                    'ja': u'すべてのロックされた文字をクリア',
                    'ko': u'모든 고정된 글자 지우기',
                }))
            else:
                self.actionButton.setToolTip_(Glyphs.localize({
                    'en': u'Restore previous locked characters',
                    'zh-Hant': u'還原上一次的鎖定字符',
                    'zh-Hans': u'还原上一次的锁定字符',
                    'ja': u'前回のロックされた文字を復元',
                    'ko': u'이전 고정된 글자 복원',
                }))
    
    def clearButtonAction_(self, sender):
        """舊版清空按鈕點擊事件（為了向後兼容） / Legacy clear button click event (for backward compatibility)"""
        self.actionButtonAction_(sender)
            
    def restoreButtonAction_(self, sender):
        """舊版還原按鈕點擊事件（為了向後兼容） / Legacy restore button click event (for backward compatibility)"""
        # 先切換到還原模式再執行操作
        self.isInClearMode = False
        self.updateActionButtonTitle()
        self.updateActionButtonTooltip()
        self.actionButtonAction_(sender)
    
    def drawRect_(self, rect):
        """
        繪製側邊欄背景
        Draw the sidebar background
        
        Args:
            rect: 要繪製的矩形區域
        """
        try:
            # 使用系統原生的背景顏色，跟隨系統明暗模式
            NSColor.windowBackgroundColor().set()
            
            NSRectFill(rect)
            
        except Exception as e:
            print(f"繪製側邊欄時發生錯誤: {e}")
            print(traceback.format_exc()) 