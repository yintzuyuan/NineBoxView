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
    from Foundation import NSObject, NSNotificationCenter, NSUserDefaultsDidChangeNotification
    from AppKit import NSMenuItem, NSUserDefaults
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
                LAST_INPUT_KEY, SELECTED_CHARS_KEY, 
                CURRENT_ARRANGEMENT_KEY, TEST_MODE_KEY, SEARCH_HISTORY_KEY,
                ZOOM_FACTOR_KEY, SHOW_NUMBERS_KEY, WINDOW_SIZE_KEY,
                DEFAULT_WINDOW_SIZE, MIN_WINDOW_SIZE, DEFAULT_ZOOM,
                SIDEBAR_VISIBLE_KEY, SIDEBAR_WIDTH
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
            self.LAST_INPUT_KEY = LAST_INPUT_KEY
            self.SELECTED_CHARS_KEY = SELECTED_CHARS_KEY
            self.CURRENT_ARRANGEMENT_KEY = CURRENT_ARRANGEMENT_KEY
            self.TEST_MODE_KEY = TEST_MODE_KEY
            self.SEARCH_HISTORY_KEY = SEARCH_HISTORY_KEY
            self.ZOOM_FACTOR_KEY = ZOOM_FACTOR_KEY
            self.SHOW_NUMBERS_KEY = SHOW_NUMBERS_KEY
            self.WINDOW_SIZE_KEY = WINDOW_SIZE_KEY
            self.SIDEBAR_VISIBLE_KEY = SIDEBAR_VISIBLE_KEY
            self.DEFAULT_ZOOM = DEFAULT_ZOOM
            
            self.loadPreferences()
            self.selectedChars = []  # 儲存選取的字符 / Store selected characters
            self.currentArrangement = []  # 儲存目前的排列 / Store current arrangement
            self.windowController = None  # 視窗控制器 / Window controller
            
            # 註冊 NSUserDefaults 變更通知
            self.registerUserDefaultsObserver()
            
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
                Glyphs.addCallback(self.selectionChanged_, DOCUMENTOPENED)
                Glyphs.addCallback(self.selectionChanged_, SELECTIONCHANGED)

                # 載入偏好設定 / Load preferences
                self.loadPreferences()
            except Exception as e:
                print(f"啟動外掛時發生錯誤: {str(e)}")
                print(traceback.format_exc())

        # === 系統明暗模式變更監聽 / System Dark Mode Change Listener ===
        
        @objc.python_method
        def registerUserDefaultsObserver(self):
            """註冊 NSUserDefaults 變更通知觀察者 / Register NSUserDefaults change notification observer"""
            try:
                # 監聽 NSUserDefaults 變更通知
                NSNotificationCenter.defaultCenter().addObserver_selector_name_object_(
                    self,
                    "userDefaultsDidChange:",
                    NSUserDefaultsDidChangeNotification,
                    None
                )
                print("已註冊 NSUserDefaults 變更通知觀察者")
            except Exception as e:
                print(f"註冊 NSUserDefaults 變更通知觀察者時發生錯誤: {str(e)}")
                print(traceback.format_exc())
        
        def userDefaultsDidChange_(self, notification):
            """處理 NSUserDefaults 變更通知 / Handle NSUserDefaults change notification"""
            try:
                # 檢查是否變更了深色模式設定 / Check if dark mode setting has changed
                currentDarkMode = NSUserDefaults.standardUserDefaults().boolForKey_("GSPreview_Black")
                
                # 檢查深色模式設定是否已變更
                if hasattr(self, 'lastDarkModeSetting') and self.lastDarkModeSetting != currentDarkMode:
                    print(f"深色模式設定已變更: {currentDarkMode}")
                    
                    # 更新深色模式設定記錄
                    self.lastDarkModeSetting = currentDarkMode
                    
                    # 只有在視窗控制器存在且可見時才更新介面
                    if hasattr(self, 'windowController') and self.windowController is not None:
                        # 獲取視窗是否可見
                        if self.windowController.window() and self.windowController.window().isVisible():
                            print("更新九宮格預覽介面")
                            self.updateInterface(None)
                
                # 如果尚未儲存當前設定，則進行儲存
                elif not hasattr(self, 'lastDarkModeSetting'):
                    self.lastDarkModeSetting = currentDarkMode
                
            except Exception as e:
                print(f"處理 NSUserDefaults 變更通知時發生錯誤: {str(e)}")
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
        def logToMacroWindow(self, message):
            """將訊息記錄到巨集視窗 / Log message to the Macro Window"""

            self.log_to_macro_window(message)

        # === 界面更新 / Interface Update ===

        @objc.python_method
        def updateInterface(self, sender):
            """更新界面 / Update interface"""
            try:
                if hasattr(self, 'windowController') and self.windowController is not None:
                    # 重繪介面 / Redraw interface
                    if hasattr(self.windowController, 'redraw'):
                        self.windowController.redraw()
            except Exception as e:
                self.log_to_macro_window(f"更新介面時發生錯誤: {e}")
                print(traceback.format_exc())
        
        @objc.python_method
        def selectionChanged_(self, sender):
            """選擇變更時的處理 / Handle selection changes"""
            try:
                # 重繪介面
                self.updateInterface(None)
                
                # 更新側邊欄字型資訊
                if hasattr(self, 'windowController') and self.windowController is not None:
                    if (hasattr(self.windowController, 'sidebarView') and 
                        self.windowController.sidebarView is not None and
                        not self.windowController.sidebarView.isHidden()):
                        self.windowController.sidebarView.updateFontInfo()
            except Exception as e:
                print(f"選擇變更處理時發生錯誤: {e}")
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
                            'en': u'Select glyphs (use Shift/Cmd for multiple selections)',
                            'zh-Hant': u'選擇字符（使用 Shift/Cmd 進行多選）',
                            'zh-Hans': u'选择字符（使用 Shift/Cmd 进行多选）',
                            'ja': u'グリフを選択（複数選択には Shift/Cmd を使用）',
                            'ko': u'글자 선택 (여러 개를 선택하려면 Shift/Cmd 사용)',
                        }),
                        options,
                        allowsMultipleSelection=True
                    )
                    
                    if selection:
                        # 解析選擇的字符 / Parse selected glyphs
                        selected_chars = []
                        for item in selection:
                            # 從顯示名稱中提取字符 / Extract character from display name
                            if " (" in item and ")" in item:
                                char = item.split(" (")[0]
                                if char != ".notdef":
                                    selected_chars.append(char)
                        
                        # 更新選取的字符列表 / Update selected character list
                        if selected_chars:
                            self.selectedChars = selected_chars
                            # 產生新排列 / Generate new arrangement
                            self.generateNewArrangement()
                            # 更新側邊欄中的字符輸入欄位
                            self.lastInput = " ".join(selected_chars)
                            if hasattr(self, 'windowController') and self.windowController:
                                if hasattr(self.windowController, 'sidebarView') and self.windowController.sidebarView:
                                    self.windowController.sidebarView.updateSearchField()
                            # 儲存偏好設定 / Save preferences
                            self.savePreferences()
                            # 更新介面 / Update interface
                            self.updateInterface(None)
            except Exception as e:
                print(f"選擇字符時發生錯誤: {e}")
                print(traceback.format_exc())

        @objc.python_method
        def randomizeCallback(self, sender):
            """隨機排列按鈕的回調函數 / Callback function for the randomize button"""
            
            if not self.selectedChars:
                if Glyphs.font and Glyphs.font.selectedLayers:
                    # 如果沒有選擇字符，但有選擇圖層，使用之前的處理方法
                    # If no characters are selected but a layer is selected, use the previous handling method
                    self.updateInterface(None)
                return
            
            # 使用生成器函數生成新的排列 / Use the generator function to generate a new arrangement
            self.generateNewArrangement()
            
            # 更新介面 / Update interface
            self.updateInterface(None)

        @objc.python_method
        def generateNewArrangement(self):
            """生成新的字符排列 / Generate a new character arrangement"""
            
            if self.selectedChars:
                # 產生新的隨機排列 / Generate a new random arrangement
                self.currentArrangement = self.generate_arrangement(self.selectedChars, 8)
                self.savePreferences()  # 儲存偏好設定 / Save preferences

        @objc.python_method
        def loadPreferences(self):
            """載入偏好設定 / Load preferences"""

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
            
            # 側邊欄可見性 / Sidebar visibility
            self.sidebarVisible = bool(Glyphs.defaults.get(self.SIDEBAR_VISIBLE_KEY, True))  # 預設開啟側邊欄

        @objc.python_method
        def savePreferences(self):
            """儲存偏好設定 / Save preferences"""

            # 儲存最後輸入的字符 / Save last input characters
            Glyphs.defaults[self.LAST_INPUT_KEY] = self.lastInput

            # 儲存選取的字符 / Save selected characters
            Glyphs.defaults[self.SELECTED_CHARS_KEY] = self.selectedChars

            # 儲存目前的排列 / Save current arrangement
            Glyphs.defaults[self.CURRENT_ARRANGEMENT_KEY] = self.currentArrangement
            
            # 儲存縮放因子 / Save zoom factor
            Glyphs.defaults[self.ZOOM_FACTOR_KEY] = self.zoomFactor
            
            # 儲存側邊欄可見性 / Save sidebar visibility
            Glyphs.defaults[self.SIDEBAR_VISIBLE_KEY] = self.sidebarVisible

        @objc.python_method
        def resetZoom(self, sender):
            """重置縮放的回調函數 / Reset zoom callback"""
            
            self.zoomFactor = self.DEFAULT_ZOOM
            self.savePreferences()
            self.updateInterface(None)

        @objc.python_method
        def getBaseWidth(self):
            """取得字符的基本寬度作為參考 / Get the base width of characters for reference"""
            
            if Glyphs.font:
                # 取得所有主要的度量資訊
                currentMaster = Glyphs.font.selectedFontMaster
                if currentMaster:
                    height = currentMaster.ascender - currentMaster.descender
                    # 以1:1的寬高比作為基礎字符寬度
                    return height
            
            # 若無法取得，使用預設值1000
            return 1000
            
        @objc.python_method
        def __del__(self):
            """析構函數，處理清理工作 / Destructor, handle cleanup work"""
            try:
                # 刪除註冊的回調函數
                Glyphs.removeCallback(self.updateInterface)
                Glyphs.removeCallback(self.selectionChanged_)
                
                # 移除 NSUserDefaults 變更通知觀察者
                NSNotificationCenter.defaultCenter().removeObserver_(self)
            except:
                pass

        @objc.python_method
        def __file__(self):
            """回傳目前檔案的路徑 / Return the path of the current file"""
            return __file__
                
except Exception as e:
    import traceback
    print(f"九宮格預覽外掛載入時發生錯誤: {e}")
    print(traceback.format_exc())
