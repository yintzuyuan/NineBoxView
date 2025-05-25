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
    NSApp
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
            
            # 設定標題標籤
            titleRect = NSMakeRect(10, frame.size.height - 40, frame.size.width - 20, 30)
            self.titleLabel = NSTextField.alloc().initWithFrame_(titleRect)
            self.titleLabel.setEditable_(False)
            self.titleLabel.setBordered_(False)
            self.titleLabel.setDrawsBackground_(False)
            self.titleLabel.setFont_(NSFont.boldSystemFontOfSize_(14))
            self.titleLabel.setAlignment_(NSCenterTextAlignment)
            self.titleLabel.setStringValue_("工具面板")
            self.addSubview_(self.titleLabel)
            
            # === 搜尋字符區塊 ===
            # 搜尋標籤
            searchLabelRect = NSMakeRect(10, frame.size.height - 80, frame.size.width - 20, 20)
            self.searchLabel = NSTextField.alloc().initWithFrame_(searchLabelRect)
            self.searchLabel.setEditable_(False)
            self.searchLabel.setBordered_(False)
            self.searchLabel.setDrawsBackground_(False)
            self.searchLabel.setFont_(NSFont.boldSystemFontOfSize_(12))
            self.searchLabel.setStringValue_("搜尋字符:")
            self.addSubview_(self.searchLabel)

            # 搜尋欄位
            searchFieldRect = NSMakeRect(10, frame.size.height - 105, frame.size.width - 20, 22)
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
            self.addSubview_(self.searchField)
            
            # 選擇字符按鈕
            pickButtonRect = NSMakeRect(10, frame.size.height - 140, (frame.size.width - 25) / 2, 30)
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
            self.addSubview_(self.pickButton)
            
            # 隨機排列按鈕
            randomizeButtonRect = NSMakeRect(frame.size.width / 2 + 5, frame.size.height - 140, (frame.size.width - 25) / 2, 30)
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
            self.addSubview_(self.randomizeButton)
            
            # === 顯示設定區塊 ===
            sectionLabelRect = NSMakeRect(10, frame.size.height - 180, frame.size.width - 20, 20)
            self.sectionLabel = NSTextField.alloc().initWithFrame_(sectionLabelRect)
            self.sectionLabel.setEditable_(False)
            self.sectionLabel.setBordered_(False)
            self.sectionLabel.setDrawsBackground_(False)
            self.sectionLabel.setFont_(NSFont.boldSystemFontOfSize_(12))
            self.sectionLabel.setStringValue_("顯示設定:")
            self.addSubview_(self.sectionLabel)
            
            # 重設縮放按鈕
            resetZoomButtonRect = NSMakeRect(10, frame.size.height - 210, frame.size.width - 20, 30)
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
            self.addSubview_(self.resetZoomButton)
            
            # === 字型資訊區塊 ===
            fontSectionLabelRect = NSMakeRect(10, frame.size.height - 250, frame.size.width - 20, 20)
            self.fontSectionLabel = NSTextField.alloc().initWithFrame_(fontSectionLabelRect)
            self.fontSectionLabel.setEditable_(False)
            self.fontSectionLabel.setBordered_(False)
            self.fontSectionLabel.setDrawsBackground_(False)
            self.fontSectionLabel.setFont_(NSFont.boldSystemFontOfSize_(12))
            self.fontSectionLabel.setStringValue_("字型資訊:")
            self.addSubview_(self.fontSectionLabel)
            
            infoRect = NSMakeRect(10, frame.size.height - 320, frame.size.width - 20, 60)
            self.infoLabel = NSTextField.alloc().initWithFrame_(infoRect)
            self.infoLabel.setEditable_(False)
            self.infoLabel.setBordered_(False)
            self.infoLabel.setDrawsBackground_(False)
            self.infoLabel.setFont_(NSFont.systemFontOfSize_(12))
            self.updateFontInfo()
            self.addSubview_(self.infoLabel)
            
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
                
                info = f"字型: {fontName}\n字符數: {glyphCount}\n主板: {masterName}\n當前字符: {currentGlyph}"
                self.infoLabel.setStringValue_(info)
            else:
                self.infoLabel.setStringValue_("未載入字型")
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
            
            for control in [self.titleLabel, self.searchLabel, self.infoLabel, 
                           self.sectionLabel, self.fontSectionLabel]:
                if hasattr(self, control.__name__) and getattr(self, control.__name__):
                    control = getattr(self, control.__name__)
                    control.setTextColor_(textColor)
            
        except Exception as e:
            print(f"繪製側邊欄時發生錯誤: {e}")
            print(traceback.format_exc()) 