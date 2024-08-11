# encoding: utf-8

###########################################################################################################
#
#
#    一般外掛
#
#    閱讀文檔：
#    https://github.com/schriftgestalt/GlyphsSDK/tree/master/Python%20Templates/General%20Plugin
#
#
###########################################################################################################


# https://developer.apple.com/library/content/documentation/Cocoa/Conceptual/CocoaViewsGuide/SubclassingNSView/SubclassingNSView.html

# 導入必要的模組
import objc
from GlyphsApp import *
from GlyphsApp.plugins import *
from AppKit import NSColor, NSFont, NSAffineTransform, NSRectFill, NSView, NSBezierPath, NSWorkspace, NSClickGestureRecognizer, NSMagnificationGestureRecognizer
from vanilla import FloatingWindow, Group, Button, EditText
import traceback  # 新增此行以便進行錯誤追蹤

# 定義九宮格預覽視圖類別
class NineBoxPreviewView(NSView):
    def init(self):
        self = super(NineBoxPreviewView, self).init()
        if self:
            # 設定雙擊手勢識別器
            doubleClickRecognizer = NSClickGestureRecognizer.alloc().initWithTarget_action_(self, self.handleDoubleClick_)
            doubleClickRecognizer.setNumberOfClicksRequired_(2)
            self.addGestureRecognizer_(doubleClickRecognizer)
            
            # 設定縮放手勢識別器
            magnificationRecognizer = NSMagnificationGestureRecognizer.alloc().initWithTarget_action_(self, self.handleMagnification_)
            self.addGestureRecognizer_(magnificationRecognizer)
            
            # 啟用觸控事件處理
            self.setAcceptsTouchEvents_(True)
        return self
    
    # 處理雙擊事件，重置縮放
    def handleDoubleClick_(self, sender):
        self.wrapper.plugin.resetZoom()

    # 處理縮放事件
    def handleMagnification_(self, sender):
        sensitivityFactor = 0.1  # 調整縮放靈敏度
        newZoom = self.wrapper.plugin.zoomFactor * (1 + sender.magnification() * sensitivityFactor)
        newZoom = max(0.5, min(2.0, newZoom))  # 限制縮放範圍
        self.wrapper.plugin.zoomFactor = newZoom
        self.wrapper.plugin.savePreferences()
        self.wrapper.plugin.updateInterface(None)

    # 繪製視圖內容
    def drawRect_(self, rect):
        try:
            # 設定背景顏色
            if self.wrapper.plugin.darkMode:
                NSColor.colorWithCalibratedRed_green_blue_alpha_(0, 0, 0, 1.0).set()
            else:
                NSColor.colorWithCalibratedRed_green_blue_alpha_(1.0, 1.0, 1.0, 1.0).set()
            NSRectFill(rect)

            # 檢查是否有選中的字符層
            if not Glyphs.font or not Glyphs.font.selectedLayers:
                return

            # 獲取目前選中的字符層和字符
            self.currentLayer = Glyphs.font.selectedLayers[0]
            currentChar = self.currentLayer.parent.unicode
            currentMaster = Glyphs.font.selectedFontMaster  # 定義 currentMaster


            # 決定要搜尋的字符
            if self.wrapper.plugin.w.searchField.get().strip() == "":
                self.searchChar = currentChar
            else:
                self.searchChar = self.wrapper.plugin.lastChar or currentChar

            # 獲取中心字符和搜尋字符
            centerGlyph = self.currentLayer.parent
            searchGlyph = Glyphs.font.glyphs[self.searchChar] if self.searchChar else centerGlyph


            # 設定邊距和間距比例
            MARGIN_RATIO = 0.07
            SPACING_RATIO = 0.03

            # 計算字符高度和邊距
            self.cachedHeight = currentMaster.ascender - currentMaster.descender
            MARGIN = min(rect.size.width, rect.size.height) * MARGIN_RATIO

            # 計算字符寬度和間距
            centerWidth = self.currentLayer.width
            searchWidth = searchGlyph.layers[currentMaster.id].width
            SPACING = max(centerWidth, searchWidth) * SPACING_RATIO

            # 計算單元格寬度
            searchCellWidth = searchWidth + SPACING
            centerCellWidth = max(centerWidth, searchWidth) + SPACING

            # 計算網格總寬度和高度
            gridWidth = centerCellWidth + 2 * searchCellWidth + 2 * SPACING
            gridHeight = 3 * self.cachedHeight + 2 * SPACING

            # 計算縮放比例
            availableWidth = rect.size.width - 2 * MARGIN
            availableHeight = rect.size.height - 2 * MARGIN
            scale = min(availableWidth / gridWidth, availableHeight / gridHeight, 1)

            # 應用自定義縮放
            customScale = self.wrapper.plugin.zoomFactor
            scale *= customScale

            # 更新網格尺寸
            centerCellWidth *= scale
            searchCellWidth *= scale
            gridWidth *= scale
            gridHeight *= scale
            SPACING *= scale

            # 計算繪製起始位置
            startX = rect.size.width / 2 - gridWidth / 2
            offsetY = rect.size.height * 0.05
            startY = (rect.size.height + gridHeight) / 2 + offsetY
            leftColumnCenterX = startX + searchCellWidth / 2
            middleColumnCenterX = startX + searchCellWidth + SPACING + centerCellWidth / 2
            rightColumnCenterX = startX + gridWidth - searchCellWidth / 2

            # 繪製九宮格中的字符
            for i in range(9):
                row = i // 3
                col = i % 3
                
                # 決定目前單元格的中心位置和寬度
                if col == 0:
                    centerX = leftColumnCenterX
                    cellWidth = searchCellWidth
                elif col == 1:
                    centerX = middleColumnCenterX
                    cellWidth = centerCellWidth if i == 4 else searchCellWidth
                else:
                    centerX = rightColumnCenterX
                    cellWidth = searchCellWidth
                
                centerY = startY - (row + 0.5) * (gridHeight / 3)
                cellHeight = gridHeight / 3 - SPACING

                # 選擇要繪製的字符層
                if i == 4:
                    layer = self.currentLayer
                else:
                    layer = searchGlyph.layers[currentMaster.id]

                if layer:
                    # 計算字符縮放比例
                    glyphWidth = layer.width
                    glyphHeight = self.cachedHeight
                    scaleX = cellWidth / glyphWidth if glyphWidth > 0 else 1
                    scaleY = cellHeight / glyphHeight if glyphHeight > 0 else 1
                    glyphScale = min(scaleX, scaleY)

                    # 計算縮放後的字符尺寸和位置
                    scaledWidth = glyphWidth * glyphScale
                    scaledHeight = glyphHeight * glyphScale
                    x = centerX - scaledWidth / 2
                    y = centerY - scaledHeight / 2

                    # 建立變換矩陣
                    transform = NSAffineTransform.transform()
                    transform.translateXBy_yBy_(x, y)
                    transform.scaleBy_(glyphScale)

                    # 繪製字符路徑
                    bezierPath = layer.completeBezierPath.copy()
                    bezierPath.transformUsingAffineTransform_(transform)

                    # 設定填充顏色
                    if self.wrapper.plugin.darkMode:
                        NSColor.whiteColor().set()
                    else:
                        NSColor.blackColor().set()
                    bezierPath.fill()

        except Exception as e:
            print(traceback.format_exc())

    # 處理滑鼠點擊事件
    def mouseDown_(self, event):
        # 當滑鼠在視圖內點擊時，使工具視窗成為關鍵視窗
        self.window().makeKeyWindow()
        self.window().makeFirstResponder_(self)

# 定義九宮格預覽群組類別
class NineBoxPreview(Group):
    nsViewClass = NineBoxPreviewView

    def __init__(self, posSize, plugin):
        super(NineBoxPreview, self).__init__(posSize)
        self._nsObject.wrapper = self
        self.plugin = plugin

    def redraw(self):
        self._nsObject.setNeedsDisplay_(True)

# 定義主外掛類別
class NineBoxView(GeneralPlugin):

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

    @objc.python_method
    def start(self):
        try:
            # 新增選單項
            newMenuItem = NSMenuItem(self.name, self.toggleWindow_)
            Glyphs.menu[WINDOW_MENU].append(newMenuItem)
            
            # 新增回調函數
            Glyphs.addCallback(self.updateInterface, UPDATEINTERFACE)
            Glyphs.addCallback(self.updateInterface, DOCUMENTACTIVATED)

            # 新增應用程式啟動和停用的觀察者
            NSWorkspace.sharedWorkspace().notificationCenter().addObserver_selector_name_object_(
                self,
                self.applicationActivated_,
                "NSWorkspaceDidActivateApplicationNotification",
                None
            )
            NSWorkspace.sharedWorkspace().notificationCenter().addObserver_selector_name_object_(
                self,
                self.applicationDeactivated_,
                "NSWorkspaceDidDeactivateApplicationNotification",
                None
            )
            
            # 載入偏好設定並開啟視窗
            self.loadPreferences()
            self.w.open()
            self.w.makeKey()
        except:
            self.logToMacroWindow(traceback.format_exc())

    @objc.python_method
    def pickGlyph(self, sender):
        font = Glyphs.font
        if not font:
            return
        
        choice = PickGlyphs(
            list(font.glyphs),
            font.selectedFontMaster.id,
            self.lastChar,
            "com.YinTzuYuan.NineBoxView.search"
        )
        
        if choice and choice[0]:
            selected_glyph = choice[0][0]
            # 如果字形有 Unicode 值，使用它；否則使用字形名稱
            self.lastChar = selected_glyph.unicode or selected_glyph.name
            self.w.searchField.set(self.lastChar)
            self.savePreferences()
            self.updateInterface(None)

    @objc.python_method
    def toggleWindow_(self, sender):
        try:
            if not hasattr(self, 'w') or self.w is None:
                # 載入上次保存的窗口大小，如果沒有則使用預設值
                defaultSize = (300, 340)
                savedSize = Glyphs.defaults.get("com.YinTzuYuan.NineBoxView.windowSize", defaultSize)
                
                self.w = FloatingWindow(savedSize, self.name, minSize=(200, 240),
                                        autosaveName="com.YinTzuYuan.NineBoxView.mainwindow")
                self.w.preview = NineBoxPreview((0, 0, -0, -40), self)
                
                placeholder = Glyphs.localize({
                    'en': u'Enter a character',
                    'zh-Hant': u'輸入一個字符',
                    'zh-Hans': u'输入一个字符形',
                    'ja': u'文字を入力',
                    'ko': u'문자 입력',
                    'ar': u'أدخل حرفًا',
                    'cs': u'Zadejte znak',
                    'de': u'Zeichen eingeben',
                    'es': u'Ingrese un carácter',
                    'fr': u'Saisissez un caractère',
                    'it': u'Inserisci un carattere',
                    'pt': u'Digite um caractere',
                    'ru': u'Введите символ',
                    'tr': u'Bir karakter girin'
                })
                
                self.w.searchField = EditText((10, -30, -140, 22), 
                                            placeholder=placeholder, 
                                            callback=self.searchFieldCallback)
                self.w.searchField.set(self.lastChar)
                
                searchButtonTitle = Glyphs.localize({
                    'en': u'Glyph Picker',
                    'zh-Hant': u'字符選擇器'
                    # 添加其他語言...
                })
                self.w.searchButton = Button((-130, -30, -70, 22), searchButtonTitle,
                                            callback=self.pickGlyph)
                
                self.w.darkModeButton = Button((-60, -30, -10, 22), self.getDarkModeIcon(),
                                            callback=self.darkModeCallback)
                
                self.w.bind("close", self.windowClosed_)
                self.w.bind("resize", self.windowResized_)
                self.w.open()

            # 調整已存在的元素
            self.adjustUIElements()

            self.w.makeKey()
            self.updateInterface(None)
        except:
            self.logToMacroWindow(traceback.format_exc())

    @objc.python_method
    def adjustUIElements(self):
        # 計算按鈕文字的寬度
        searchButtonTitle = Glyphs.localize({
            'en': u'Glyph Picker',
            'zh-Hant': u'字符選擇器',
            'zh-Hans': u'字符形选择器',
            'ja': u'グリフ選択ツール',
            'ko': u'글리프 선택기',
            'ar': u'أداة اختيار المحارف',
            'cs': u'Výběr glyfů',
            'de': u'Glyphenauswahl',
            'es': u'Selector de glifos',
            'fr': u'Sélecteur de glyphes',
            'it': u'Selettore di glifi',
            'pt': u'Seletor de glifos',
            'ru': u'Выбор глифа',
            'tr': u'Glif Seçici'
        })
        buttonFont = NSFont.systemFontOfSize_(NSFont.systemFontSize())
        buttonWidth = NSString.stringWithString_(searchButtonTitle).sizeWithAttributes_({NSFontAttributeName: buttonFont}).width

        # 設定最小和最大寬度
        minButtonWidth = 80
        maxButtonWidth = 150
        buttonWidth = max(minButtonWidth, min(buttonWidth + 20, maxButtonWidth))  # 加 20 為左右邊距

        # 獲取當前窗口寬度
        currentSize = self.w.getPosSize()
        windowWidth = currentSize[2]

        # 調整搜索欄位位置和大小
        searchFieldWidth = windowWidth - 20 - buttonWidth - 60 - 20  # 20 是左邊距，60 是深色模式按鈕寬度，20 是按鈕間距
        self.w.searchField.setPosSize((10, -30, searchFieldWidth, 22))

        # 調整按鈕位置和大小
        buttonX = searchFieldWidth + 20
        self.w.searchButton.setPosSize((buttonX, -30, buttonWidth + 10, 22))
        self.w.searchButton.setTitle(searchButtonTitle)

        # 調整深色模式按鈕位置
        darkModeButtonX = buttonX + buttonWidth + 20
        self.w.darkModeButton.setPosSize((darkModeButtonX, -30, -10, 22))

    @objc.python_method
    def windowResized_(self, sender):
        # 當窗口大小改變時，保存新的大小
        newSize = sender.getPosSize()
        Glyphs.defaults["com.YinTzuYuan.NineBoxView.windowSize"] = newSize
        
        # 調整UI元素以適應新的窗口大小
        self.adjustUIElements()

    @objc.python_method
    def windowClosed_(self, sender):
        # 當窗口關閉時，保存窗口大小
        Glyphs.defaults["com.YinTzuYuan.NineBoxView.windowSize"] = sender.getPosSize()
        self.w = None

    @objc.python_method
    def getDarkModeIcon(self):
        return "◐" if self.darkMode else "◑"

    @objc.python_method
    def loadPreferences(self):
        # 載入使用者偏好設定
        self.darkMode = Glyphs.defaults.get("com.YinTzuYuan.NineBoxView.darkMode", False)
        self.lastChar = Glyphs.defaults.get("com.YinTzuYuan.NineBoxView.lastChar", "")
        self.testMode = Glyphs.defaults.get("com.YinTzuYuan.NineBoxView.testMode", False)
        self.searchHistory = Glyphs.defaults.get("com.YinTzuYuan.NineBoxView.search", "")
        self.zoomFactor = Glyphs.defaults.get("com.YinTzuYuan.NineBoxView.zoomFactor", 1.0)

    @objc.python_method
    def savePreferences(self):
        # 儲存使用者偏好設定
        Glyphs.defaults["com.YinTzuYuan.NineBoxView.darkMode"] = self.darkMode
        Glyphs.defaults["com.YinTzuYuan.NineBoxView.lastChar"] = self.lastChar
        Glyphs.defaults["com.YinTzuYuan.NineBoxView.testMode"] = self.testMode
        Glyphs.defaults["com.YinTzuYuan.NineBoxView.search"] = self.searchHistory
        Glyphs.defaults["com.YinTzuYuan.NineBoxView.zoomFactor"] = self.zoomFactor

    @objc.python_method
    def logToMacroWindow(self, message):
        # 將訊息記錄到巨集視窗
        Glyphs.clearLog()
        print(message)

    @objc.python_method
    def updateInterface(self, sender):
        # 更新介面
        if hasattr(self, 'w') and self.w is not None and hasattr(self.w, 'preview'):
            self.w.preview.redraw()

    @objc.python_method
    def searchFieldCallback(self, sender):
        char = sender.get()
        if len(char) > 0:
            self.lastChar = char[0]  # 只取第一個字符
            sender.set(self.lastChar)
        else:
            self.lastChar = ""
        self.savePreferences()
        self.updateInterface(None)

    @objc.python_method
    def darkModeCallback(self, sender):
        # 切換深色模式
        self.darkMode = not self.darkMode
        sender.setTitle(self.getDarkModeIcon())
        self.savePreferences()
        self.updateInterface(None)

    @objc.python_method
    def resetZoom(self):
        # 重置縮放
        self.zoomFactor = 1.0
        self.savePreferences()
        self.updateInterface(None)

    @objc.python_method
    def showWindow(self):
        # 顯示視窗
        if hasattr(self, 'w') and self.w is not None:
            self.w.show()

    @objc.python_method
    def hideWindow(self):
        # 隱藏視窗
        if hasattr(self, 'w') and self.w is not None:
            self.w.hide()

    @objc.python_method
    def __del__(self):
        # 清理資源
        self.savePreferences()
        Glyphs.removeCallback(self.updateInterface, UPDATEINTERFACE)
        Glyphs.removeCallback(self.updateInterface, DOCUMENTACTIVATED)
        NSWorkspace.sharedWorkspace().notificationCenter().removeObserver_(self)

    def __file__(self):
        return __file__