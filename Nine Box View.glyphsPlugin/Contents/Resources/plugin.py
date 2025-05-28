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
    from AppKit import NSMenuItem, NSUserDefaults, NSTextField
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
                # 確保偏好設定已經載入
                self.loadPreferences()
                
                # 如果視窗不存在，則建立 / If window doesn't exist, create it
                if self.windowController is None:
                    # 在建立視窗前，確保字符排列已經正確初始化
                    # Ensure character arrangement is correctly initialized before creating the window
                    if self.selectedChars and not self.currentArrangement:
                        print("視窗初始化前產生新排列...")
                        self.generateNewArrangement()
                    
                    self.windowController = self.NineBoxWindow.alloc().initWithPlugin_(self)
                    
                # 顯示視窗 / Show window
                self.windowController.makeKeyAndOrderFront()
                
                # 不再需要手動呼叫 updateInterface，因為 makeKeyAndOrderFront 中已經添加了完整初始化步驟
                # 這有助於避免重複更新
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
                    # 檢查是否應該更新預覽畫面
                    # 這個檢查是為了補充 windowController.redraw() 中的檢查
                    # 因為有時候更新可能不是通過 redraw() 觸發的
                    
                    should_update = True  # 預設允許更新，除非明確來自鎖定輸入框
                    
                    # 檢查是否是從長文本輸入框調用 - 使用 sender 參數區分來源
                    # 長文本輸入框調用時總是允許更新
                    is_from_search_field = (sender is not None and hasattr(sender, 'isKindOfClass_') and 
                                           sender.isKindOfClass_(NSTextField) and 
                                           hasattr(self.windowController, 'sidebarView') and
                                           hasattr(self.windowController.sidebarView, 'searchField') and
                                           sender == self.windowController.sidebarView.searchField)
                    
                    # 檢查是否是從鎖定輸入框調用
                    is_from_lock_field = (sender is not None and hasattr(sender, 'isKindOfClass_') and 
                                         sender.isKindOfClass_(NSTextField) and
                                         hasattr(sender, 'position'))  # 鎖定輸入框有 position 屬性
                                         
                    if is_from_search_field:
                        # 來自長文本輸入框的更新始終允許
                        should_update = True
                        print("來自長文本輸入框的更新 - 始終允許")
                    elif is_from_lock_field:
                        # 鎖定輸入框需要根據鎖頭狀態決定
                        is_in_clear_mode = True  # 預設為解鎖狀態 (安全)
                        
                        if (hasattr(self.windowController, 'sidebarView') and 
                            self.windowController.sidebarView and 
                            hasattr(self.windowController.sidebarView, 'isInClearMode')):
                            
                            # 判斷鎖頭狀態 - False = 上鎖狀態（輸入框和預覽關聯）
                            # True = 解鎖狀態（輸入框和預覽不關聯）
                            is_in_clear_mode = self.windowController.sidebarView.isInClearMode
                            
                            # 只有在鎖頭上鎖狀態（False）時才允許更新預覽
                            if not is_in_clear_mode:
                                should_update = True
                                print("鎖定輸入框更新：鎖頭處於上鎖狀態 - 允許更新預覽")
                            else:
                                should_update = False
                                print("鎖定輸入框更新：鎖頭處於解鎖狀態 - 不更新預覽")
                    else:
                        # 來自其他位置的更新（如編輯畫面）始終允許
                        should_update = True
                        print("來自其他來源的更新 - 始終允許")
                    
                    # 重繪介面 / Redraw interface - 只在允許更新時呼叫
                    if should_update and hasattr(self.windowController, 'redraw'):
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
            
            # 長文本輸入框始終與預覽畫面關聯，無條件更新界面
            # 直接呼叫 updateInterfaceForSearchField 而非 updateInterface，確保長文本輸入框的更新不受鎖頭狀態影響
            self.updateInterfaceForSearchField(None)

        @objc.python_method
        def updateInterfaceForSearchField(self, sender):
            """專為長文本輸入框設計的更新界面函數 - 不受鎖頭狀態影響"""
            try:
                if hasattr(self, 'windowController') and self.windowController is not None:
                    # 無條件重繪預覽 - 這是長文本輸入框的特權
                    if hasattr(self.windowController, 'redrawIgnoreLockState'):
                        self.windowController.redrawIgnoreLockState()
                    else:
                        # 如果沒有專用方法，則使用標準方法，但可能會受到鎖頭狀態影響
                        self.windowController.redraw()
            except Exception as e:
                self.log_to_macro_window(f"更新長文本輸入框介面時發生錯誤: {e}")
                print(traceback.format_exc())

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
                    # 空輸入時，無論鎖頭狀態如何，都清除該位置的鎖定
                    if position in self.lockedChars:
                        del self.lockedChars[position]
                        print(f"位置 {position} 的鎖定已清除（空輸入）")
                        self.savePreferences()
                    return
                
                # 先檢查鎖頭狀態
                is_in_clear_mode = True  # 預設為解鎖狀態 (安全)
                
                if (hasattr(self, 'windowController') and self.windowController and 
                    hasattr(self.windowController, 'sidebarView') and 
                    self.windowController.sidebarView and 
                    hasattr(self.windowController.sidebarView, 'isInClearMode')):
                    
                    # 判斷鎖頭狀態 - False = 上鎖狀態（輸入框和預覽關聯）
                    # True = 解鎖狀態（輸入框和預覽不關聯）
                    is_in_clear_mode = self.windowController.sidebarView.isInClearMode
                    
                    # 解鎖狀態下，不進行任何鎖定相關操作
                    if is_in_clear_mode:
                        print(f"鎖頭處於解鎖狀態 - 忽略鎖定輸入框的輸入")
                        return
                    
                    print(f"鎖頭處於上鎖狀態 - 允許鎖定操作")
                else:
                    # 如果無法確定鎖頭狀態，為安全起見，不進行任何操作
                    print(f"無法確定鎖頭狀態 - 為安全起見，不進行任何鎖定操作")
                    return
                
                # 只有在鎖頭上鎖狀態下才執行下面的鎖定邏輯
                
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
                
                # 只在有辨識結果時處理
                if recognized_char:
                    # 檢查是否真的變更了，避免不必要的更新
                    if position not in self.lockedChars or self.lockedChars[position] != recognized_char:
                        # 更新鎖定字典
                        self.lockedChars[position] = recognized_char
                        
                        # 更新當前排列中的字符
                        if hasattr(self, 'currentArrangement') and self.currentArrangement:
                            if position < len(self.currentArrangement):
                                self.currentArrangement[position] = recognized_char
                                print(f"位置 {position} 已更新字符為 '{recognized_char}'")
                        
                        # 儲存偏好設定
                        self.savePreferences()
                        
                        # 更新預覽畫面
                        print("鎖頭上鎖 - 更新預覽畫面")
                        self.updateInterface(sender)  # 將 sender 傳遞過去，使 updateInterface 可以識別來源
            
            except Exception as e:
                print(f"智能鎖定字符處理時發生錯誤: {e}")
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
            
            # 檢查鎖頭狀態，判斷是否需要特殊處理
            is_in_clear_mode = True  # 預設為解鎖狀態 (安全)
            
            if (hasattr(self, 'windowController') and self.windowController and 
                hasattr(self.windowController, 'sidebarView') and 
                self.windowController.sidebarView and 
                hasattr(self.windowController.sidebarView, 'isInClearMode')):
                
                is_in_clear_mode = self.windowController.sidebarView.isInClearMode
                print(f"亂數排列按鈕：鎖頭處於{'解鎖' if is_in_clear_mode else '上鎖'}狀態")
            
            # 添加強制重排的標記，確保即使在鎖頭鎖定狀態下也能重新排列
            self.force_randomize = True
            
            # 調用 generateNewArrangement 函數以確保每個字符至少出現一次
            self.generateNewArrangement()
            
            # 更新介面 - 使用強制更新方法，忽略鎖頭狀態
            if hasattr(self, 'windowController') and self.windowController:
                if hasattr(self.windowController, 'redrawIgnoreLockState'):
                    print("隨機排列：使用強制更新方法，忽略鎖頭狀態")
                    self.windowController.redrawIgnoreLockState()
                else:
                    # 後備方案：使用標準更新方法
                    print("隨機排列：使用標準更新方法")
                    self.updateInterface(None)
            else:
                # 如果窗口控制器不存在，仍使用標準方法
                self.updateInterface(None)
            
            # 重置強制重排標記
            self.force_randomize = False

        @objc.python_method
        def generateNewArrangement(self):
            """生成新的字符排列 / Generate a new character arrangement"""
            
            if not self.selectedChars:
                # 如果沒有選擇字符，則直接返回，不做任何處理
                print("沒有選擇字符，無法生成排列")
                return
            
            # 檢查鎖頭狀態 - 只有在鎖頭上鎖狀態時才應用鎖定字符
            should_apply_locks = False
            is_in_clear_mode = True  # 預設為解鎖狀態 (安全)
            
            # 檢查鎖頭狀態
            if (hasattr(self, 'windowController') and self.windowController and 
                hasattr(self.windowController, 'sidebarView') and 
                self.windowController.sidebarView and 
                hasattr(self.windowController.sidebarView, 'isInClearMode')):
                
                # False = 上鎖狀態（輸入框和預覽關聯）, True = 解鎖狀態（輸入框和預覽不關聯）
                is_in_clear_mode = self.windowController.sidebarView.isInClearMode
                should_apply_locks = not is_in_clear_mode
                print(f"亂數排列：鎖頭處於{'解鎖' if is_in_clear_mode else '上鎖'}狀態，{'不' if is_in_clear_mode else ''}應用鎖定字符")
            
            # 檢查是否為強制重排（由 randomizeCallback 設置）
            force_randomize = hasattr(self, 'force_randomize') and self.force_randomize
            if force_randomize:
                print("檢測到強制重排標記 - 即使鎖頭鎖定也將重新排列非鎖定位置")
            
            # 根據鎖頭狀態使用不同的邏輯
            if is_in_clear_mode:
                # 解鎖狀態：完全不使用鎖定字符
                print("解鎖狀態：完全不使用鎖定字符")
                
                # 產生新的隨機排列，確保每個字符至少出現一次
                import random
                arrangement_size = 9
                new_arrangement = []
                
                # 1. 首先確保每個選擇的字符至少出現一次
                # 創建字符列表的副本
                chars_to_include = list(self.selectedChars)
                
                # 如果字符數量少於9，則重複字符直到達到9個
                while len(chars_to_include) < arrangement_size:
                    chars_to_include.extend(self.selectedChars[:arrangement_size - len(chars_to_include)])
                
                # 如果字符數量超過9，則隨機選擇9個（但確保每個字符至少選一次）
                if len(chars_to_include) > arrangement_size:
                    # 先選擇每個字符各一次
                    unique_chars = list(set(self.selectedChars))
                    # 確保不超過九宮格大小
                    if len(unique_chars) > arrangement_size:
                        unique_chars = random.sample(unique_chars, arrangement_size)
                    
                    # 把這些字符加入排列
                    new_arrangement = unique_chars.copy()
                    
                    # 如果還有空位，則從原始列表中隨機選擇填充
                    while len(new_arrangement) < arrangement_size:
                        new_arrangement.append(random.choice(self.selectedChars))
                else:
                    # 字符數量剛好，打亂順序後使用
                    new_arrangement = chars_to_include.copy()
                
                # 最後打亂整個排列的順序
                random.shuffle(new_arrangement)
                
                # 直接使用新排列，不套用任何鎖定字元
                self.currentArrangement = new_arrangement
                print(f"解鎖狀態下生成的排列，確保每個字符至少出現一次: {new_arrangement}")
            else:
                # 上鎖狀態：先生成排列，然後應用鎖定字符，同時確保每個字符至少出現一次
                print("上鎖狀態：應用鎖定字符，但確保每個字符至少出現一次")
                
                import random
                arrangement_size = 9
                
                # 無論是否有強制重排標記，都先生成一個完全新的基礎排列
                # 這確保每次點擊亂數排列按鈕時，至少非鎖定位置的字符會被重新隨機化
                chars_to_include = list(self.selectedChars)
                while len(chars_to_include) < arrangement_size:
                    chars_to_include.extend(self.selectedChars[:arrangement_size - len(chars_to_include)])
                
                if len(chars_to_include) > arrangement_size:
                    unique_chars = list(set(self.selectedChars))
                    if len(unique_chars) > arrangement_size:
                        unique_chars = random.sample(unique_chars, arrangement_size)
                    base_arrangement = unique_chars.copy()
                    while len(base_arrangement) < arrangement_size:
                        base_arrangement.append(random.choice(self.selectedChars))
                else:
                    base_arrangement = chars_to_include.copy()
                
                # 每次都打亂順序，確保不會重複前一次的排列
                random.shuffle(base_arrangement)
                new_arrangement = list(base_arrangement)  # 複製一份基礎排列
                
                # 初始化鎖定位置的列表，用於追蹤有效和無效的鎖定
                valid_locked_positions = []
                invalid_locked_positions = []
                
                # 應用鎖定字符，但先檢查字符有效性
                if hasattr(self, 'lockedChars') and self.lockedChars:
                    print("應用鎖定字符到排列中")
                    
                    # 將鎖定的字符應用到排列中
                    for position, char_or_name in self.lockedChars.items():
                        if position < arrangement_size:
                            # 確保鎖定的字符/Nice Name 存在於字型中
                            glyph = Glyphs.font.glyphs[char_or_name]
                            if glyph:
                                new_arrangement[position] = char_or_name
                                valid_locked_positions.append(position)
                                print(f"位置 {position} 已套用鎖定字符 '{char_or_name}'")
                            else:
                                # 如果字符不存在，移除鎖定
                                invalid_locked_positions.append(position)
                                print(f"位置 {position} 的鎖定字符 '{char_or_name}' 無效，將被移除")
                
                # 處理無效鎖定
                for position in invalid_locked_positions:
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
                
                # 確保每個選定的字符至少出現一次（如果可能）
                if valid_locked_positions:
                    # 檢查哪些字符已經在鎖定位置中使用
                    locked_chars_used = [new_arrangement[pos] for pos in valid_locked_positions]
                    
                    # 找出還未在鎖定字符中使用的字符
                    remaining_chars = [char for char in set(self.selectedChars) if char not in locked_chars_used]
                    
                    # 找出可用的位置（非鎖定位置）
                    available_positions = [i for i in range(arrangement_size) if i not in valid_locked_positions]
                    
                    # 確保每個剩餘字符至少出現一次（如果空間允許）
                    if remaining_chars and available_positions:
                        # 如果剩餘位置不足以容納所有未使用字符，則隨機選擇部分字符
                        if len(remaining_chars) > len(available_positions):
                            # 每次強制生成新的隨機選擇，確保連續點擊時排列變化
                            chars_to_use = random.sample(remaining_chars, len(available_positions))
                            for i, pos in enumerate(available_positions):
                                new_arrangement[pos] = chars_to_use[i]
                        else:
                            # 首先確保每個剩餘字符至少出現一次
                            for i, char in enumerate(remaining_chars):
                                if i < len(available_positions):
                                    new_arrangement[available_positions[i]] = char
                            
                            # 如果還有空位，則從所有字符中隨機選擇填充
                            remaining_positions = available_positions[len(remaining_chars):]
                            
                            # 每次強制生成新的隨機選擇，確保連續點擊時排列變化
                            for pos in remaining_positions:
                                new_arrangement[pos] = random.choice(self.selectedChars)
                    
                    # 如果強制重排，確保非鎖定位置的字符順序被打亂
                    if force_randomize and available_positions:
                        # 提取非鎖定位置的當前字符
                        non_locked_chars = [new_arrangement[pos] for pos in available_positions]
                        # 打亂這些字符
                        random.shuffle(non_locked_chars)
                        # 將打亂後的字符放回非鎖定位置
                        for i, pos in enumerate(available_positions):
                            new_arrangement[pos] = non_locked_chars[i]
                
                self.currentArrangement = new_arrangement
                print(f"上鎖狀態下生成的排列，確保每個字符至少出現一次: {new_arrangement}")
            
            # 儲存偏好設定，無論鎖頭狀態如何
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
            """鎖定所有字符輸入框的回調函數 / Callback function for locking all character fields"""
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
                
                # 取得側邊欄輸入框中的內容並套用到九宮格預覽
                if hasattr(self, 'windowController') and self.windowController:
                    if (hasattr(self.windowController, 'sidebarView') and 
                        self.windowController.sidebarView and 
                        not self.windowController.sidebarView.isHidden() and
                        hasattr(self.windowController.sidebarView, 'lockFields')):
                        
                        # 先清空現有鎖定
                        self.lockedChars = {}
                        
                        # 逐一處理每個輸入框
                        for position, field in self.windowController.sidebarView.lockFields.items():
                            input_text = field.stringValue().strip()
                            if input_text:
                                # 嘗試驗證字符是否存在於字型中
                                glyph = Glyphs.font.glyphs[input_text]
                                if glyph:
                                    self.lockedChars[position] = input_text
                                else:
                                    # 嘗試解析字符
                                    parsed_chars = self.parse_input_text(input_text)
                                    if parsed_chars:
                                        self.lockedChars[position] = parsed_chars[0]
                
                # 更新排列中對應的字符
                if hasattr(self, 'currentArrangement') and self.currentArrangement:
                    for position, char_or_name in self.lockedChars.items():
                        if position < len(self.currentArrangement):
                            self.currentArrangement[position] = char_or_name
                
                # 儲存偏好設定
                self.savePreferences()
                
                # 更新介面
                self.updateInterface(None)
                print("已鎖定所有輸入框中的字符")
            except Exception as e:
                print(f"鎖定字符時發生錯誤: {e}")
                print(traceback.format_exc())

        @objc.python_method
        def restoreAllLockFieldsCallback(self, sender):
            """解除鎖定所有字符輸入框的回調函數 / Callback function for unlocking all character fields"""
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
                
                # 解除所有鎖定，直接清空鎖定字典
                self.lockedChars = {}
                
                # 如果有選擇的字符，重新生成排列（解除鎖定後允許字符位置變動）
                if hasattr(self, 'selectedChars') and self.selectedChars:
                    # 重新生成排列
                    self.generateNewArrangement()
                
                # 儲存偏好設定
                self.savePreferences()
                
                # 更新介面
                self.updateInterface(None)
                print("已解除所有字符的鎖定")
            except Exception as e:
                print(f"解除鎖定字符時發生錯誤: {e}")
                print(traceback.format_exc())

except Exception as e:
    import traceback
    print(f"九宮格預覽外掛載入時發生錯誤: {e}")
    print(traceback.format_exc())
