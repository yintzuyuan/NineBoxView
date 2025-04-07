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

# 只有在 Glyphs.app 中運行時才會執行
# Will only run in Glyphs.app

import traceback

try:
    import objc
    from Foundation import NSObject, NSNotificationCenter
    from AppKit import NSMenuItem
    from GlyphsApp import *
    from GlyphsApp.plugins import *
    
    # 設定 GeneralPlugin 子類別
    class NineBoxView(GeneralPlugin):
        """
        定義主要外掛類別
        Nine Box Preview Plugin - Main Class
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
            
            # 導入所有實際功能模組
            # 在 settings 中進行導入以避免循環依賴問題
            from constants import (
                DARK_MODE_KEY, LAST_INPUT_KEY, SELECTED_CHARS_KEY, 
                CURRENT_ARRANGEMENT_KEY, TEST_MODE_KEY, SEARCH_HISTORY_KEY,
                ZOOM_FACTOR_KEY, SHOW_NUMBERS_KEY, WINDOW_SIZE_KEY,
                DEFAULT_WINDOW_SIZE, MIN_WINDOW_SIZE, DEFAULT_ZOOM
            )
            
            from utils import parse_input_text, generate_arrangement, get_base_width, log_to_macro_window
            from window_controller import NineBoxWindow
            
            # 儲存到 self 中供後續使用
            self.NineBoxWindow = NineBoxWindow
            self.parse_input_text = parse_input_text
            self.generate_arrangement = generate_arrangement
            self.get_base_width = get_base_width
            self.log_to_macro_window = log_to_macro_window
            
            # 常數導入
            self.DARK_MODE_KEY = DARK_MODE_KEY
            self.LAST_INPUT_KEY = LAST_INPUT_KEY
            self.SELECTED_CHARS_KEY = SELECTED_CHARS_KEY
            self.CURRENT_ARRANGEMENT_KEY = CURRENT_ARRANGEMENT_KEY
            self.TEST_MODE_KEY = TEST_MODE_KEY
            self.SEARCH_HISTORY_KEY = SEARCH_HISTORY_KEY
            self.ZOOM_FACTOR_KEY = ZOOM_FACTOR_KEY
            self.SHOW_NUMBERS_KEY = SHOW_NUMBERS_KEY
            self.WINDOW_SIZE_KEY = WINDOW_SIZE_KEY
            self.DEFAULT_ZOOM = DEFAULT_ZOOM
            
            self.loadPreferences()
            self.selectedChars = []  # 儲存選取的字符 / Store selected characters
            self.currentArrangement = []  # 儲存目前的排列 / Store current arrangement
            self.windowController = None  # 視窗控制器 / Window controller
            
            # 印出一條訊息確認外掛已被載入
            print("九宮格預覽外掛已成功載入。")

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
            except Exception as e:
                print(f"啟動外掛時發生錯誤: {str(e)}")
                print(traceback.format_exc())

        # === 視窗操作 / Window Operations ===

        @objc.python_method
        def toggleWindow_(self, sender):
            """切換視窗的顯示狀態 / Toggle the visibility of the window"""

            try:
                # 如果視窗不存在，則建立 / If window doesn't exist, create it
                if self.windowController is None:
                    self.windowController = self.NineBoxWindow.alloc().initWithPlugin_(self)
                    
                # 顯示視窗 / Show window
                self.windowController.makeKeyAndOrderFront()
                self.updateInterface(None)
            except Exception as e:
                print(f"切換視窗時發生錯誤: {str(e)}")
                print(traceback.format_exc())

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

            self.log_to_macro_window(message)

        # === 界面更新 / Interface Update ===

        @objc.python_method
        def updateInterface(self, sender):
            """更新界面 / Update interface"""
            try:
                # 更新深色模式按鈕圖標 / Update dark mode button icon
                if hasattr(self, 'windowController') and self.windowController is not None:
                    # 檢查屬性是否存在
                    if hasattr(self.windowController, 'darkModeButton') and self.windowController.darkModeButton is not None:
                        darkModeButton = self.windowController.darkModeButton
                        darkModeButton.setTitle_(self.getDarkModeIcon())
                        # 設定按鈕狀態 / Set button state
                        if self.darkMode:
                            darkModeButton.setState_(1)  # 1 表示開啟
                        else:
                            darkModeButton.setState_(0)  # 0 表示關閉
                    
                    # 重繪介面 / Redraw interface
                    if hasattr(self.windowController, 'redraw'):
                        self.windowController.redraw()
            except Exception as e:
                self.log_to_macro_window(f"更新介面時發生錯誤: {e}")
                print(traceback.format_exc())

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
                new_chars = self.parse_input_text(input_text)

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
        def pickGlyphCallback(self, sender):
            """選擇字符按鈕的回調函數 / Callback function for the pick glyph button"""
            try:
                if not Glyphs.font:
                    print("警告：沒有開啟字型檔案")
                    return
                
                # 取得目前字型檔案中的所有字符 / Get all glyphs in the current font
                all_glyphs = Glyphs.font.glyphs
                glyph_names = [glyph.name for glyph in all_glyphs]
                
                # 建立選項清單 / Create a list of options
                options = []
                for name in glyph_names:
                    # 構建顯示名稱 / Build display name
                    glyph = Glyphs.font.glyphs[name]
                    if glyph:
                        unicode_value = glyph.unicode
                        if unicode_value:
                            char = chr(int(unicode_value, 16))
                            options.append(f"{char} ({name})")
                        else:
                            options.append(f".notdef ({name})")
                
                # 顯示選項對話窗 / Show options dialog
                if options:
                    selection = Glyphs.displayDialog(
                        Glyphs.localize({
                            'en': u'Select characters to display in the grid',
                            'zh-Hant': u'選擇要在格子中顯示的字符',
                            'zh-Hans': u'选择要在格子中显示的字符',
                            'ja': u'グリッドに表示する文字を選択してください',
                            'ko': u'그리드에 표시할 글자를 선택하세요',
                        }),
                        options,
                        "OK",
                        multipleSelection=True
                    )
                    
                    if selection:
                        # 解析選取的字符並更新 / Parse selected characters and update
                        selected_chars = []
                        for selected in selection:
                            # 從字串中提取字符名稱 / Extract glyph name from string
                            if "(" in selected and ")" in selected:
                                name = selected.split("(")[1].split(")")[0]
                                glyph = Glyphs.font.glyphs[name]
                                if glyph and glyph.unicode:
                                    selected_chars.append(chr(int(glyph.unicode, 16)))
                        
                        # 更新選取的字符 / Update selected characters
                        if selected_chars != self.selectedChars:
                            self.selectedChars = selected_chars
                            
                            # 生成新的字符排列 / Generate a new character arrangement
                            self.generateNewArrangement()
                            
                            # 更新搜尋欄位 / Update search field
                            if hasattr(self, 'windowController') and hasattr(self.windowController, 'searchField'):
                                self.windowController.searchField.setStringValue_(" ".join(selected_chars))
                                self.lastInput = " ".join(selected_chars)
                            
                            self.savePreferences()
                            self.updateInterface(None)
            except Exception as e:
                print(f"選擇字符時發生錯誤: {e}")
                print(traceback.format_exc())
                
        @objc.python_method
        def randomizeCallback(self, sender):
            """隨機排列回調函數 / Randomization callback function"""
            
            if not self.selectedChars:
                return
                
            # 生成新的排列 / Generate a new arrangement
            self.generateNewArrangement()
            
            # 重繪預覽 / Redraw preview
            self.updateInterface(None)

        @objc.python_method
        def generateNewArrangement(self):
            """生成新的字符排列 / Generate a new character arrangement"""

            if not self.selectedChars:
                self.currentArrangement = []
                return

            # 從選取的字符中生成新排列 / Generate a new arrangement from selected characters
            self.currentArrangement = self.generate_arrangement(self.selectedChars)

        @objc.python_method
        def loadPreferences(self):
            """載入偏好設定 / Load preferences"""

            # 深色模式設定 / Dark mode setting
            self.darkMode = bool(Glyphs.defaults.get(self.DARK_MODE_KEY, False))

            # 最後輸入的字符 / Last input characters
            self.lastInput = Glyphs.defaults.get(self.LAST_INPUT_KEY, "")

            # 選取的字符 / Selected characters
            selected_chars = Glyphs.defaults.get(self.SELECTED_CHARS_KEY)
            if selected_chars:
                self.selectedChars = selected_chars
            else:
                self.selectedChars = []

            # 目前的排列 / Current arrangement
            current_arrangement = Glyphs.defaults.get(self.CURRENT_ARRANGEMENT_KEY)
            if current_arrangement:
                self.currentArrangement = current_arrangement
            else:
                self.currentArrangement = []
                
            # 縮放因子 / Zoom factor
            self.zoomFactor = float(Glyphs.defaults.get(self.ZOOM_FACTOR_KEY, self.DEFAULT_ZOOM))

        @objc.python_method
        def savePreferences(self):
            """儲存偏好設定 / Save preferences"""

            # 儲存深色模式設定 / Save dark mode setting
            Glyphs.defaults[self.DARK_MODE_KEY] = self.darkMode

            # 儲存最後輸入的字符 / Save last input characters
            Glyphs.defaults[self.LAST_INPUT_KEY] = self.lastInput

            # 儲存選取的字符 / Save selected characters
            Glyphs.defaults[self.SELECTED_CHARS_KEY] = self.selectedChars

            # 儲存目前的排列 / Save current arrangement
            Glyphs.defaults[self.CURRENT_ARRANGEMENT_KEY] = self.currentArrangement
            
            # 儲存縮放因子 / Save zoom factor
            Glyphs.defaults[self.ZOOM_FACTOR_KEY] = self.zoomFactor

        # === 回調函數 / Callback Functions ===

        @objc.python_method
        def darkModeCallback(self, sender):
            """深色模式切換回調函數 / Dark mode toggle callback function"""
            self.darkMode = not self.darkMode
            self.savePreferences()
            self.updateInterface(None)

        @objc.python_method
        def toggleShowNumbers(self, sender):
            """切換顯示數字的回調函數 / Toggle show numbers callback"""
            
            self.showNumbers = not self.showNumbers
            self.savePreferences()
            self.updateInterface(None)

        @objc.python_method
        def resetZoom(self, sender):
            """重置縮放的回調函數 / Reset zoom callback"""
            
            self.zoomFactor = self.DEFAULT_ZOOM
            self.savePreferences()
            self.updateInterface(None)

        # === 輔助函數 / Helper Functions ===

        @objc.python_method
        def getBaseWidth(self):
            """
            取得基準寬度
            Get base width
            
            基於目前字型檔案的矩形寬度或預設 UPM
            Based on the width of the rect in the current font file or default UPM
            
            Returns:
                float: 基準寬度
            """
            return self.get_base_width()

        @objc.python_method
        def systemAppearanceIsDark(self):
            """
            檢查系統外觀是否為深色模式
            Check if system appearance is dark mode
            
            Returns:
                bool: 系統是否為深色模式
            """
            try:
                from AppKit import NSAppearanceNameDarkAqua, NSApplication
                return NSApplication.sharedApplication().effectiveAppearance().name() == NSAppearanceNameDarkAqua
            except:
                return False

        # === 外掛終止 / Plugin Termination ===

        @objc.python_method
        def __del__(self):
            """
            外掛終止時的清理 / Cleanup when this plugin instance is deleted
            """
            Glyphs.removeCallback(self.updateInterface, DOCUMENTACTIVATED)
            Glyphs.removeCallback(self.updateInterface, UPDATEINTERFACE)

        @objc.python_method
        def __file__(self):
            """
            外掛檔案路徑 / Plugin file path
            """
            from os.path import dirname
            return dirname(__file__)

except Exception as e:
    import traceback
    print(f"插件載入時發生錯誤，{e}")
    print(traceback.format_exc())
