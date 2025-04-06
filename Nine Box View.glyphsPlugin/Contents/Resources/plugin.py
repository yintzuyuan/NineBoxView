# encoding: utf-8


###########################################################################################################
#
#
#    一般外掛 / General Plugin
#
#    閱讀文檔： / Read the Docs:
#    https://github.com/schriftgestalt/GlyphsSDK/tree/master/Python%20Templates/General%20Plugin
#
#
###########################################################################################################


# https://developer.apple.com/library/content/documentation/Cocoa/Conceptual/CocoaViewsGuide/SubclassingNSView/SubclassingNSView.html

# === 導入必要的模組 / Import necessary modules ===

from __future__ import division, print_function, unicode_literals
import objc
from GlyphsApp import *
from GlyphsApp.plugins import *
from AppKit import (
    NSColor, NSFont, NSAffineTransform, NSRectFill, NSView, NSBezierPath, 
    NSWorkspace, NSClickGestureRecognizer, NSMagnificationGestureRecognizer, 
    NSPanel, NSWindow, NSButton, NSTextField, NSRect, NSMakeRect, NSScrollView,
    NSTextView, NSTextAlignment, NSCenterTextAlignment, NSWindowController,
    NSFloatingWindowLevel, NSTitledWindowMask, NSClosableWindowMask,
    NSResizableWindowMask, NSMiniaturizableWindowMask, NSLayoutConstraint,
    NSLayoutAttributeLeft, NSLayoutAttributeRight, NSLayoutAttributeTop, 
    NSLayoutAttributeBottom, NSLayoutAttributeWidth, NSLayoutAttributeHeight,
    NSLayoutFormatAlignAllTop, NSLayoutFormatAlignAllLeft, NSLayoutFormatAlignAllRight,
    NSLayoutRelationEqual, NSPointInRect, NSNotificationCenter, 
    NSWindowWillCloseNotification, NSWindowDidResizeNotification,
    NSFontAttributeName, NSForegroundColorAttributeName, NSMakeSize
)
from Foundation import NSObject, NSString, NSArray, NSMutableArray, NSMakePoint, NSSize
import random
import traceback  # 錯誤追蹤 / Error traceback

# === 視圖元件類別 / View Element Classes ===

class NineBoxPreviewView(NSView):
    """
    九宮格預覽視圖類別，負責實際的繪製工作。
    Nine Box Preview View Class, responsible for actual drawing work.
    """

    def initWithFrame_plugin_(self, frame, plugin):
        """初始化視圖 / Initialize the view"""
        self = super(NineBoxPreviewView, self).initWithFrame_(frame)
        if self:
            self.plugin = plugin
            self.cachedHeight = 0
            
            # 註冊 mouseDown 事件，不使用手勢識別 / Register mouseDown event without using gesture recognizers
            # 簡化事件處理機制，減少 ObjC 互操作問題 / Simplify event handling to reduce ObjC interop issues
        return self
    
    def mouseDown_(self, event):
        """
        # 處理滑鼠點擊事件 / Handle mouse click event
        當滑鼠在視圖中點擊時，觸發隨機排列功能。 / When mouse clicked in view, trigger randomize function.
        """
        # 如果是雙擊，執行縮放重置 / If double click, reset zoom
        if event.clickCount() == 2:
            self.plugin.zoomFactor = 1.0
            self.plugin.savePreferences()
            self.setNeedsDisplay_(True)
        else:
            # 單擊時進行隨機排列 / Randomize on single click
            self.window().makeKeyWindow()
            self.window().makeFirstResponder_(self)
            self.plugin.randomizeCallback(self)
            
    # 移除滾輪事件處理，避免可能造成的問題
    # def scrollWheel_(self, event):
    #     """處理滾輪事件來縮放 / Handle scroll wheel events for zooming"""
    #     delta = event.deltaY()
    #     # 滾輪向上放大，向下縮小 / Scroll up to zoom in, down to zoom out
    #     scaleFactor = 1.0 + (delta * 0.03)  # 調整縮放靈敏度 / Adjust zoom sensitivity
    #     self.plugin.zoomFactor *= scaleFactor
    #     # 限制縮放範圍 / Limit zoom range
    #     self.plugin.zoomFactor = max(0.5, min(2.0, self.plugin.zoomFactor))
    #     self.plugin.savePreferences()
    #     self.setNeedsDisplay_(True)

    def drawRect_(self, rect):
        """繪製視圖內容 / Draw the content of the view"""

        try:
            # === 設定背景顏色 / Set the background color ===
            if self.plugin.darkMode:
                NSColor.colorWithCalibratedRed_green_blue_alpha_(0.1, 0.1, 0.1, 1.0).set()
            else:
                NSColor.colorWithCalibratedRed_green_blue_alpha_(1.0, 1.0, 1.0, 1.0).set()
            NSRectFill(rect)

            # === 取得基本參數 / Get basic parameters ===
            # 取得目前字型和主板 / Get the current font and master
            if not Glyphs.font:
                return

            currentMaster = Glyphs.font.selectedFontMaster

            # 使用目前的排列 / Use the current arrangement
            display_chars = self.plugin.currentArrangement if self.plugin.selectedChars else []

            # === 設定基本尺寸 / Set basic sizes ===
            MARGIN_RATIO = 0.07
            SPACING_RATIO = 0.03

            # 計算字符高度和邊距 / Calculate the character height and margin
            self.cachedHeight = currentMaster.ascender - currentMaster.descender
            MARGIN = min(rect.size.width, rect.size.height) * MARGIN_RATIO

            # === 計算網格尺寸 / Calculate the grid size ===
            # 使用 getBaseWidth 方法取得基準寬度
            baseWidth = self.plugin.getBaseWidth()

            # 計算最大寬度
            maxWidth = baseWidth
            if display_chars:
                for char in display_chars:
                    glyph = Glyphs.font.glyphs[char]
                    if glyph and glyph.layers[currentMaster.id]:
                        maxWidth = max(maxWidth, glyph.layers[currentMaster.id].width)

            SPACING = maxWidth * SPACING_RATIO

            # 計算單元格寬度 / Calculate the cell width
            cellWidth = maxWidth + SPACING

            # 計算網格總寬度和高度 / Calculate the total width and height of the grid
            gridWidth = 3 * cellWidth + 2 * SPACING
            gridHeight = 3 * self.cachedHeight + 2 * SPACING

            # === 計算縮放比例 / Calculate the scale ===
            availableWidth = rect.size.width - 2 * MARGIN
            availableHeight = rect.size.height - 2 * MARGIN
            scale = min(availableWidth / gridWidth, availableHeight / gridHeight, 1)

            # 應用自定義縮放 / Apply custom scale
            customScale = min(max(self.plugin.zoomFactor, 0.5), 2.0)  # 確保縮放值在有效範圍內
            scale *= customScale

            # 更新網格尺寸 / Update the grid size
            cellWidth *= scale
            gridWidth *= scale
            gridHeight *= scale
            SPACING *= scale

            # 計算繪製起始位置 / Calculate the starting position for drawing
            startX = rect.size.width / 2 - gridWidth / 2
            offsetY = rect.size.height * 0.05
            startY = (rect.size.height + gridHeight) / 2 + offsetY

            # === 繪製九宮格字符 / Draw the characters in the nine-box grid ===
            for i in range(9):
                row = i // 3
                col = i % 3

                # 計算目前單元格的中心位置 / Calculate the center position of the current cell
                centerX = startX + (col + 0.5) * cellWidth + col * SPACING
                centerY = startY - (row + 0.5) * (gridHeight / 3)

                # 選擇要繪製的字符層 / Select the character layer to draw
                layer = None
                if i == 4 and Glyphs.font.selectedLayers:  # 中心位置 / Center position
                    layer = Glyphs.font.selectedLayers[0]
                else:
                    # 當沒有其他字符時，使用目前編輯的字符填充 / When there are no other characters, fill with the currently edited character
                    if not display_chars:
                        if Glyphs.font.selectedLayers:
                            layer = Glyphs.font.selectedLayers[0]
                    else:
                        char_index = i if i < 4 else i - 1
                        if char_index < len(display_chars):
                            glyph = Glyphs.font.glyphs[display_chars[char_index]]
                            layer = glyph.layers[currentMaster.id] if glyph else None

                if layer:
                    # 計算字符縮放比例 / Calculate the character scale
                    glyphWidth = layer.width
                    glyphHeight = self.cachedHeight
                    scaleX = cellWidth / glyphWidth if glyphWidth > 0 else 1
                    scaleY = (gridHeight / 3 - SPACING) / glyphHeight if glyphHeight > 0 else 1
                    glyphScale = min(scaleX, scaleY)

                    # 計算縮放後的字符尺寸和位置 / Calculate the scaled character size and position
                    scaledWidth = glyphWidth * glyphScale
                    scaledHeight = glyphHeight * glyphScale
                    x = centerX - scaledWidth / 2
                    y = centerY - scaledHeight / 2

                    # 建立變換矩陣 / Create a transformation matrix
                    transform = NSAffineTransform.transform()
                    transform.translateXBy_yBy_(x, y)
                    transform.scaleBy_(glyphScale)

                    # === 繪製開放和封閉路徑 / Draw open and closed paths ===
                    # 取得完整路徑的副本 / Get a copy of complete path
                    bezierPath = layer.completeBezierPath.copy()
                    bezierPath.transformUsingAffineTransform_(transform)

                    # 取得開放路徑的副本 / Get a copy of open path
                    openBezierPath = layer.completeOpenBezierPath.copy()
                    openBezierPath.transformUsingAffineTransform_(transform)

                    # 設定繪製顏色 / Set drawing color
                    if self.plugin.darkMode:
                        fillColor = NSColor.whiteColor()
                        strokeColor = NSColor.whiteColor()
                    else:
                        fillColor = NSColor.blackColor()
                        strokeColor = NSColor.blackColor()

                    # 繪製封閉路徑（使用填充）/ Draw closed paths (using fill)
                    fillColor.set()
                    bezierPath.fill()

                    # 繪製開放路徑（使用描邊）/ Draw open paths (using stroke)
                    strokeColor.set()
                    openBezierPath.setLineWidth_(1.0)  # 設定線寬 / Set line width
                    openBezierPath.stroke()

                    # 新增：繪製格子編號 / New: Draw grid number
                    if self.plugin.showNumbers:
                        # 直接在這裡繪製數字 / Draw number directly here
                        numberText = NSString.stringWithString_(str(i))
                        numberAttributes = {
                            NSFontAttributeName: NSFont.boldSystemFontOfSize_(9.0),
                            NSForegroundColorAttributeName: fillColor.colorWithAlphaComponent_(0.5)
                        }
                        numberSize = numberText.sizeWithAttributes_(numberAttributes)
                        numberPosition = NSMakePoint(
                            centerX - numberSize.width/2, 
                            centerY - scaledHeight/2 - 15 - numberSize.height/2
                        )
                        numberText.drawAtPoint_withAttributes_(numberPosition, numberAttributes)

        except Exception as e:
            print(traceback.format_exc())

class NineBoxWindow(NSWindowController):
    """
    九宮格預覽視窗控制器，取代原有的 Vanilla FloatingWindow。
    Nine Box Window Controller, replaces the original Vanilla FloatingWindow.
    """
    
    def initWithPlugin_(self, plugin):
        """初始化視窗控制器 / Initialize the window controller"""
        try:
            # 載入上次儲存的視窗大小 / Load last saved window size
            defaultSize = (300, 340)
            savedSize = Glyphs.defaults.get("com.YinTzuYuan.NineBoxView.windowSize", defaultSize)
            
            # 建立視窗 / Create window
            windowRect = NSMakeRect(0, 0, savedSize[0], savedSize[1])
            styleMask = NSTitledWindowMask | NSClosableWindowMask | NSResizableWindowMask | NSMiniaturizableWindowMask
            window = NSPanel.alloc().initWithContentRect_styleMask_backing_defer_(
                windowRect,
                styleMask,
                2,
                False
            )
            window.setTitle_(plugin.name)
            window.setMinSize_(NSMakeSize(200, 240))
            window.setLevel_(NSFloatingWindowLevel)
            window.setReleasedWhenClosed_(False)
            
            # 使用規範的 ObjC 初始化方式
            windowController = NSWindowController.alloc().initWithWindow_(window)
            
            # 手動將 self 轉換為擴展的 NSWindowController
            self.window = lambda: window
            self.plugin = plugin
            self.showWindow_ = windowController.showWindow_
            self.previewView = None
            self.searchField = None
            self.pickButton = None
            self.darkModeButton = None
            
            contentView = window.contentView()
            
            # 建立預覽視圖 / Create preview view
            previewRect = NSMakeRect(0, 35, window.frame().size.width, window.frame().size.height - 35)
            self.previewView = NineBoxPreviewView.alloc().initWithFrame_plugin_(previewRect, plugin)
            contentView.addSubview_(self.previewView)
            
            # 建立輸入框 / Create input field
            placeholder = Glyphs.localize({
                'en': u'Input glyphs (space-separated) or leave blank',
                'zh-Hant': u'輸入字符（以空格分隔）或留空',
                'zh-Hans': u'输入字符（用空格分隔）或留空',
                'ja': u'文字を入力してください（スペースで区切る）または空欄のまま',
                'ko': u'문자를 입력하세요 (공백으로 구분) 또는 비워 두세요',
            })
            
            searchFieldRect = NSMakeRect(10, 8, window.frame().size.width - 110, 22)
            self.searchField = NSTextField.alloc().initWithFrame_(searchFieldRect)
            self.searchField.setStringValue_(plugin.lastInput)
            self.searchField.setPlaceholderString_(placeholder)
            self.searchField.setTarget_(self)
            self.searchField.setAction_("searchFieldAction:")
            contentView.addSubview_(self.searchField)
            
            # 建立選擇字符按鈕 / Create pick glyph button
            pickButtonRect = NSMakeRect(window.frame().size.width - 95, 8, 40, 22)
            self.pickButton = NSButton.alloc().initWithFrame_(pickButtonRect)
            self.pickButton.setTitle_("🔣")
            self.pickButton.setTarget_(self)
            self.pickButton.setAction_("pickGlyphAction:")
            self.pickButton.setBezelStyle_(1)  # 圓角按鈕 / Rounded button
            contentView.addSubview_(self.pickButton)
            
            # 建立深色模式按鈕 / Create dark mode button
            darkModeButtonRect = NSMakeRect(window.frame().size.width - 50, 8, 40, 22)
            self.darkModeButton = NSButton.alloc().initWithFrame_(darkModeButtonRect)
            self.darkModeButton.setTitle_(plugin.getDarkModeIcon())
            self.darkModeButton.setTarget_(self)
            self.darkModeButton.setAction_("darkModeAction:")
            self.darkModeButton.setBezelStyle_(1)  # 圓角按鈕 / Rounded button
            contentView.addSubview_(self.darkModeButton)
            
            # 監聽視窗大小調整 / Listen for window resize events
            NSNotificationCenter.defaultCenter().addObserver_selector_name_object_(
                self,
                "windowDidResize:",
                NSWindowDidResizeNotification,
                window
            )
            
            # 監聽視窗關閉 / Listen for window close events
            NSNotificationCenter.defaultCenter().addObserver_selector_name_object_(
                self,
                "windowWillClose:",
                NSWindowWillCloseNotification,
                window
            )
            
            # 如果有選取的字符但沒有排列，則生成新排列 / Generate a new arrangement if there are selected characters but no arrangement
            if plugin.selectedChars and not plugin.currentArrangement:
                plugin.generateNewArrangement()
                
        except Exception as e:
            print(f"初始化視窗時發生錯誤: {e}")
            print(traceback.format_exc())
            
        return self
    
    def windowDidResize_(self, notification):
        """視窗大小調整時的處理 / Handle window resize events"""
        if notification.object() == self.window():
            frame = self.window().frame()
            contentView = self.window().contentView()
            contentSize = contentView.frame().size
            
            # 調整預覽視圖大小 / Adjust preview view size
            self.previewView.setFrame_(NSMakeRect(0, 35, contentSize.width, contentSize.height - 35))
            # 調整其他控制項的位置 / Adjust other controls' positions
            self.searchField.setFrame_(NSMakeRect(10, 8, contentSize.width - 110, 22))
            self.pickButton.setFrame_(NSMakeRect(contentSize.width - 95, 8, 40, 22))
            self.darkModeButton.setFrame_(NSMakeRect(contentSize.width - 50, 8, 40, 22))
            
            # 更新重繪 / Update and redraw
            self.previewView.setNeedsDisplay_(True)
    
    def windowWillClose_(self, notification):
        """視窗關閉時的處理 / Handle window close events"""
        if notification.object() == self.window():
            # 儲存目前輸入內容 / Save current input
            self.plugin.lastInput = self.searchField.stringValue()
            self.plugin.savePreferences()
            # 儲存視窗大小 / Save window size
            frame = self.window().frame()
            Glyphs.defaults["com.YinTzuYuan.NineBoxView.windowSize"] = (frame.size.width, frame.size.height)
            # 移除觀察者 / Remove observers
            NSNotificationCenter.defaultCenter().removeObserver_(self)
    
    def searchFieldAction_(self, sender):
        """輸入框動作處理 / Handle search field action"""
        self.plugin.searchFieldCallback(sender)
    
    def pickGlyphAction_(self, sender):
        """選擇字符按鈕動作處理 / Handle pick glyph button action"""
        self.plugin.pickGlyph(sender)
    
    def darkModeAction_(self, sender):
        """深色模式按鈕動作處理 / Handle dark mode button action"""
        self.plugin.darkModeCallback(sender)
    
    def redraw(self):
        """重繪預覽視圖 / Redraw the preview view"""
        self.previewView.setNeedsDisplay_(True)
    
    def makeKeyAndOrderFront(self):
        """顯示並成為主視窗 / Show and become key window"""
        try:
            self.showWindow_(None)
            self.window().makeKeyAndOrderFront_(None)
        except Exception as e:
            print(f"顯示視窗時發生錯誤: {e}")
            print(traceback.format_exc())

# === 主要外掛類別 / Main Plugin Class ==

class NineBoxView(GeneralPlugin):
    """
    定義主要外掛類別 / Define the main plugin class
    - 視窗操作 / Window Operations
    - 界面更新 / Interface Update
    - 事件處理 / Event Handling
    - 配置管理 / Configuration Management
    - 工具方法 / Utility Methods
    - 清理方法 / Cleanup
    """

    @objc.python_method
    def settings(self):
        # 設定外掛名稱
        self.name = Glyphs.localize({
            'en': u'Nine Box Preview',
            'zh-Hant': u'九宮格預覽',
            'zh-Hans': u'九宫格预览',
            'ja': u'九宮格プレビュー',
            'ko': u'구궁격 미리보기',
            'ar': u'معاينة المربعات التسعة',
            'cs': u'Náhled devíti polí',
            'de': u'Neun-Felder-Vorschau',
            'es': u'Vista previa de nueve cuadros',
            'fr': u'Aperçu en neuf cases',
            'it': u'Anteprima a nove caselle',
            'pt': u'Visualização em nove caixas',
            'ru': u'Предпросмотр девяти ячеек',
            'tr': u'Dokuz Kutu Önizleme'
        })
        self.loadPreferences()
        self.selectedChars = []  # 儲存選取的字符 / Store selected characters
        self.currentArrangement = []  # 儲存目前的排列 / Store current arrangement
        self.windowController = None  # 視窗控制器 / Window controller

    @objc.python_method
    def start(self):
        try:
            # 新增選單項 / Add menu item
            newMenuItem = NSMenuItem(self.name, self.toggleWindow_)
            Glyphs.menu[WINDOW_MENU].append(newMenuItem)

            # 新增回調函數
            Glyphs.addCallback(self.updateInterface, UPDATEINTERFACE)
            Glyphs.addCallback(self.updateInterface, DOCUMENTACTIVATED)

            # 載入偏好設定 / Load preferences
            self.loadPreferences()
        except:
            self.logToMacroWindow(traceback.format_exc())

    # === 視窗操作 / Window Operations ===

    @objc.python_method
    def toggleWindow_(self, sender):
        """切換視窗的顯示狀態 / Toggle the visibility of the window"""

        try:
            # 如果視窗不存在，則創建 / If window doesn't exist, create it
            if self.windowController is None:
                self.windowController = NineBoxWindow.alloc().initWithPlugin_(self)
                
            # 顯示視窗 / Show window
            self.windowController.makeKeyAndOrderFront()
            self.updateInterface(None)
        except:
            self.logToMacroWindow(traceback.format_exc())

    @objc.python_method
    def showWindow(self):
        """顯示視窗 / Show the window"""

        if self.windowController is not None:
            self.windowController.showWindow_(None)

    @objc.python_method
    def hideWindow(self):
        """隱藏視窗 / Hide the window"""

        if self.windowController is not None:
            self.windowController.window().orderOut_(None)

    @objc.python_method
    def getDarkModeIcon(self):
        """取得深色模式按鈕的圖示 / Get the icon for the dark mode button"""

        return "🌙" if self.darkMode else "☀️"

    @objc.python_method
    def logToMacroWindow(self, message):
        """將訊息記錄到巨集視窗 / Log message to the Macro Window"""

        Glyphs.clearLog()
        print(message)

    # === 界面更新 / Interface Update ===

    @objc.python_method
    def updateInterface(self, sender):
        """更新介面 / Update the interface"""

        if self.windowController is not None:
            self.windowController.redraw()
            
            # 更新深色模式按鈕的圖示 / Update dark mode button icon
            darkModeButton = self.windowController.darkModeButton
            if darkModeButton:
                darkModeButton.setTitle_(self.getDarkModeIcon())

    # === 事件處理 / Event Handling ===

    @objc.python_method
    def searchFieldCallback(self, sender):
        """處理輸入框的回調函數 / Callback function for the input field"""

        # 檢查是否有開啟字型檔案
        if not Glyphs.font:
            print("警告：沒有開啟字型檔案")
            return

        # 取得目前輸入 / Get the current input
        input_text = sender.stringValue()

        # 儲存目前輸入內容 / Save the current input content
        self.lastInput = input_text

        if input_text:
            # 解析輸入文字，取得所有有效字符 / Parse the input text and get all valid characters
            new_chars = self.parseInputText(input_text)

            # 檢查字符列表是否有實質變化 / Check if the character list has changed
            if new_chars != self.selectedChars:
                self.selectedChars = new_chars
                # 只在字符列表變化時執行隨機排列 / Only perform randomization when the character list changes
                self.generateNewArrangement()
        else:
            self.selectedChars = []
            self.currentArrangement = []

        self.savePreferences()
        self.updateInterface(None)

    @objc.python_method
    def randomizeCallback(self, sender):
        """隨機排列按鈕的回調函數 / Randomize Button Callback"""

        if self.selectedChars:
            self.generateNewArrangement()
            self.updateInterface(None)

    @objc.python_method
    def darkModeCallback(self, sender):
        """深色模式按鈕的回調函數 / Dark Mode Button Callback"""

        self.darkMode = not self.darkMode
        if self.windowController is not None:
            self.windowController.darkModeButton.setTitle_(self.getDarkModeIcon())
        self.savePreferences()
        self.updateInterface(None)

    @objc.python_method
    def pickGlyph(self, sender):
        """選擇字符的回調函數 / Callback function for picking glyphs"""

        try:
            font = Glyphs.font
            if not font:
                return

            choice = PickGlyphs(
                list(font.glyphs),
                font.selectedFontMaster.id,
                self.searchHistory,
                "com.YinTzuYuan.NineBoxView.search"
            )

            if choice and choice[0]:
                selected_chars = []
                for selection in choice[0]:
                    if isinstance(selection, GSGlyph):
                        # 直接使用字符名稱 / Use the glyph name directly
                        selected_chars.append(selection.name)

                if selected_chars and self.windowController is not None:
                    # 取得目前文字 / Get the current text
                    textField = self.windowController.searchField
                    current_text = textField.stringValue()
                    editor = textField.currentEditor()
                    
                    # 取得游標位置 / Get the cursor position
                    if editor:
                        selection_range = editor.selectedRange()
                        cursor_position = selection_range.location
                    else:
                        cursor_position = len(current_text)

                    # 將選取的字符用空格連接 / Join the selected characters with spaces
                    chars_to_insert = ' '.join(selected_chars)
                    if cursor_position > 0 and current_text[cursor_position-1:cursor_position] != ' ':
                        chars_to_insert = ' ' + chars_to_insert
                    if cursor_position < len(current_text) and current_text[cursor_position:cursor_position+1] != ' ':
                        chars_to_insert = chars_to_insert + ' '

                    # 在游標位置插入新的文字 / Insert new text at the cursor position
                    new_text = current_text[:cursor_position] + chars_to_insert + current_text[cursor_position:]
                    textField.setStringValue_(new_text)

                    # 更新游標位置到插入內容之後 / Update the cursor position to after the inserted content
                    new_position = cursor_position + len(chars_to_insert)
                    if editor:
                        editor.setSelectedRange_((new_position, new_position))

                    # 觸發 searchFieldCallback 以更新界面 / Trigger searchFieldCallback to update the interface
                    self.searchFieldCallback(textField)

        except Exception as e:
            print(f"選擇字符時發生錯誤: {str(e)}")
            print(traceback.format_exc())

    # === 配置管理 / Configuration Management ===

    @objc.python_method
    def loadPreferences(self):
        """載入使用者偏好設定 / Load user preferences"""

        self.darkMode = Glyphs.defaults.get("com.YinTzuYuan.NineBoxView.darkMode", False)
        self.lastInput = Glyphs.defaults.get("com.YinTzuYuan.NineBoxView.lastInput", "")
        self.selectedChars = Glyphs.defaults.get("com.YinTzuYuan.NineBoxView.selectedChars", [])
        self.currentArrangement = Glyphs.defaults.get("com.YinTzuYuan.NineBoxView.currentArrangement", [])
        self.testMode = Glyphs.defaults.get("com.YinTzuYuan.NineBoxView.testMode", False)
        self.searchHistory = Glyphs.defaults.get("com.YinTzuYuan.NineBoxView.search", "")
        self.zoomFactor = Glyphs.defaults.get("com.YinTzuYuan.NineBoxView.zoomFactor", 1.0)
        self.showNumbers = Glyphs.defaults.get("com.YinTzuYuan.NineBoxView.showNumbers", False)

    @objc.python_method
    def savePreferences(self):
        """儲存使用者偏好設定 / Save user preferences"""

        Glyphs.defaults["com.YinTzuYuan.NineBoxView.darkMode"] = self.darkMode
        Glyphs.defaults["com.YinTzuYuan.NineBoxView.lastInput"] = self.lastInput
        Glyphs.defaults["com.YinTzuYuan.NineBoxView.selectedChars"] = self.selectedChars
        Glyphs.defaults["com.YinTzuYuan.NineBoxView.currentArrangement"] = self.currentArrangement
        Glyphs.defaults["com.YinTzuYuan.NineBoxView.testMode"] = self.testMode
        Glyphs.defaults["com.YinTzuYuan.NineBoxView.search"] = self.searchHistory
        Glyphs.defaults["com.YinTzuYuan.NineBoxView.zoomFactor"] = self.zoomFactor
        Glyphs.defaults["com.YinTzuYuan.NineBoxView.showNumbers"] = self.showNumbers


    # === 工具方法 / Utility Methods ===

    @objc.python_method
    def getBaseWidth(self):
        """取得基準寬度 / Get the base width"""
        if not Glyphs.font:
            return 1000

        currentMaster = Glyphs.font.selectedFontMaster

        # 1. 檢查主板是否有 Default Layer Width 參數
        defaultWidth = None
        if currentMaster.customParameters['Default Layer Width']:
            defaultWidth = float(currentMaster.customParameters['Default Layer Width'])
            if defaultWidth > 0:
                return defaultWidth

        # 2. 使用選取的字符層寬度
        if Glyphs.font.selectedLayers:
            return Glyphs.font.selectedLayers[0].width

        # 3. 使用字型的 UPM (units per em) K值
        if hasattr(Glyphs.font, 'upm'):
            return max(Glyphs.font.upm, 500)

        # 4. 最後的預設值
        return 1000

    @objc.python_method
    def parseInputText(self, text):
        """
        解析輸入文字並返回有效的字符列表

        處理規則：
            - 漢字/東亞文字：直接連續處理，不需空格分隔
            - ASCII 字符/字符名稱：需要用空格分隔
            - 混合輸入時，保持上述規則

        例如：
            - 輸入 "顯示文字" -> ['顯', '示', '文', '字']
            - 輸入 "A B C.ss01" -> ['A', 'B', 'C.ss01']
            - 輸入 "顯示文字 A B" -> ['顯', '示', '文', '字', 'A', 'B']

        ---

        Parse the input text and return a list of valid characters

        Rules:
            - For Chinese characters or East Asian characters, process them directly without space separation
            - For ASCII characters or glyph names, separate them with spaces
            - When mixed input, keep the above rules

        For example:
            - Input "顯示文字" -> ['顯', '示', '文', '字']
            - Input "A B C.ss01" -> ['A', 'B', 'C.ss01']
            - Input "顯示文字 A B" -> ['顯', '示', '文', '字', 'A', 'B']
        """

        # 檢查是否有開啟字型檔案 / Check if a font file is open
        if not Glyphs.font:
            print("警告：沒有開啟字型檔案")
            return []

        chars = []
        # 移除連續的多餘空格，但保留有意義的單個空格 / Remove consecutive extra spaces, but keep meaningful single spaces
        parts = ' '.join(text.split())
        parts = parts.split(' ')

        for part in parts:
            if not part:
                continue

            # 檢查是否包含漢字/東亞文字 / Check if it contains Chinese characters or East Asian characters
            if any(ord(c) > 0x4E00 for c in part):
                # 對於漢字，逐字符處理 / For Chinese characters, process character by character
                for char in part:
                    if Glyphs.font.glyphs[char]:
                        chars.append(char)
                    else:
                        pass
            else:
                # 對於 ASCII 字符名稱，整體處理 / For ASCII character names, process as a whole
                if Glyphs.font.glyphs[part]:
                    chars.append(part)
                else:
                    pass

        return chars

    @objc.python_method
    def generateNewArrangement(self):
        """
        生成新的隨機排列 / Generate a new random arrangement
        """

        display_chars = list(self.selectedChars)  # 複製一份字符列表 / Copy the character list

        # 如果字符數量超過 8 個，隨機選擇 8 個 / If there are more than 8 characters, randomly select 8
        if len(display_chars) > 8:
            display_chars = random.sample(display_chars, 8)
        elif display_chars:
            # 如果字符數量不足 8 個，從現有字符中隨機選擇來填充 / If there are fewer than 8 characters, fill in randomly from the existing characters
            while len(display_chars) < 8:
                display_chars.append(random.choice(display_chars))

        # 隨機打亂順序 / Randomize the order
        random.shuffle(display_chars)
        self.currentArrangement = display_chars
        self.savePreferences()

    # === 清理方法 / Cleanup ===

    @objc.python_method
    def __del__(self):
        """
        清理資源 / Clean up resources
        """

        self.savePreferences()
        Glyphs.removeCallback(self.updateInterface, UPDATEINTERFACE)
        Glyphs.removeCallback(self.updateInterface, DOCUMENTACTIVATED)
        NSNotificationCenter.defaultCenter().removeObserver_(self)

    def __file__(self):
        return __file__
