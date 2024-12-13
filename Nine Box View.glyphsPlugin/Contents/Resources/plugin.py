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
from AppKit import NSColor, NSFont, NSAffineTransform, NSRectFill, NSView, NSBezierPath, NSWorkspace, NSClickGestureRecognizer, NSMagnificationGestureRecognizer
from vanilla import FloatingWindow, Group, Button, EditText
import random
import traceback  # 錯誤追蹤 / Error traceback

# === 視圖元件類別 / View Element Classes ===

class NineBoxPreviewView(NSView):
    """
    九宮格預覽視圖類別，負責實際的繪製工作。
    Nine Box Preview View Class, responsible for actual drawing work.
    """

    def drawRect_(self, rect):
        """繪製視圖內容 / Draw the content of the view"""

        try:
            # === 設定背景顏色 ===
            if self.wrapper.plugin.darkMode:
                NSColor.colorWithCalibratedRed_green_blue_alpha_(0, 0, 0, 1.0).set()
            else:
                NSColor.colorWithCalibratedRed_green_blue_alpha_(1.0, 1.0, 1.0, 1.0).set()
            NSRectFill(rect)

            # === 獲取基本參數 ===
            # 獲取當前字體和主字模
            if not Glyphs.font:
                return

            currentMaster = Glyphs.font.selectedFontMaster

            # 使用當前的排列
            display_chars = self.wrapper.plugin.currentArrangement if self.wrapper.plugin.selectedChars else []

            # === 設定基本尺寸 ===
            MARGIN_RATIO = 0.07
            SPACING_RATIO = 0.03

            # 計算字符高度和邊距
            self.cachedHeight = currentMaster.ascender - currentMaster.descender
            MARGIN = min(rect.size.width, rect.size.height) * MARGIN_RATIO

            # === 計算網格尺寸 ===
            # 計算基礎寬度 - 使用當前字體的平均寬度或預設值
            baseWidth = 500  # 預設基礎寬度

            # 如果有選中的字符層,使用其寬度
            if Glyphs.font.selectedLayers:
                baseWidth = Glyphs.font.selectedLayers[0].width

            maxWidth = baseWidth
            if display_chars:
                for char in display_chars:
                    glyph = Glyphs.font.glyphs[char]
                    if glyph and glyph.layers[currentMaster.id]:
                        maxWidth = max(maxWidth, glyph.layers[currentMaster.id].width)

            SPACING = maxWidth * SPACING_RATIO

            # 計算單元格寬度
            cellWidth = maxWidth + SPACING

            # 計算網格總寬度和高度
            gridWidth = 3 * cellWidth + 2 * SPACING
            gridHeight = 3 * self.cachedHeight + 2 * SPACING

            # === 計算縮放比例 ===
            availableWidth = rect.size.width - 2 * MARGIN
            availableHeight = rect.size.height - 2 * MARGIN
            scale = min(availableWidth / gridWidth, availableHeight / gridHeight, 1)

            # 應用自定義縮放
            customScale = self.wrapper.plugin.zoomFactor
            scale *= customScale

            # 更新網格尺寸
            cellWidth *= scale
            gridWidth *= scale
            gridHeight *= scale
            SPACING *= scale

            # 計算繪製起始位置
            startX = rect.size.width / 2 - gridWidth / 2
            offsetY = rect.size.height * 0.05
            startY = (rect.size.height + gridHeight) / 2 + offsetY

            # === 繪製九宮格字符 ===
            for i in range(9):
                row = i // 3
                col = i % 3

                # 計算當前單元格的中心位置
                centerX = startX + (col + 0.5) * cellWidth + col * SPACING
                centerY = startY - (row + 0.5) * (gridHeight / 3)

                # 選擇要繪製的字符層
                layer = None
                if i == 4 and Glyphs.font.selectedLayers:  # 中心位置
                    layer = Glyphs.font.selectedLayers[0]
                else:
                    # 當沒有其他字符時，使用當前編輯的字符填充
                    if not display_chars:
                        if Glyphs.font.selectedLayers:
                            layer = Glyphs.font.selectedLayers[0]
                    else:
                        char_index = i if i < 4 else i - 1
                        if char_index < len(display_chars):
                            glyph = Glyphs.font.glyphs[display_chars[char_index]]
                            layer = glyph.layers[currentMaster.id] if glyph else None

                if layer:
                    # 計算字符縮放比例
                    glyphWidth = layer.width
                    glyphHeight = self.cachedHeight
                    scaleX = cellWidth / glyphWidth if glyphWidth > 0 else 1
                    scaleY = (gridHeight / 3 - SPACING) / glyphHeight if glyphHeight > 0 else 1
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

    def mouseDown_(self, event):
        """
        # 處理滑鼠點擊事件 / Handle mouse click event
        當滑鼠在視圖中點擊時，觸發隨機排列功能。 / When mouse clicked in view, trigger randomize function.
        """

        self.window().makeKeyWindow()
        self.window().makeFirstResponder_(self)
        self.wrapper.plugin.randomizeCallback(self)

class NineBoxPreview(Group):
    """
    九宮格預覽群組類別，用於包裝視圖。
    Nine Box Preview Group Class, used to wrap the View.
    """

    nsViewClass = NineBoxPreviewView

    def __init__(self, posSize, plugin):
        """初始化方法 / Initializer"""
        super(NineBoxPreview, self).__init__(posSize)
        self._nsObject.wrapper = self
        self.plugin = plugin

    def redraw(self):
        """重繪視圖 / Redraw the view"""
        self._nsObject.setNeedsDisplay_(True)

# === 主要外掛類別 / Main Plugin Class ==

class NineBoxView(GeneralPlugin):
    """
    定義主要外掛類別 / Define the main plugin class
    - 視窗操作
    - 界面更新
    - 事件處理
    - 配置管理
    - 工具方法
    - 清理方法
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
        self.selectedChars = []  # 儲存選中的字符 / Store selected characters
        self.currentArrangement = []  # 儲存當前的排列 / Store current arrangement

    @objc.python_method
    def start(self):
        try:
            # 新增選單項 / Add menu item
            newMenuItem = NSMenuItem(self.name, self.toggleWindow_)
            Glyphs.menu[WINDOW_MENU].append(newMenuItem)

            # 新增回調函數
            Glyphs.addCallback(self.updateInterface, UPDATEINTERFACE)
            Glyphs.addCallback(self.updateInterface, DOCUMENTACTIVATED)

            # 新增應用程式啟動和停用的觀察者 / Add observers for application activation and deactivation
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

            # 載入偏好設定並開啟視窗 / Load preferences and open window
            self.loadPreferences()
            self.w.open()
            self.w.makeKey()
        except:
            self.logToMacroWindow(traceback.format_exc())

    # === 視窗操作 / Window Operations ===

    @objc.python_method
    def toggleWindow_(self, sender):
        """切換視窗的顯示狀態 / Toggle the visibility of the window"""

        try:
            if not hasattr(self, 'w') or self.w is None:
                # 載入上次保存的窗口大小，如果沒有則使用預設值
                defaultSize = (300, 340)
                savedSize = Glyphs.defaults.get("com.YinTzuYuan.NineBoxView.windowSize", defaultSize)

                self.w = FloatingWindow(savedSize, self.name, minSize=(200, 240),
                                        autosaveName="com.YinTzuYuan.NineBoxView.mainwindow")
                self.w.preview = NineBoxPreview((0, 0, -0, -60), self)

                placeholder = Glyphs.localize({
                    'en': u'Enter char or leave blank for current',
                    'zh-Hant': u'輸入或留空顯示目前字符',
                    'zh-Hans': u'输入或留空显示当前字符形',
                    'ja': u'文字入力 (空欄で現在の文字)',
                    'ko': u'문자 입력 또는 공백으로 현재 문자',
                    'ar': u'أدخل حرفًا أو اتركه فارغًا للحالي',
                    'cs': u'Zadejte znak nebo nechte prázdné pro aktuální',
                    'de': u'Zeichen eingeben oder leer für aktuelles',
                    'es': u'Ingrese carácter o deje en blanco para el actual',
                    'fr': u"Saisissez un caractère ou laissez vide pour l'actuel",
                    'it': u"Inserisci carattere o lascia vuoto per l'attuale",
                    'pt': u'Digite caractere ou deixe em branco para o atual',
                    'ru': u'Введите символ или оставьте пустым для текущего',
                    'tr': u'Karakter girin veya mevcut için boş bırakın'
                })

                self.w.searchField = EditText((10, -55, -10, 22),
                                            placeholder=placeholder,
                                            callback=self.searchFieldCallback)
                self.w.searchField.set(self.lastChar)

                searchButtonTitle = Glyphs.localize({
                    'en': u'🔣', # Glyph Picker
                    # 'zh-Hant': u'字符選擇器',
                    # 'zh-Hans': u'字符形选择器',
                    # 'ja': u'グリフ選択ツール',
                    # 'ko': u'글리프 선택기',
                    # 'ar': u'أداة اختيار المحارف',
                    # 'cs': u'Výběr glyfů',
                    # 'de': u'Glyphenauswahl',
                    # 'es': u'Selector de glifos',
                    # 'fr': u'Sélecteur de glyphes',
                    # 'it': u'Selettore di glifi',
                    # 'pt': u'Seletor de glifos',
                    # 'ru': u'Выбор глифа',
                    # 'tr': u'Glif Seçici'
                })
                self.w.searchButton = Button((10, -30, 50, 22), searchButtonTitle,
                                            callback=self.pickGlyph)

                self.w.darkModeButton = Button((-60, -30, -10, 22), self.getDarkModeIcon(),
                                            callback=self.darkModeCallback)                #                                           callback=self.randomizeCallback)

                self.w.bind("close", self.windowClosed_)
                self.w.open()

            self.w.makeKey()
            self.updateInterface(None)
        except:
            self.logToMacroWindow(traceback.format_exc())

    @objc.python_method
    def showWindow(self):
        """顯示視窗 / Show the window"""

        if hasattr(self, 'w') and self.w is not None:
            self.w.show()

    @objc.python_method
    def hideWindow(self):
        """隱藏視窗 / Hide the window"""

        if hasattr(self, 'w') and self.w is not None:
            self.w.hide()

    @objc.python_method
    def windowClosed_(self, sender):
        """當窗口關閉時，保存窗口大小。 / Save window size when window is closed."""

        Glyphs.defaults["com.YinTzuYuan.NineBoxView.windowSize"] = sender.getPosSize()
        self.w = None

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

        if hasattr(self, 'w') and self.w is not None and hasattr(self.w, 'preview'):
            self.w.preview.redraw()

    # @objc.python_method
    # def resetZoom(self):
    #     """
    #     重置縮放 / Reset zoom
    #     """
    #     self.zoomFactor = 1.0
    #     self.savePreferences()
    #     self.updateInterface(None)

    # === 事件處理 / Event Handling ===

    @objc.python_method
    def searchFieldCallback(self, sender):
        """處理輸入框的回調函數 / Callback function for the input field"""

        # 檢查是否有開啟字型檔案
        if not Glyphs.font:
            print("Warning: No font file is open")
            return

        input_text = sender.get().strip()

        if input_text:
            # 解析輸入文字，獲取所有有效字符
            self.selectedChars = self.parseInputText(input_text)
            # 生成新的隨機排列
            self.generateNewArrangement()
            # 保持輸入框的原始內容
            sender.set(input_text)

            if not self.selectedChars:
                print("Warning: No valid glyphs found in input")
        else:
            self.selectedChars = []
            self.currentArrangement = []
            sender.set("")

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
        sender.setTitle(self.getDarkModeIcon())
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
                self.lastChar,
                # None,
                "com.YinTzuYuan.NineBoxView.search"
            )

            if choice and choice[0]:  # 確保有選擇結果
                # 收集所有選擇的字符
                selected_chars = []
                for selection in choice[0]:  # choice[0] 是選擇的字形列表
                    if isinstance(selection, GSGlyph):  # 確認是 GSGlyph 物件
                        # 優先使用 Unicode 值，若無則使用字形名稱
                        char = selection.unicode or selection.name
                        selected_chars.append(char)

                if selected_chars:
                    # 用空格連接所有字符
                    current_text = self.w.searchField.get()
                    cursor_position = self.w.searchField.getSelection()[0]
                    new_text = current_text[:cursor_position] + ' '.join(selected_chars) + current_text[cursor_position:]
                    self.w.searchField.set(new_text)

                    # 更新游標位置
                    new_cursor_position = cursor_position + len(' '.join(selected_chars))
                    self.w.searchField.setSelection((new_cursor_position, new_cursor_position))

                    self.updateInterface(None)
        except Exception as e:
            print(f"Error in pickGlyph: {str(e)}")


    # === 配置管理 / Configuration Management ===

    @objc.python_method
    def loadPreferences(self):
        """載入使用者偏好設定 / Load user preferences"""

        self.darkMode = Glyphs.defaults.get("com.YinTzuYuan.NineBoxView.darkMode", False)
        self.lastChar = Glyphs.defaults.get("com.YinTzuYuan.NineBoxView.lastChar", "")
        self.selectedChars = Glyphs.defaults.get("com.YinTzuYuan.NineBoxView.selectedChars", [])
        self.currentArrangement = Glyphs.defaults.get("com.YinTzuYuan.NineBoxView.currentArrangement", [])
        self.testMode = Glyphs.defaults.get("com.YinTzuYuan.NineBoxView.testMode", False)
        self.searchHistory = Glyphs.defaults.get("com.YinTzuYuan.NineBoxView.search", "")
        self.zoomFactor = Glyphs.defaults.get("com.YinTzuYuan.NineBoxView.zoomFactor", 1.0)

    @objc.python_method
    def savePreferences(self):
        """儲存使用者偏好設定 / Save user preferences"""

        Glyphs.defaults["com.YinTzuYuan.NineBoxView.darkMode"] = self.darkMode
        Glyphs.defaults["com.YinTzuYuan.NineBoxView.lastChar"] = self.lastChar
        Glyphs.defaults["com.YinTzuYuan.NineBoxView.selectedChars"] = self.selectedChars
        Glyphs.defaults["com.YinTzuYuan.NineBoxView.currentArrangement"] = self.currentArrangement
        Glyphs.defaults["com.YinTzuYuan.NineBoxView.testMode"] = self.testMode
        Glyphs.defaults["com.YinTzuYuan.NineBoxView.search"] = self.searchHistory
        Glyphs.defaults["com.YinTzuYuan.NineBoxView.zoomFactor"] = self.zoomFactor


    # === 工具方法 / Utility Methods ===

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

        # 檢查是否有開啟字型檔案
        if not Glyphs.font:
            print("Warning: No font file is open")
            return []

        chars = []

        # 分割輸入文字，用空格作為分隔符 / Split the input text, use space as the separator
        parts = text.strip().split(' ')

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
                        print(f"Warning: No glyph found for '{char}'")
            else:
                # 對於 ASCII 字符名稱，整體處理 / For ASCII glyph names, process as a whole
                if Glyphs.font.glyphs[part]:
                    chars.append(part)
                else:
                    print(f"Warning: No glyph found for '{part}'")

        return chars

    @objc.python_method
    def generateNewArrangement(self):
        """
        生成新的隨機排列 / Generate a new random arrangement
        """

        display_chars = list(self.selectedChars)  # 複製一份字符列表

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

    # === 清理方法 / Cleanup ===

    @objc.python_method
    def __del__(self):
        """
        清理資源 / Clean up resources
        """

        self.savePreferences()
        Glyphs.removeCallback(self.updateInterface, UPDATEINTERFACE)
        Glyphs.removeCallback(self.updateInterface, DOCUMENTACTIVATED)
        NSWorkspace.sharedWorkspace().notificationCenter().removeObserver_(self)

    def __file__(self):
        return __file__
