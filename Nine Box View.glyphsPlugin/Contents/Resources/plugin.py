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
                DEFAULT_WINDOW_SIZE, MIN_WINDOW_SIZE
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
                    self.SEARCH_HISTORY_KEY
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

            self.darkMode = Glyphs.defaults.get(self.DARK_MODE_KEY, False)
            self.lastInput = Glyphs.defaults.get(self.LAST_INPUT_KEY, "")
            self.selectedChars = Glyphs.defaults.get(self.SELECTED_CHARS_KEY, [])
            self.currentArrangement = Glyphs.defaults.get(self.CURRENT_ARRANGEMENT_KEY, [])
            self.testMode = Glyphs.defaults.get(self.TEST_MODE_KEY, False)
            self.searchHistory = Glyphs.defaults.get(self.SEARCH_HISTORY_KEY, "")
            self.zoomFactor = Glyphs.defaults.get(self.ZOOM_FACTOR_KEY, 1.0)
            self.showNumbers = Glyphs.defaults.get(self.SHOW_NUMBERS_KEY, False)

        @objc.python_method
        def savePreferences(self):
            """儲存使用者偏好設定 / Save user preferences"""

            Glyphs.defaults[self.DARK_MODE_KEY] = self.darkMode
            Glyphs.defaults[self.LAST_INPUT_KEY] = self.lastInput
            Glyphs.defaults[self.SELECTED_CHARS_KEY] = self.selectedChars
            Glyphs.defaults[self.CURRENT_ARRANGEMENT_KEY] = self.currentArrangement
            Glyphs.defaults[self.TEST_MODE_KEY] = self.testMode
            Glyphs.defaults[self.SEARCH_HISTORY_KEY] = self.searchHistory
            Glyphs.defaults[self.ZOOM_FACTOR_KEY] = self.zoomFactor
            Glyphs.defaults[self.SHOW_NUMBERS_KEY] = self.showNumbers

        # === 工具方法 / Utility Methods ===

        @objc.python_method
        def getBaseWidth(self):
            """取得基準寬度 / Get the base width"""
            return self.get_base_width()

        @objc.python_method
        def generateNewArrangement(self):
            """生成新的隨機排列 / Generate a new random arrangement"""
            self.currentArrangement = self.generate_arrangement(self.selectedChars)
            self.savePreferences()

        # === 清理方法 / Cleanup ===

        @objc.python_method
        def __del__(self):
            """清理資源 / Clean up resources"""

            self.savePreferences()
            Glyphs.removeCallback(self.updateInterface, UPDATEINTERFACE)
            Glyphs.removeCallback(self.updateInterface, DOCUMENTACTIVATED)
            NSNotificationCenter.defaultCenter().removeObserver_(self)

        def __file__(self):
            return __file__

except Exception as e:
    print(f"載入九宮格預覽外掛時發生錯誤: {str(e)}")
    import traceback
    print(traceback.format_exc())
