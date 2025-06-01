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
    
    def textDidChange_(self, notification):
        """文本變更時的回調函數"""
        try:
            if hasattr(self, 'plugin') and self.plugin:
                # 先保存當前的 sender 對象，用於 updateInterface 判斷來源
                self.plugin.lastSender = self
                
                # 如果有可用的專用函數，則使用它，確保長文本輸入框始終能更新預覽
                if hasattr(self.plugin, 'updateInterfaceForSearchField'):
                    # 使用專用的長文本輸入框更新函數，確保不受鎖頭狀態影響
                    self.plugin.searchFieldCallback(self)
                else:
                    # 向後兼容：使用普通的回調函數
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
            # 獲取當前輸入內容
            input_text = self.stringValue()
            
            # 檢查鎖頭狀態
            is_in_clear_mode = True  # 預設為解鎖狀態 (安全)
            
            if (hasattr(self, 'plugin') and hasattr(self.plugin, 'windowController') and 
                self.plugin.windowController and 
                hasattr(self.plugin.windowController, 'sidebarView') and 
                self.plugin.windowController.sidebarView and 
                hasattr(self.plugin.windowController.sidebarView, 'isInClearMode')):
                
                # 判斷鎖頭狀態 - False = 上鎖狀態（輸入框和預覽關聯）
                # True = 解鎖狀態（輸入框和預覽不關聯）
                is_in_clear_mode = self.plugin.windowController.sidebarView.isInClearMode
                
                # 在解鎖狀態下，直接返回，不處理任何鎖定相關邏輯
                if is_in_clear_mode:
                    print(f"鎖頭處於解鎖狀態 - 忽略鎖定輸入框的變更")
                    return
            else:
                # 如果無法確定鎖頭狀態，為安全起見不做任何處理
                print(f"無法確定鎖頭狀態 - 為安全起見，不處理輸入框變更")
                return
            
            # 只在鎖頭上鎖狀態下執行以下代碼
            
            # 如果輸入為空，直接處理清空事件
            if not input_text:
                # 直接在這裡處理清空邏輯
                if hasattr(self, 'plugin') and hasattr(self.plugin, 'lockedChars'):
                    position = self.position
                    
                    # 從鎖定字典中移除此位置
                    if position in self.plugin.lockedChars:
                        del self.plugin.lockedChars[position]
                        print(f"已移除位置 {position} 的鎖定")
                    
                    # 儲存偏好設定
                    if hasattr(self.plugin, 'savePreferences'):
                        self.plugin.savePreferences()
                    
                    # 更新預覽畫面
                    print(f"鎖頭處於上鎖狀態 - 允許更新預覽畫面")
                    if hasattr(self.plugin, 'updateInterface'):
                        self.plugin.updateInterface(self)
            
            # 調用智能鎖定回調函數
            if hasattr(self, 'plugin') and hasattr(self.plugin, 'smartLockCharacterCallback'):
                self.plugin.smartLockCharacterCallback(self)
        
        except Exception as e:
            print(f"處理鎖定輸入框變更時發生錯誤: {e}")
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
            
            # 追蹤鎖定/解除鎖定按鈕的狀態 (True = 鎖定模式，False = 解除鎖定模式)
            # 根據是否有鎖定的字符來設定初始狀態
            if hasattr(plugin, 'lockedChars') and plugin.lockedChars:
                # 已有鎖定字符，設為解除鎖定模式 (下一步是解除鎖定)
                self.isInClearMode = False
                print("初始化為解除鎖定模式 - 因有鎖定字符")
            else:
                # 沒有鎖定字符，設為鎖定模式 (下一步是鎖定)
                self.isInClearMode = True
                print("初始化為鎖定模式 - 因沒有鎖定字符")
            
            # 設置側邊欄視圖的自動調整掩碼 - 視圖寬度可調整，高度可調整
            self.setAutoresizingMask_(NSViewWidthSizable | NSViewHeightSizable)
            
            # 初始化所有視圖元素
            self.initializeViews()
            
            # 註冊視圖尺寸變更通知
            NSNotificationCenter.defaultCenter().addObserver_selector_name_object_(
                self,
                "viewFrameDidChange:",
                "NSViewFrameDidChangeNotification",
                self
            )
            
            # 確保初始化時按鈕圖示正確顯示
            if hasattr(self, 'actionButton'):
                # 延遲一小段時間確保其他初始化完成後才設置圖示
                self.performSelector_withObject_afterDelay_(
                    "forceUpdateActionButtonImage", 
                    None, 
                    0.1
                )
        
        return self
    
    def initializeViews(self):
        """初始化所有視圖元素並計算它們的布局"""
        # 先移除所有現有子視圖（如果有的話）
        for subview in list(self.subviews()):
            subview.removeFromSuperview()
        
        # === 布局常數設定 ===
        frame = self.frame()
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
        
        # === 第二部分：不再創建按鈕，將在鎖定框中央創建圖示按鈕 ===
        
        # === 第三部分：鎖定字符輸入框 ===
        
        # 計算九宮格區域的頂部位置（直接在標題下方）
        lockFieldsTopY = totalHeight - titleHeight - topMargin - elementSpacing
        
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
            lockField = LockCharacterField.alloc().initWithFrame_position_plugin_(fieldRect, i, self.plugin)
            
            # 設置額外的樣式以便於輸入 Nice Name
            lockField.setFont_(NSFont.systemFontOfSize_(12.0))
            
            # 設置自動調整掩碼，確保鎖定框跟著上邊緣移動
            lockField.setAutoresizingMask_(NSViewWidthSizable | NSViewMinYMargin)
            
            self.lockFields[i] = lockField
            self.addSubview_(lockField)
            
            # 如果外掛中已有鎖定字符設定，初始化填入
            if hasattr(self.plugin, 'lockedChars') and self.plugin.lockedChars and i in self.plugin.lockedChars:
                lockField.setStringValue_(self.plugin.lockedChars[i])
        
        # === 添加鎖頭圖示按鈕在中央位置 ===
        # 計算中央位置
        centerX = margin + cellWidth + horizontalMargin
        centerY = lockFieldsTopY - fieldHeight * 2 - smallMargin
        
        # 設定鎖頭按鈕大小
        lockButtonSize = min(32, max(24, fieldHeight * 1.2))  # 適當大小的按鈕
        
        # 計算按鈕位置 (置中)
        lockButtonX = centerX + (cellWidth - lockButtonSize) / 2
        lockButtonY = centerY + (fieldHeight - lockButtonSize) / 2
        
        # 創建鎖頭按鈕
        lockButtonRect = NSMakeRect(
            lockButtonX,  # x 座標
            lockButtonY,  # y 座標
            lockButtonSize,  # 寬度
            lockButtonSize  # 高度
        )
        
        self.actionButton = NSButton.alloc().initWithFrame_(lockButtonRect)
        self.actionButton.setBezelStyle_(NSBezelStyleRegularSquare)  # 使用方形按鈕樣式
        self.actionButton.setButtonType_(NSButtonTypeMomentaryPushIn)  # 使用瞬時按鈕類型，避免自動切換狀態
        self.actionButton.setBordered_(False)  # 無邊框
        self.actionButton.setTarget_(self)
        self.actionButton.setAction_("actionButtonAction:")
        self.actionButton.setAutoresizingMask_(NSViewMinYMargin)
        self.actionButton.setTitle_("")  # 確保按鈕沒有文字
        
        # 設置鎖頭圖示 (稍後會在 updateActionButtonImage 中設置)
        
        # 設定工具提示
        self.updateActionButtonTooltip()
        
        # 添加到視圖
        self.addSubview_(self.actionButton)
        
        # 立即更新按鈕圖示
        self.updateActionButtonImage()
        
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
        self.searchField = CustomTextField.alloc().initWithFrame_plugin_(searchFieldRect, self.plugin)
        
        placeholder = Glyphs.localize({
            'en': u'Input glyphs or nice names (only nice names need spaces)',
            'zh-Hant': u'輸入字符或 Nice Name（僅 Nice Name 需要空格分隔）',
            'zh-Hans': u'输入字符或 Nice Name（仅 Nice Name 需要空格分隔）',
            'ja': u'文字または Nice Name を入力してください（Nice Name のみスペースが必要）',
            'ko': u'문자 또는 Nice Name을 입력하세요 (Nice Name만 공백 필요)',
        })
        
        self.searchField.setStringValue_(self.plugin.lastInput)
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
    
    def viewFrameDidChange_(self, notification):
        """視圖尺寸變更時重新計算布局"""
        # 延遲執行以避免過於頻繁的更新
        self.performSelector_withObject_afterDelay_("delayedViewFrameDidChange:", None, 0.2)
    
    def delayedViewFrameDidChange_(self, sender):
        """延遲執行的視圖尺寸變更處理"""
        try:
            # 暫存當前鎖定字符和輸入文字
            lockedCharsValues = {}
            if hasattr(self, 'lockFields'):
                for pos, field in self.lockFields.items():
                    lockedCharsValues[pos] = field.stringValue()
            
            # 保存當前按鈕狀態
            currentIsInClearMode = self.isInClearMode if hasattr(self, 'isInClearMode') else True
            
            # 保存搜索欄位值
            searchFieldValue = ""
            if hasattr(self, 'searchField'):
                searchFieldValue = self.searchField.stringValue()
            
            # 重新初始化視圖
            self.initializeViews()
            
            # 恢復按鈕狀態
            self.isInClearMode = currentIsInClearMode
            print(f"視窗重繪後恢復按鈕狀態: {'鎖定模式' if self.isInClearMode else '解除鎖定模式'}")
            
            # 恢復暫存的值
            if hasattr(self, 'lockFields'):
                for pos, value in lockedCharsValues.items():
                    if pos in self.lockFields:
                        self.lockFields[pos].setStringValue_(value)
            
            if hasattr(self, 'searchField'):
                self.searchField.setStringValue_(searchFieldValue)
            
            # 確保按鈕圖示正確
            if hasattr(self, 'actionButton'):
                self.forceUpdateActionButtonImage()
            
        except Exception as e:
            print(f"視圖尺寸變更處理時發生錯誤: {e}")
            print(traceback.format_exc())
    
    def dealloc(self):
        """釋放資源"""
        # 移除通知觀察者
        NSNotificationCenter.defaultCenter().removeObserver_(self)
        objc.super(SidebarView, self).dealloc()
    
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
    
    def randomizeAction_(self, sender):
        """隨機按鈕點擊事件 / Randomize button click event"""
        if self.plugin:
            self.plugin.randomizeCallback(sender)
            
    def pickGlyphAction_(self, sender):
        """選擇字符按鈕點擊事件 / Pick glyph button click event"""
        if self.plugin:
            self.plugin.pickGlyphCallback(sender)
            
    def actionButtonAction_(self, sender):
        """鎖定/解除鎖定按鈕點擊事件 / Lock/Unlock button click event"""
        if self.plugin:
            # 記錄動作開始
            print("------ 按鈕點擊開始 ------")
            
            # 保存變更前的狀態，用於後續判斷
            previousState = self.isInClearMode
            
            # 根據當前狀態執行相應操作
            if self.isInClearMode:
                # 目前是解鎖模式，執行鎖定操作
                print("執行操作: 鎖定全部")
                self.plugin.clearAllLockFieldsCallback(sender)
                # 切換到上鎖模式
                self.isInClearMode = False
            else:
                # 目前是上鎖模式，執行解除鎖定操作
                print("執行操作: 解除鎖定")
                self.plugin.restoreAllLockFieldsCallback(sender)
                # 切換到解鎖模式
                self.isInClearMode = True
                
                # 在切換到解鎖模式後，進行一次完全隨機的字符排列
                if hasattr(self.plugin, 'selectedChars') and self.plugin.selectedChars:
                    print("切換到解鎖模式：進行一次完全隨機的字符排列")
                    
                    # 直接調用隨機排列函數，強制忽略鎖定狀態
                    if hasattr(self.plugin, 'randomizeCallback'):
                        self.plugin.randomizeCallback(sender)
                    
            # 更新按鈕狀態和文字
            self.updateButtonAppearance()
            
            # 特殊處理：狀態從解鎖變為上鎖時，強制更新預覽畫面一次
            if previousState and not self.isInClearMode:  # 從 True (解鎖) 變為 False (上鎖)
                print("特殊處理：狀態從解鎖變為上鎖，強制更新預覽畫面")
                if hasattr(self.plugin, 'windowController') and self.plugin.windowController:
                    if hasattr(self.plugin.windowController, 'redrawIgnoreLockState'):
                        self.plugin.windowController.redrawIgnoreLockState()
            
            # 記錄動作結束
            print(f"------ 按鈕點擊結束：當前狀態 = {'解鎖' if self.isInClearMode else '上鎖'} ------")
            
    def forceUpdateActionButtonImage(self):
        """強制更新按鈕圖示，確保顯示正確"""
        if hasattr(self, 'actionButton'):
            # 根據當前狀態確定應該顯示的圖示
            is_locked = not self.isInClearMode  # True = 顯示鎖定圖示, False = 顯示解鎖圖示
            
            print(f"強制更新圖示: {'鎖定圖示' if is_locked else '解鎖圖示'}")
            
            # 創建對應的圖示
            lockImage = self.createLockImage(is_locked)
            
            if lockImage:
                # 設置圖示
                self.actionButton.setImage_(lockImage)
                self.actionButton.setImagePosition_(NSImageOnly)
                
                # 不設置替代圖示，避免系統自動切換
                # self.actionButton.setAlternateImage_(None)
                
                # 強制重繪
                self.actionButton.setNeedsDisplay_(True)
    
    def updateActionButtonImage(self):
        """更新按鈕圖示"""
        # 轉發到強制更新方法，確保一致性
        self.forceUpdateActionButtonImage()
    
    def updateActionButtonTooltip(self):
        """根據當前模式更新按鈕提示 / Update button tooltip based on current mode"""
        if hasattr(self, 'actionButton'):
            if self.isInClearMode:
                self.actionButton.setToolTip_(Glyphs.localize({
                    'en': u'Lock all characters in input fields',
                    'zh-Hant': u'鎖定所有輸入框中的字符',
                    'zh-Hans': u'锁定所有输入框中的字符',
                    'ja': u'入力フィールド内のすべての文字をロック',
                    'ko': u'입력 필드의 모든 글자 잠금',
                }))
            else:
                self.actionButton.setToolTip_(Glyphs.localize({
                    'en': u'Unlock all characters',
                    'zh-Hant': u'解除所有字符的鎖定',
                    'zh-Hans': u'解除所有字符的锁定',
                    'ja': u'すべての文字のロックを解除',
                    'ko': u'모든 글자 잠금 해제',
                }))
    
    def clearButtonAction_(self, sender):
        """舊版鎖定按鈕點擊事件（為了向後兼容） / Legacy lock button click event (for backward compatibility)"""
        self.actionButtonAction_(sender)
            
    def restoreButtonAction_(self, sender):
        """舊版解除鎖定按鈕點擊事件（為了向後兼容） / Legacy unlock button click event (for backward compatibility)"""
        # 先切換到解除鎖定模式再執行操作
        self.isInClearMode = False
        self.updateActionButtonImage()
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

    def updateActionButtonTitle(self):
        """已不再使用，保留向後兼容"""
        # 改為調用圖示更新方法
        self.updateActionButtonImage() 

    def createLockImage(self, locked=True):
        """
        創建自定義鎖頭圖示，使用Unicode符號確保顯示正確
        
        Args:
            locked: 是否為鎖定狀態
            
        Returns:
            NSImage: 鎖頭圖示
        """
        # 設定圖像大小，確保留有足夠邊距
        imageSize = 22
        
        # 創建空白圖像
        lockImage = NSImage.alloc().initWithSize_((imageSize, imageSize))
        
        # 開始編輯圖像
        lockImage.lockFocus()
        
        try:
            # 清除背景 (透明)
            NSColor.clearColor().set()
            NSBezierPath.fillRect_(((0, 0), (imageSize, imageSize)))
            
            # 設定文字屬性 - 使用稍小一點的字體確保不會被切掉
            fontSize = 14.0
            font = NSFont.systemFontOfSize_(fontSize)
            attrs = {
                NSFontAttributeName: font, 
                NSForegroundColorAttributeName: NSColor.controlTextColor()
            }
            
            # 使用Unicode符號 - 開源且跨平台
            if locked:
                # 鎖定符號 - 可選多種Unicode鎖頭
                symbol = "🔒"  # 標準鎖頭
                # 其他備選："\u{1F512}" (🔒) 或 "\u{1F510}" (🔐)
            else:
                # 解鎖符號 - 可選多種Unicode解鎖
                symbol = "🔓"  # 標準開鎖
                # 其他備選："\u{1F513}" (🔓)
            
            # 創建文字並計算尺寸
            string = NSString.stringWithString_(symbol)
            stringSize = string.sizeWithAttributes_(attrs)
            
            # 計算居中位置，確保完全在繪製範圍內
            x = (imageSize - stringSize.width) / 2
            y = (imageSize - stringSize.height) / 2
            
            # 確保座標是正數且不超出邊界
            x = max(1, min(x, imageSize - stringSize.width - 1))
            y = max(1, min(y, imageSize - stringSize.height - 1))
            
            # 繪製符號
            string.drawAtPoint_withAttributes_(NSMakePoint(x, y), attrs)
            
            # 輸出調試信息
            print(f"已使用Unicode符號創建{'鎖定' if locked else '解鎖'}圖示：{symbol}")
            
        except Exception as e:
            print(f"創建鎖頭圖示時發生錯誤: {e}")
            print(traceback.format_exc())
            
            # 如果Unicode方法失敗，嘗試使用NSImage
            try:
                # 在macOS上嘗試使用系統提供的圖示
                systemIcon = None
                
                if locked:
                    # 嘗試幾種可能的系統鎖定圖示名稱
                    for iconName in ["NSLockLockedTemplate", "lockLocked", "lock"]:
                        systemIcon = NSImage.imageNamed_(iconName)
                        if systemIcon:
                            break
                else:
                    # 嘗試幾種可能的系統解鎖圖示名稱
                    for iconName in ["NSLockUnlockedTemplate", "lockUnlocked", "unlock"]:
                        systemIcon = NSImage.imageNamed_(iconName)
                        if systemIcon:
                            break
                
                # 如果找到系統圖示，使用它
                if systemIcon:
                    # 清除當前繪製
                    lockImage.unlockFocus()
                    
                    # 創建新圖像並繪製系統圖示
                    newImage = NSImage.alloc().initWithSize_((imageSize, imageSize))
                    newImage.lockFocus()
                    
                    # 清除背景
                    NSColor.clearColor().set()
                    NSBezierPath.fillRect_(((0, 0), (imageSize, imageSize)))
                    
                    # 計算居中位置
                    srcWidth = systemIcon.size().width
                    srcHeight = systemIcon.size().height
                    
                    # 確保不超出邊界的縮放比例
                    scale = min((imageSize - 4) / srcWidth, (imageSize - 4) / srcHeight)
                    
                    destWidth = srcWidth * scale
                    destHeight = srcHeight * scale
                    
                    destX = (imageSize - destWidth) / 2
                    destY = (imageSize - destHeight) / 2
                    
                    # 繪製系統圖示
                    systemIcon.drawInRect_fromRect_operation_fraction_(
                        NSMakeRect(destX, destY, destWidth, destHeight),
                        NSMakeRect(0, 0, srcWidth, srcHeight),
                        NSCompositingOperationSourceOver,
                        1.0
                    )
                    
                    newImage.unlockFocus()
                    
                    # 設置為模板圖像以支援暗色模式
                    newImage.setTemplate_(True)
                    
                    print(f"已使用系統圖示創建{'鎖定' if locked else '解鎖'}圖示: {iconName}")
                    return newImage
            except:
                pass
            
        finally:
            # 結束編輯
            lockImage.unlockFocus()
        
        # 設置為模板圖像以支援暗色模式
        lockImage.setTemplate_(True)
        
        return lockImage 

    def updateButtonAppearance(self):
        """更新按鈕外觀和提示文字 / Update button appearance and tooltip"""
        # 更新按鈕圖示
        self.forceUpdateActionButtonImage()
        
        # 更新提示文字
        self.updateActionButtonTooltip() 