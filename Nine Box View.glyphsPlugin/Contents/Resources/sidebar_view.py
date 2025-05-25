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
    NSApp, NSViewWidthSizable, NSViewHeightSizable, NSViewMinYMargin, NSViewMaxYMargin
)

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
            
            # 設置側邊欄視圖的自動調整掩碼 - 視圖寬度可調整，高度可調整
            self.setAutoresizingMask_(NSViewWidthSizable | NSViewHeightSizable)
            
            # 視圖內部元素的常數設定
            margin = 10
            controlHeight = 25
            labelHeight = 20
            buttonHeight = 30
            totalHeight = frame.size.height
            frameWidth = frame.size.width
            
            # === 頂部區域（固定在頂部）===
            topSectionHeight = 130  # 標題 + 搜尋標籤 + 搜尋框的高度和間距
            
            # 創建頂部容器視圖
            topSectionRect = NSMakeRect(0, totalHeight - topSectionHeight, frameWidth, topSectionHeight)
            self.topSectionView = NSView.alloc().initWithFrame_(topSectionRect)
            self.topSectionView.setAutoresizingMask_(NSViewWidthSizable | NSViewMaxYMargin)
            self.addSubview_(self.topSectionView)
            
            # 設定標題標籤
            titleRect = NSMakeRect(margin, topSectionHeight - labelHeight - margin, frameWidth - margin * 2, labelHeight)
            self.titleLabel = NSTextField.alloc().initWithFrame_(titleRect)
            self.titleLabel.setEditable_(False)
            self.titleLabel.setBordered_(False)
            self.titleLabel.setDrawsBackground_(False)
            self.titleLabel.setFont_(NSFont.boldSystemFontOfSize_(14))
            self.titleLabel.setAlignment_(NSCenterTextAlignment)
            self.titleLabel.setStringValue_("工具面板")
            self.titleLabel.setAutoresizingMask_(NSViewWidthSizable)
            self.topSectionView.addSubview_(self.titleLabel)
            
            # 搜尋標籤
            searchLabelRect = NSMakeRect(margin, topSectionHeight - labelHeight * 2 - margin - 5, frameWidth - margin * 2, labelHeight)
            self.searchLabel = NSTextField.alloc().initWithFrame_(searchLabelRect)
            self.searchLabel.setEditable_(False)
            self.searchLabel.setBordered_(False)
            self.searchLabel.setDrawsBackground_(False)
            self.searchLabel.setFont_(NSFont.boldSystemFontOfSize_(12))
            self.searchLabel.setStringValue_("搜尋字符:")
            self.searchLabel.setAutoresizingMask_(NSViewWidthSizable)
            self.topSectionView.addSubview_(self.searchLabel)
            
            # 搜尋欄位
            searchFieldRect = NSMakeRect(margin, topSectionHeight - labelHeight * 2 - margin - controlHeight - 10, frameWidth - margin * 2, controlHeight)
            self.searchField = NSSearchField.alloc().initWithFrame_(searchFieldRect)
            
            placeholder = Glyphs.localize({
                'en': u'Input glyphs (space-separated)',
                'zh-Hant': u'輸入字符（以空格分隔）',
                'zh-Hans': u'输入字符（用空格分隔）',
                'ja': u'文字を入力してください（スペースで区切る）',
                'ko': u'문자를 입력하세요 (공백으로 구분)',
            })
            
            self.searchField.setStringValue_(plugin.lastInput)
            self.searchField.setPlaceholderString_(placeholder)
            
            # 設定搜尋欄位外觀
            self.searchField.setFont_(NSFont.systemFontOfSize_(12.0))
            self.searchField.setFocusRingType_(NSFocusRingTypeNone)
            
            # 設定搜尋欄位提示
            searchTooltip = Glyphs.localize({
                'en': u'Enter glyphs to display around the selected glyph',
                'zh-Hant': u'輸入要在選定字符周圍顯示的字符',
                'zh-Hans': u'输入要在选定字符周围显示的字符',
                'ja': u'選択された文字の周りに表示する文字を入力してください',
                'ko': u'선택한 글자 주변에 표시할 글자를 입력하세요',
            })
            
            self.searchField.setToolTip_(searchTooltip)
            self.searchField.setTarget_(self)
            self.searchField.setAction_("searchFieldAction:")
            self.searchField.setAutoresizingMask_(NSViewWidthSizable)
            self.topSectionView.addSubview_(self.searchField)
            
            # === 底部區域（固定在底部）===
            bottomSectionHeight = 100  # 字型資訊的高度和間距
            
            # 創建底部容器視圖
            bottomSectionRect = NSMakeRect(0, 0, frameWidth, bottomSectionHeight)
            self.bottomSectionView = NSView.alloc().initWithFrame_(bottomSectionRect)
            self.bottomSectionView.setAutoresizingMask_(NSViewWidthSizable | NSViewMinYMargin)
            self.addSubview_(self.bottomSectionView)
            
            # 字型資訊標籤
            fontSectionLabelRect = NSMakeRect(margin, bottomSectionHeight - labelHeight - margin, frameWidth - margin * 2, labelHeight)
            self.fontSectionLabel = NSTextField.alloc().initWithFrame_(fontSectionLabelRect)
            self.fontSectionLabel.setEditable_(False)
            self.fontSectionLabel.setBordered_(False)
            self.fontSectionLabel.setDrawsBackground_(False)
            self.fontSectionLabel.setFont_(NSFont.boldSystemFontOfSize_(12))
            self.fontSectionLabel.setStringValue_("字型資訊:")
            self.fontSectionLabel.setAutoresizingMask_(NSViewWidthSizable)
            self.bottomSectionView.addSubview_(self.fontSectionLabel)
            
            # 資訊標籤
            infoHeight = 60
            infoRect = NSMakeRect(margin, margin, frameWidth - margin * 2, infoHeight)
            self.infoLabel = NSTextField.alloc().initWithFrame_(infoRect)
            self.infoLabel.setEditable_(False)
            self.infoLabel.setBordered_(False)
            self.infoLabel.setDrawsBackground_(False)
            self.infoLabel.setFont_(NSFont.systemFontOfSize_(12))
            self.infoLabel.setAutoresizingMask_(NSViewWidthSizable)
            self.updateFontInfo()
            self.bottomSectionView.addSubview_(self.infoLabel)
            
            # === 中間區域（可伸縮）===
            middleSectionHeight = totalHeight - topSectionHeight - bottomSectionHeight
            
            # 創建中間容器視圖
            middleSectionRect = NSMakeRect(0, bottomSectionHeight, frameWidth, middleSectionHeight)
            self.middleSectionView = NSView.alloc().initWithFrame_(middleSectionRect)
            # 中間區域在垂直方向上可以調整高度，固定在底部，頂部可變
            self.middleSectionView.setAutoresizingMask_(NSViewWidthSizable | NSViewHeightSizable | NSViewMinYMargin)
            self.addSubview_(self.middleSectionView)
            
            # 計算中間區域各按鈕的位置
            middleMargin = 15
            buttonSpacing = 20
            buttonAreaHeight = middleSectionHeight - middleMargin * 2
            buttonsStartY = buttonAreaHeight - buttonHeight
            
            buttonWidth = (frameWidth - margin * 3) / 2
            
            # 選擇字符按鈕
            pickButtonRect = NSMakeRect(margin, buttonsStartY, buttonWidth, buttonHeight)
            self.pickButton = NSButton.alloc().initWithFrame_(pickButtonRect)
            self.pickButton.setTitle_("選擇字符 🔣")
            self.pickButton.setBezelStyle_(NSTexturedRoundedBezelStyle)
            self.pickButton.setButtonType_(NSButtonTypeMomentaryPushIn)
            self.pickButton.setTarget_(self)
            self.pickButton.setAction_("pickGlyphAction:")
            
            # 設定選擇字符按鈕提示
            pickTooltip = Glyphs.localize({
                'en': u'Select glyphs from the font',
                'zh-Hant': u'從字型中選擇字符',
                'zh-Hans': u'从字体中选择字符',
                'ja': u'フォントから文字を選択',
                'ko': u'폰트에서 글자 선택',
            })
            
            self.pickButton.setToolTip_(pickTooltip)
            self.pickButton.setAutoresizingMask_(NSViewWidthSizable)
            self.middleSectionView.addSubview_(self.pickButton)
            
            # 隨機排列按鈕
            randomizeButtonRect = NSMakeRect(margin * 2 + buttonWidth, buttonsStartY, buttonWidth, buttonHeight)
            self.randomizeButton = NSButton.alloc().initWithFrame_(randomizeButtonRect)
            self.randomizeButton.setTitle_("隨機排列 🔄")
            self.randomizeButton.setBezelStyle_(NSTexturedRoundedBezelStyle)
            self.randomizeButton.setButtonType_(NSButtonTypeMomentaryPushIn)
            self.randomizeButton.setTarget_(self)
            self.randomizeButton.setAction_("randomizeAction:")
            
            # 設定隨機排列按鈕提示
            randomizeTooltip = Glyphs.localize({
                'en': u'Randomize character arrangement',
                'zh-Hant': u'隨機排列字符',
                'zh-Hans': u'随机排列字符',
                'ja': u'文字の配置をランダム化',
                'ko': u'문자 배열 무작위화',
            })
            
            self.randomizeButton.setToolTip_(randomizeTooltip)
            self.randomizeButton.setAutoresizingMask_(NSViewWidthSizable)
            self.middleSectionView.addSubview_(self.randomizeButton)
            
            # === 顯示設定區塊 ===
            sectionLabelRect = NSMakeRect(margin, buttonsStartY - buttonSpacing - labelHeight, frameWidth - margin * 2, labelHeight)
            self.sectionLabel = NSTextField.alloc().initWithFrame_(sectionLabelRect)
            self.sectionLabel.setEditable_(False)
            self.sectionLabel.setBordered_(False)
            self.sectionLabel.setDrawsBackground_(False)
            self.sectionLabel.setFont_(NSFont.boldSystemFontOfSize_(12))
            self.sectionLabel.setStringValue_("顯示設定:")
            self.sectionLabel.setAutoresizingMask_(NSViewWidthSizable)
            self.middleSectionView.addSubview_(self.sectionLabel)
            
            # 重設縮放按鈕
            resetZoomButtonRect = NSMakeRect(margin, buttonsStartY - buttonSpacing - labelHeight - buttonHeight - 5, frameWidth - margin * 2, buttonHeight)
            self.resetZoomButton = NSButton.alloc().initWithFrame_(resetZoomButtonRect)
            self.resetZoomButton.setTitle_("重設縮放 🔍")
            self.resetZoomButton.setBezelStyle_(NSTexturedRoundedBezelStyle)
            self.resetZoomButton.setButtonType_(NSButtonTypeMomentaryPushIn)
            self.resetZoomButton.setTarget_(self)
            self.resetZoomButton.setAction_("resetZoomAction:")
            
            # 設定重設縮放按鈕提示
            resetZoomTooltip = Glyphs.localize({
                'en': u'Reset zoom to default',
                'zh-Hant': u'重設縮放至預設值',
                'zh-Hans': u'重置缩放到默认值',
                'ja': u'ズームをリセット',
                'ko': u'확대/축소 초기화',
            })
            
            self.resetZoomButton.setToolTip_(resetZoomTooltip)
            self.resetZoomButton.setAutoresizingMask_(NSViewWidthSizable)
            self.middleSectionView.addSubview_(self.resetZoomButton)
            
        return self
    
    def searchFieldAction_(self, sender):
        """搜尋欄位動作"""
        try:
            self.plugin.searchFieldCallback(sender)
        except Exception as e:
            print(f"處理搜尋欄位動作時發生錯誤: {e}")
            print(traceback.format_exc())
    
    def pickGlyphAction_(self, sender):
        """選擇字符按鈕動作"""
        try:
            self.plugin.pickGlyphCallback(sender)
        except Exception as e:
            print(f"處理選擇字符按鈕動作時發生錯誤: {e}")
            print(traceback.format_exc())
    
    def randomizeAction_(self, sender):
        """隨機排列按鈕動作"""
        try:
            self.plugin.randomizeCallback(sender)
        except Exception as e:
            print(f"處理隨機排列按鈕動作時發生錯誤: {e}")
            print(traceback.format_exc())
    
    def resetZoomAction_(self, sender):
        """重設縮放按鈕動作"""
        try:
            self.plugin.resetZoom(sender)
        except Exception as e:
            print(f"處理重設縮放按鈕動作時發生錯誤: {e}")
            print(traceback.format_exc())
    
    def updateFontInfo(self):
        """更新字型資訊顯示"""
        try:
            if Glyphs.font:
                fontName = Glyphs.font.familyName
                glyphCount = len(Glyphs.font.glyphs)
                masterName = Glyphs.font.selectedFontMaster.name if Glyphs.font.selectedFontMaster else "無"
                currentGlyph = Glyphs.font.selectedLayers[0].parent.name if Glyphs.font.selectedLayers else "無"
                
                # 限制資訊字串長度以避免超出顯示區域
                if fontName and len(fontName) > 20:
                    fontName = fontName[:17] + "..."
                if masterName and len(masterName) > 20:
                    masterName = masterName[:17] + "..."
                if currentGlyph and len(currentGlyph) > 20:
                    currentGlyph = currentGlyph[:17] + "..."
                
                info = f"字型: {fontName}\n字符數: {glyphCount}\n主板: {masterName}\n當前字符: {currentGlyph}"
                self.infoLabel.setStringValue_(info)
            else:
                self.infoLabel.setStringValue_("未載入字型")
                
            # 確保字體大小適合目前的顯示區域
            labelFrame = self.infoLabel.frame()
            if labelFrame.size.height < 40:  # 如果高度太小
                self.infoLabel.setFont_(NSFont.systemFontOfSize_(10.0))  # 使用較小的字體
            else:
                self.infoLabel.setFont_(NSFont.systemFontOfSize_(12.0))  # 使用標準字體大小
                
        except Exception as e:
            print(f"更新字型資訊錯誤: {e}")
            print(traceback.format_exc())
    
    def updateSearchField(self):
        """更新搜尋欄位內容"""
        try:
            if hasattr(self, 'searchField') and self.plugin.lastInput is not None:
                self.searchField.setStringValue_(self.plugin.lastInput)
        except Exception as e:
            print(f"更新搜尋欄位錯誤: {e}")
            print(traceback.format_exc())
    
    def drawRect_(self, rect):
        """
        繪製側邊欄內容
        Draw the content of the sidebar
        
        Args:
            rect: 要繪製的矩形區域
        """
        try:
            # 設定背景顏色 - 使用系統深淺色模式設定，而不是跟隨預覽面板
            # 使用 effectiveAppearance 檢查系統暗色模式
            is_dark = "Dark" in str(NSApp.effectiveAppearance().name())
            
            # 不再使用 GSPreview_Black 設定
            # is_black = NSUserDefaults.standardUserDefaults().boolForKey_("GSPreview_Black")
            
            if is_dark:
                NSColor.colorWithCalibratedWhite_alpha_(0.15, 1.0).set()
            else:
                NSColor.colorWithCalibratedWhite_alpha_(0.9, 1.0).set()
            
            NSRectFill(rect)
            
            # 繪製分隔線
            if is_dark:
                NSColor.colorWithCalibratedWhite_alpha_(0.3, 1.0).set()
            else:
                NSColor.colorWithCalibratedWhite_alpha_(0.7, 1.0).set()
                
            separatorPath = NSBezierPath.bezierPath()
            separatorPath.moveToPoint_(NSMakePoint(0, rect.size.height))
            separatorPath.lineToPoint_(NSMakePoint(0, 0))
            separatorPath.setLineWidth_(1.0)
            separatorPath.stroke()
            
            # 根據模式設定文字顏色
            textColor = NSColor.whiteColor() if is_dark else NSColor.blackColor()
            
            # 直接設定每個文字控制項的顏色，避免使用 __name__ 屬性
            if hasattr(self, 'titleLabel') and self.titleLabel:
                self.titleLabel.setTextColor_(textColor)
                
            if hasattr(self, 'searchLabel') and self.searchLabel:
                self.searchLabel.setTextColor_(textColor)
                
            if hasattr(self, 'infoLabel') and self.infoLabel:
                self.infoLabel.setTextColor_(textColor)
                
            if hasattr(self, 'sectionLabel') and self.sectionLabel:
                self.sectionLabel.setTextColor_(textColor)
                
            if hasattr(self, 'fontSectionLabel') and self.fontSectionLabel:
                self.fontSectionLabel.setTextColor_(textColor)
            
            # 確保三個區域的大小正確
            if hasattr(self, 'topSectionView') and self.topSectionView and hasattr(self, 'bottomSectionView') and self.bottomSectionView and hasattr(self, 'middleSectionView') and self.middleSectionView:
                # 獲取當前總高度
                totalHeight = rect.size.height
                frameWidth = rect.size.width
                
                # 頂部和底部區域高度固定
                topSectionHeight = 130
                bottomSectionHeight = 100
                
                # 中間區域高度自適應
                middleSectionHeight = max(20, totalHeight - topSectionHeight - bottomSectionHeight)
                
                # 更新各區域位置和大小
                self.topSectionView.setFrame_(NSMakeRect(0, totalHeight - topSectionHeight, frameWidth, topSectionHeight))
                self.bottomSectionView.setFrame_(NSMakeRect(0, 0, frameWidth, bottomSectionHeight))
                self.middleSectionView.setFrame_(NSMakeRect(0, bottomSectionHeight, frameWidth, middleSectionHeight))
            
            # 根據窗口大小變化調整中間區域
            self._adjustMiddleSectionLayout()
            
        except Exception as e:
            print(f"繪製側邊欄時發生錯誤: {e}")
            print(traceback.format_exc())
            
    def _adjustMiddleSectionLayout(self):
        """根據當前窗口大小調整中間區域的佈局"""
        try:
            if hasattr(self, 'middleSectionView') and self.middleSectionView:
                # 獲取中間區域的當前高度
                middleHeight = self.middleSectionView.frame().size.height
                frameWidth = self.middleSectionView.frame().size.width
                margin = 10
                
                # 根據可用高度調整按鈕的布局
                if middleHeight < 120:  # 當空間非常有限時
                    # 最小化模式 - 只顯示兩個主要按鈕並排
                    buttonHeight = min(30, middleHeight / 2)  # 按鈕高度不超過可用空間的一半
                    buttonWidth = (frameWidth - margin * 3) / 2
                    
                    # 重新定位兩個主要按鈕
                    if hasattr(self, 'pickButton'):
                        self.pickButton.setFrame_(NSMakeRect(margin, middleHeight - buttonHeight - margin, buttonWidth, buttonHeight))
                    
                    if hasattr(self, 'randomizeButton'):
                        self.randomizeButton.setFrame_(NSMakeRect(margin * 2 + buttonWidth, middleHeight - buttonHeight - margin, buttonWidth, buttonHeight))
                    
                    # 設定區域和重設縮放按鈕可能會隱藏
                    if hasattr(self, 'sectionLabel'):
                        self.sectionLabel.setHidden_(True)
                    
                    if hasattr(self, 'resetZoomButton'):
                        self.resetZoomButton.setHidden_(True)
                        
                elif middleHeight < 180:  # 中等空間
                    # 顯示所有元素，但布局更緊湊
                    buttonHeight = 25  # 減小按鈕高度
                    buttonWidth = (frameWidth - margin * 3) / 2
                    buttonSpacing = 10  # 減小間距
                    
                    # 重新定位按鈕和標籤
                    if hasattr(self, 'pickButton'):
                        self.pickButton.setFrame_(NSMakeRect(margin, middleHeight - buttonHeight - margin, buttonWidth, buttonHeight))
                        self.pickButton.setHidden_(False)
                    
                    if hasattr(self, 'randomizeButton'):
                        self.randomizeButton.setFrame_(NSMakeRect(margin * 2 + buttonWidth, middleHeight - buttonHeight - margin, buttonWidth, buttonHeight))
                        self.randomizeButton.setHidden_(False)
                    
                    if hasattr(self, 'sectionLabel'):
                        self.sectionLabel.setFrame_(NSMakeRect(margin, middleHeight - buttonHeight - margin * 2 - 20, frameWidth - margin * 2, 20))
                        self.sectionLabel.setHidden_(False)
                    
                    if hasattr(self, 'resetZoomButton'):
                        self.resetZoomButton.setFrame_(NSMakeRect(margin, 10, frameWidth - margin * 2, buttonHeight))
                        self.resetZoomButton.setHidden_(False)
                
                else:  # 充足的空間
                    # 完整布局，元素間距較大
                    buttonHeight = 30
                    buttonWidth = (frameWidth - margin * 3) / 2
                    buttonSpacing = 20
                    buttonsStartY = middleHeight - buttonHeight - margin
                    
                    # 重新定位所有元素
                    if hasattr(self, 'pickButton'):
                        self.pickButton.setFrame_(NSMakeRect(margin, buttonsStartY, buttonWidth, buttonHeight))
                        self.pickButton.setHidden_(False)
                    
                    if hasattr(self, 'randomizeButton'):
                        self.randomizeButton.setFrame_(NSMakeRect(margin * 2 + buttonWidth, buttonsStartY, buttonWidth, buttonHeight))
                        self.randomizeButton.setHidden_(False)
                    
                    if hasattr(self, 'sectionLabel'):
                        self.sectionLabel.setFrame_(NSMakeRect(margin, buttonsStartY - buttonSpacing - 20, frameWidth - margin * 2, 20))
                        self.sectionLabel.setHidden_(False)
                    
                    if hasattr(self, 'resetZoomButton'):
                        self.resetZoomButton.setFrame_(NSMakeRect(margin, buttonsStartY - buttonSpacing - 20 - buttonHeight - 5, frameWidth - margin * 2, buttonHeight))
                        self.resetZoomButton.setHidden_(False)
                
        except Exception as e:
            print(f"調整中間區域佈局時發生錯誤: {e}")
            print(traceback.format_exc()) 