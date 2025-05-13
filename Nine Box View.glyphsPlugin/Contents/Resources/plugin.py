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
            # === 設定背景顏色 / Set the background color ===
            if self.wrapper.plugin.darkMode:
                NSColor.colorWithCalibratedRed_green_blue_alpha_(0, 0, 0, 1.0).set()
            else:
                NSColor.colorWithCalibratedRed_green_blue_alpha_(1.0, 1.0, 1.0, 1.0).set()
            NSRectFill(rect)

            # === 取得基本參數 / Get basic parameters ===
            # 取得目前字型和主板 / Get the current font and master
            if not Glyphs.font:
                return

            currentMaster = Glyphs.font.selectedFontMaster

            # 使用目前的排列 / Use the current arrangement
            display_chars = self.wrapper.plugin.currentArrangement if self.wrapper.plugin.selectedChars else []

            # === 設定基本尺寸 / Set basic sizes ===
            MARGIN_RATIO = 0.07
            SPACING_RATIO = 0.03

            # 計算字符高度和邊距 / Calculate the character height and margin
            self.cachedHeight = currentMaster.ascender - currentMaster.descender
            MARGIN = min(rect.size.width, rect.size.height) * MARGIN_RATIO

            # === 計算網格尺寸 / Calculate the grid size ===
            # 使用 getBaseWidth 方法取得基準寬度
            baseWidth = self.wrapper.plugin.getBaseWidth()

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
            customScale = self.wrapper.plugin.zoomFactor
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
                    if self.wrapper.plugin.darkMode:
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

    @objc.python_method
    def start(self):
        try:
            # 新增選單項 / Add menu item
            newMenuItem = NSMenuItem(self.name, self.toggleWindow_)
            Glyphs.menu[WINDOW_MENU].append(newMenuItem)

            # 新增回調函數
            Glyphs.addCallback(self.updateInterface, UPDATEINTERFACE)
            Glyphs.addCallback(self.updateInterface, DOCUMENTACTIVATED)

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
                # 確保已載入偏好設定 / Make sure the preferences are loaded
                self.loadPreferences()

                # 載入上次儲存的視窗大小，如果沒有則使用預設值 / Load the last saved window size, or use the default value
                defaultSize = (300, 340)
                savedSize = Glyphs.defaults.get("com.YinTzuYuan.NineBoxView.windowSize", defaultSize)

                self.w = FloatingWindow(savedSize, self.name, minSize=(200, 240),
                                        autosaveName="com.YinTzuYuan.NineBoxView.mainwindow")
                self.w.preview = NineBoxPreview((0, 0, -0, -35), self)

                placeholder = Glyphs.localize({
                    'en': u'Input glyphs (space-separated) or leave blank',
                    'zh-Hant': u'輸入字符（以空格分隔）或留空',
                    'zh-Hans': u'输入字符（用空格分隔）或留空',
                    'ja': u'文字を入力してください（スペースで区切る）または空欄のまま',
                    'ko': u'문자를 입력하세요 (공백으로 구분) 또는 비워 두세요',
                })

                # 使用 lastInput 設定輸入框的初始內容 / Use lastInput to set the initial content of the input field
                self.w.searchField = EditText(
                    (10, -30, -100, 22),
                    text=self.lastInput,  # 使用儲存的最後輸入 / Use the last saved input
                    placeholder=placeholder,
                    callback=self.searchFieldCallback
                )

                self.w.searchButton = Button((-95, -30, -55, 22), "🔣",
                                            callback=self.pickGlyph)

                self.w.darkModeButton = Button((-50, -30, -10, 22),
                                                self.getDarkModeIcon(),
                                                callback=self.darkModeCallback)

                self.w.bind("close", self.windowClosed_)

                # 如果沒有現有排列但有選取的字符，則生成新排列 / Generate a new arrangement if there is no existing arrangement but there are selected characters
                if self.selectedChars and not self.currentArrangement:
                    self.generateNewArrangement()

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
        """當視窗關閉時，儲存設定。 / Save settings when the window is closed."""

        # 儲存目前輸入內容 / Save the current input content
        self.lastInput = self.w.searchField.get()
        self.savePreferences()

        # 儲存視窗大小 / Save the window size
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

    # === 事件處理 / Event Handling ===

    @objc.python_method
    def searchFieldCallback(self, sender):
        """處理輸入框的回調函數 / Callback function for the input field"""

        # 檢查是否有開啟字型檔案
        if not Glyphs.font:
            print("Warning: No font file is open")
            return

        # 取得目前輸入 / Get the current input
        input_text = sender.get()

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
                self.searchHistory,
                "com.YinTzuYuan.NineBoxView.search"
            )

            if choice and choice[0]:
                selected_chars = []
                for selection in choice[0]:
                    if isinstance(selection, GSGlyph):
                        # 直接使用字符名稱 / Use the glyph name directly
                        selected_chars.append(selection.name)

                if selected_chars:
                    # 取得目前文字 / Get the current text
                    textfield = self.w.searchField.getNSTextField()
                    editor = textfield.currentEditor()
                    current_text = self.w.searchField.get()

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
                    self.w.searchField.set(new_text)

                    # 更新游標位置到插入內容之後 / Update the cursor position to after the inserted content
                    new_position = cursor_position + len(chars_to_insert)
                    if editor:
                        editor.setSelectedRange_((new_position, new_position))

                    # 觸發 searchFieldCallback 以更新界面 / Trigger searchFieldCallback to update the interface
                    self.searchFieldCallback(self.w.searchField)

        except Exception as e:
            print(f"Error in pickGlyph: {str(e)}")
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


    # === 工具方法 / Utility Methods ===

    @objc.python_method
    def getBaseWidth(self):
        """取得基準寬度 / Get the base width"""
        if not Glyphs.font:
            return 1000

        currentMaster = Glyphs.font.selectedFontMaster

        # 1. 檢查主板是否有 Default Layer Width 參數
        defaultWidth = None
        try:
            if 'Default Layer Width' in currentMaster.customParameters:
                # 取得參數值
                width_param = currentMaster.customParameters['Default Layer Width']
                
                # 處理可能帶有腳本前綴的格式，如 'han: 950'
                if isinstance(width_param, str) and ':' in width_param:
                    # 分割腳本和寬度值
                    parts = width_param.split(':', 1)
                    if len(parts) == 2:
                        width_str = parts[1].strip()
                        
                        # 嘗試轉換寬度值部分
                        try:
                            defaultWidth = float(width_str)
                        except (ValueError, TypeError):
                            pass
                else:
                    # 直接嘗試轉換為浮點數
                    try:
                        defaultWidth = float(width_param)
                    except (ValueError, TypeError):
                        pass
                
                # 如果成功解析到寬度值，直接返回
                if defaultWidth and defaultWidth > 0:
                    return defaultWidth
        except Exception:
            pass

        # 2. 使用選取的字符層寬度
        try:
            if Glyphs.font.selectedLayers:
                return Glyphs.font.selectedLayers[0].width
        except Exception:
            pass

        # 3. 使用字型的 UPM (units per em) 值
        try:
            if hasattr(Glyphs.font, 'upm'):
                return max(Glyphs.font.upm, 500)
        except Exception:
            pass

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
            print("Warning: No font file is open")
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
