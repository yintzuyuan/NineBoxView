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
                SIDEBAR_VISIBLE_KEY, SIDEBAR_WIDTH, LOCKED_CHARS_KEY,
                PREVIOUS_LOCKED_CHARS_KEY
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
            self.LOCKED_CHARS_KEY = LOCKED_CHARS_KEY
            self.PREVIOUS_LOCKED_CHARS_KEY = PREVIOUS_LOCKED_CHARS_KEY
            self.DEFAULT_ZOOM = DEFAULT_ZOOM
            
            self.loadPreferences()
            self.selectedChars = []  # 儲存選取的字符 / Store selected characters
            self.currentArrangement = []  # 儲存目前的排列 / Store current arrangement
            self.windowController = None  # 視窗控制器 / Window controller
            self.previousLockedChars = {}  # 儲存前一次鎖定字符狀態 / Store previous locked characters state
            
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
                
                # 更新側邊欄輸入欄位
                if hasattr(self, 'windowController') and self.windowController is not None:
                    if (hasattr(self.windowController, 'sidebarView') and 
                        self.windowController.sidebarView is not None and
                        not self.windowController.sidebarView.isHidden()):
                        self.windowController.sidebarView.updateSearchField()
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

            # 檢查輸入是否變更，避免重複處理相同內容
            if hasattr(self, 'lastInput') and self.lastInput == input_text:
                return

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
        def smartLockCharacterCallback(self, sender):
            """智能鎖定字符回調函數 - 即時辨識但絕不干擾輸入"""
            try:
                # 檢查是否有開啟字型檔案
                if not Glyphs.font:
                    return
                
                # 確保 lockedChars 字典存在
                if not hasattr(self, 'lockedChars'):
                    self.lockedChars = {}
                
                # 取得位置和輸入的文字
                position = sender.position
                input_text = sender.stringValue()  # 不要 strip，保留原始輸入
                
                if not input_text:
                    # 空輸入直接返回，不做任何處理
                    # 空輸入的處理由 textDidChange_ 中的 handleLockFieldCleared 完成
                    return
                
                # 智能辨識邏輯（優先級順序）：
                recognized_char = None
                
                # 1. 嘗試完整輸入作為 Nice Name 或字符
                try:
                    glyph = Glyphs.font.glyphs[input_text]
                    if glyph:
                        recognized_char = input_text
                        print(f"✓ 辨識完整輸入: '{input_text}'")
                except:
                    pass
                
                # 2. 如果完整輸入無效，嘗試第一個字符
                if not recognized_char and len(input_text) > 0:
                    try:
                        first_char = input_text[0]
                        first_glyph = Glyphs.font.glyphs[first_char]
                        if first_glyph:
                            recognized_char = first_char
                            print(f"✓ 辨識第一個字符: '{first_char}' (輸入: '{input_text}')")
                    except:
                        pass
                
                # 3. 最後嘗試通過解析
                if not recognized_char:
                    try:
                        parsed_chars = self.parse_input_text(input_text)
                        if parsed_chars:
                            recognized_char = parsed_chars[0]
                            print(f"✓ 通過解析辨識: '{recognized_char}' (輸入: '{input_text}')")
                    except:
                        pass
                
                # 只在有辨識結果時更新鎖定
                if recognized_char:
                    # 檢查是否真的變更了，避免不必要的更新
                    if position not in self.lockedChars or self.lockedChars[position] != recognized_char:
                        self.lockedChars[position] = recognized_char
                        
                        # 更新當前排列中的鎖定字符
                        if hasattr(self, 'currentArrangement') and self.currentArrangement:
                            if position < len(self.currentArrangement):
                                self.currentArrangement[position] = recognized_char
                        
                        # 只在實際變更時儲存和更新
                        self.savePreferences()
                        self.updateInterface(None)
                
                # 無法辨識時什麼都不做，保持之前的狀態
                
            except Exception as e:
                print(f"智能鎖定字符處理時發生錯誤: {e}")
                print(traceback.format_exc())

        @objc.python_method
        def handleLockFieldCleared(self, sender):
            """處理鎖定框被清空的事件"""
            try:
                # 檢查是否有開啟字型檔案
                if not Glyphs.font:
                    return
                
                # 確保 lockedChars 字典存在
                if not hasattr(self, 'lockedChars'):
                    self.lockedChars = {}
                
                position = sender.position
                
                # 移除此位置的鎖定
                if position in self.lockedChars:
                    del self.lockedChars[position]
                    print(f"已清空位置 {position} 的鎖定")
                
                # 更新當前排列中的字符
                if hasattr(self, 'currentArrangement') and self.currentArrangement and position < len(self.currentArrangement):
                    # 如果有選擇的字符，使用隨機字符替換
                    if hasattr(self, 'selectedChars') and self.selectedChars:
                        import random
                        random_char = random.choice(self.selectedChars)
                        self.currentArrangement[position] = random_char
                        print(f"位置 {position} 已使用隨機字符 '{random_char}' 替換")
                
                # 更新排列和介面
                self.savePreferences()
                self.updateInterface(None)
                
            except Exception as e:
                print(f"處理鎖定框清空時發生錯誤: {e}")
                print(traceback.format_exc())

        @objc.python_method
        def lockCharacterCallback(self, sender):
            """處理鎖定字符輸入框的回調函數 / Callback function for lock character fields"""
            try:
                # 檢查是否有開啟字型檔案
                if not Glyphs.font:
                    print("警告：沒有開啟字型檔案")
                    return
                
                # 確保 lockedChars 字典存在
                if not hasattr(self, 'lockedChars'):
                    self.lockedChars = {}
                
                # 取得位置和輸入的文字
                position = sender.position
                input_text = sender.stringValue().strip()  # 移除前後空白
                
                if input_text:
                    # 嘗試直接查找字符 - 可能是單個字符或 Nice Name
                    glyph = Glyphs.font.glyphs[input_text]
                    
                    if glyph:
                        # 找到有效的字符或 Nice Name
                        self.lockedChars[position] = input_text
                        print(f"已鎖定位置 {position}: {input_text}")
                    else:
                        # 如果找不到，嘗試使用 parse_input_text 解析
                        parsed_chars = self.parse_input_text(input_text)
                        if parsed_chars:
                            # 有解析結果，使用第一個有效字符
                            first_char = parsed_chars[0]
                            self.lockedChars[position] = first_char
                            print(f"已鎖定位置 {position}: {first_char} (從輸入 '{input_text}' 解析)")
                            
                            # 不再修改輸入框內容，完全保留用戶輸入
                            # 讓用戶知道實際鎖定的字符是什麼
                        else:
                            # 無法解析為有效字符，取消此位置的鎖定
                            if position in self.lockedChars:
                                del self.lockedChars[position]
                                print(f"無法解析 '{input_text}'，已取消位置 {position} 的鎖定")
                else:
                    # 如果輸入為空，解除鎖定
                    if position in self.lockedChars:
                        del self.lockedChars[position]
                
                # 更新當前排列中的鎖定字符，但不重新生成整個排列
                if hasattr(self, 'currentArrangement') and self.currentArrangement:
                    if position < len(self.currentArrangement) and position in self.lockedChars:
                        # 只更新指定位置的字符
                        self.currentArrangement[position] = self.lockedChars[position]
                
                # 儲存偏好設定
                self.savePreferences()
                
                # 更新介面
                self.updateInterface(None)
            except Exception as e:
                print(f"處理鎖定字符時發生錯誤: {e}")
                print(traceback.format_exc())

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
                            # 更新側邊欄中的字符輸入欄位 - 不再使用空格分隔字符
                            self.lastInput = "".join(selected_chars)
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
                new_arrangement = self.generate_arrangement(self.selectedChars, 8)
                
                # 應用鎖定字符設定 / Apply locked characters
                if hasattr(self, 'lockedChars') and self.lockedChars:
                    # 複製一份新排列，以便修改
                    self.currentArrangement = list(new_arrangement)
                    
                    # 將鎖定的字符應用到排列中
                    for position, char_or_name in self.lockedChars.items():
                        if position < len(self.currentArrangement):
                            # 確保鎖定的字符/Nice Name 存在於字型中
                            glyph = Glyphs.font.glyphs[char_or_name]
                            if glyph:
                                self.currentArrangement[position] = char_or_name
                            else:
                                # 如果字符不存在，移除鎖定
                                if position in self.lockedChars:
                                    del self.lockedChars[position]
                                    # 如果是視窗已存在，則同步更新輸入框
                                    if hasattr(self, 'windowController') and self.windowController:
                                        if (hasattr(self.windowController, 'sidebarView') and 
                                            self.windowController.sidebarView and 
                                            not self.windowController.sidebarView.isHidden() and
                                            hasattr(self.windowController.sidebarView, 'lockFields') and
                                            position in self.windowController.sidebarView.lockFields):
                                            self.windowController.sidebarView.lockFields[position].setStringValue_("")
                else:
                    self.currentArrangement = new_arrangement
                
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
            
            # 鎖定字符資訊 / Locked characters information
            locked_chars_str = Glyphs.defaults.get(self.LOCKED_CHARS_KEY)
            if locked_chars_str:
                # 將字串鍵轉換回整數鍵
                self.lockedChars = {}
                for key_str, value in locked_chars_str.items():
                    self.lockedChars[int(key_str)] = value
            else:
                self.lockedChars = {}
                
            # 前一次鎖定字符資訊 / Previous locked characters information
            previous_locked_chars_str = Glyphs.defaults.get(self.PREVIOUS_LOCKED_CHARS_KEY)
            if previous_locked_chars_str:
                # 將字串鍵轉換回整數鍵
                self.previousLockedChars = {}
                for key_str, value in previous_locked_chars_str.items():
                    self.previousLockedChars[int(key_str)] = value
            else:
                self.previousLockedChars = {}

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
            
            # 儲存鎖定字符資訊 / Save locked characters information
            if hasattr(self, 'lockedChars'):
                # 將整數鍵轉換為字串鍵
                locked_chars_str = {}
                for key, value in self.lockedChars.items():
                    locked_chars_str[str(key)] = value
                Glyphs.defaults[self.LOCKED_CHARS_KEY] = locked_chars_str
                
            # 儲存前一次鎖定字符資訊 / Save previous locked characters information
            if hasattr(self, 'previousLockedChars'):
                # 將整數鍵轉換為字串鍵
                previous_locked_chars_str = {}
                for key, value in self.previousLockedChars.items():
                    previous_locked_chars_str[str(key)] = value
                Glyphs.defaults[self.PREVIOUS_LOCKED_CHARS_KEY] = previous_locked_chars_str

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
            except:
                pass

        @objc.python_method
        def __file__(self):
            """回傳目前檔案的路徑 / Return the path of the current file"""
            return __file__
                
        @objc.python_method
        def clearAllLockFieldsCallback(self, sender):
            """清空所有鎖定字符輸入框的回調函數 / Callback function for clearing all lock fields"""
            try:
                # 檢查是否有開啟字型檔案
                if not Glyphs.font:
                    print("警告：沒有開啟字型檔案")
                    return
                
                # 確保 lockedChars 和 previousLockedChars 字典存在
                if not hasattr(self, 'lockedChars'):
                    self.lockedChars = {}
                if not hasattr(self, 'previousLockedChars'):
                    self.previousLockedChars = {}
                
                # 備份目前的鎖定字符狀態以便還原
                self.previousLockedChars = self.lockedChars.copy()
                
                # 清空所有鎖定字符
                self.lockedChars = {}
                
                # 更新排列中對應的字符
                if hasattr(self, 'currentArrangement') and self.currentArrangement and hasattr(self, 'selectedChars') and self.selectedChars:
                    # 重新生成排列
                    self.generateNewArrangement()
                
                # 更新側邊欄中的鎖定輸入框
                if hasattr(self, 'windowController') and self.windowController:
                    if (hasattr(self.windowController, 'sidebarView') and 
                        self.windowController.sidebarView and 
                        not self.windowController.sidebarView.isHidden() and
                        hasattr(self.windowController.sidebarView, 'lockFields')):
                        for position, field in self.windowController.sidebarView.lockFields.items():
                            field.setStringValue_("")
                
                # 儲存偏好設定
                self.savePreferences()
                
                # 更新介面
                self.updateInterface(None)
                print("已清空所有鎖定字符")
            except Exception as e:
                print(f"清空所有鎖定字符時發生錯誤: {e}")
                print(traceback.format_exc())

        @objc.python_method
        def restoreAllLockFieldsCallback(self, sender):
            """還原所有鎖定字符輸入框的回調函數 / Callback function for restoring all lock fields"""
            try:
                # 檢查是否有開啟字型檔案
                if not Glyphs.font:
                    print("警告：沒有開啟字型檔案")
                    return
                
                # 確保 lockedChars 和 previousLockedChars 字典存在
                if not hasattr(self, 'lockedChars'):
                    self.lockedChars = {}
                if not hasattr(self, 'previousLockedChars'):
                    self.previousLockedChars = {}
                
                # 如果沒有前一個狀態可還原，則提示並返回
                if not self.previousLockedChars:
                    print("沒有可還原的鎖定字符狀態")
                    return
                
                # 交換當前和前一個狀態
                current_state = self.lockedChars.copy()
                self.lockedChars = self.previousLockedChars.copy()
                self.previousLockedChars = current_state
                
                # 更新排列中的鎖定字符
                if hasattr(self, 'currentArrangement') and self.currentArrangement:
                    for position, char_or_name in self.lockedChars.items():
                        if position < len(self.currentArrangement):
                            # 確保鎖定的字符/Nice Name 存在於字型中
                            glyph = Glyphs.font.glyphs[char_or_name]
                            if glyph:
                                self.currentArrangement[position] = char_or_name
                
                # 更新側邊欄中的鎖定輸入框
                if hasattr(self, 'windowController') and self.windowController:
                    if (hasattr(self.windowController, 'sidebarView') and 
                        self.windowController.sidebarView and 
                        not self.windowController.sidebarView.isHidden() and
                        hasattr(self.windowController.sidebarView, 'lockFields')):
                        for position, field in self.windowController.sidebarView.lockFields.items():
                            value = self.lockedChars.get(position, "")
                            field.setStringValue_(value)
                
                # 儲存偏好設定
                self.savePreferences()
                
                # 更新介面
                self.updateInterface(None)
                print("已還原所有鎖定字符")
            except Exception as e:
                print(f"還原所有鎖定字符時發生錯誤: {e}")
                print(traceback.format_exc())

except Exception as e:
    import traceback
    print(f"九宮格預覽外掛載入時發生錯誤: {e}")
    print(traceback.format_exc())
