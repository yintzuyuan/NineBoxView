# encoding: utf-8
"""
九宮格預覽外掛 - 主程式（優化版）
Nine Box Preview Plugin - Main Class (Optimized)
"""

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
        九宮格預覽外掛主類別（優化版）
        Nine Box Preview Plugin Main Class (Optimized)
        """
        
        @objc.python_method
        def settings(self):
            """設定外掛基本資訊"""
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
            
            # 導入模組（延遲導入以避免循環依賴）
            self._import_modules()
            
            # 初始化屬性
            self._initialize_properties()
            
            print("九宮格預覽外掛已成功載入。")
        
        @objc.python_method
        def _import_modules(self):
            """導入所需模組"""
            from constants import (
                LAST_INPUT_KEY, SELECTED_CHARS_KEY, 
                CURRENT_ARRANGEMENT_KEY, TEST_MODE_KEY, SEARCH_HISTORY_KEY,
                ZOOM_FACTOR_KEY, SHOW_NUMBERS_KEY, WINDOW_SIZE_KEY, WINDOW_POSITION_KEY,
                DEFAULT_WINDOW_SIZE, MIN_WINDOW_SIZE, DEFAULT_ZOOM,
                SIDEBAR_VISIBLE_KEY, CONTROLS_PANEL_VISIBLE_KEY, CONTROLS_PANEL_WIDTH, 
                LOCKED_CHARS_KEY, PREVIOUS_LOCKED_CHARS_KEY, DEBUG_MODE
            )
            
            from utils import (
                parse_input_text, generate_arrangement, get_base_width, 
                log_to_macro_window, debug_log, clear_cache, get_cached_glyph,
                validate_locked_positions, apply_locked_chars
            )
            from window_controller import NineBoxWindow
            
            # 儲存到 self 中
            self.NineBoxWindow = NineBoxWindow
            self.parse_input_text = parse_input_text
            self.generate_arrangement = generate_arrangement
            self.get_base_width = get_base_width
            self.log_to_macro_window = log_to_macro_window
            self.debug_log = debug_log
            self.clear_cache = clear_cache
            self.get_cached_glyph = get_cached_glyph
            self.validate_locked_positions = validate_locked_positions
            self.apply_locked_chars = apply_locked_chars
            
            # 常數
            self.LAST_INPUT_KEY = LAST_INPUT_KEY
            self.SELECTED_CHARS_KEY = SELECTED_CHARS_KEY
            self.CURRENT_ARRANGEMENT_KEY = CURRENT_ARRANGEMENT_KEY
            self.TEST_MODE_KEY = TEST_MODE_KEY
            self.SEARCH_HISTORY_KEY = SEARCH_HISTORY_KEY
            self.ZOOM_FACTOR_KEY = ZOOM_FACTOR_KEY
            self.SHOW_NUMBERS_KEY = SHOW_NUMBERS_KEY
            self.WINDOW_SIZE_KEY = WINDOW_SIZE_KEY
            self.WINDOW_POSITION_KEY = WINDOW_POSITION_KEY
            self.SIDEBAR_VISIBLE_KEY = SIDEBAR_VISIBLE_KEY
            self.CONTROLS_PANEL_VISIBLE_KEY = CONTROLS_PANEL_VISIBLE_KEY
            self.LOCKED_CHARS_KEY = LOCKED_CHARS_KEY
            self.PREVIOUS_LOCKED_CHARS_KEY = PREVIOUS_LOCKED_CHARS_KEY
            self.DEFAULT_ZOOM = DEFAULT_ZOOM
            self.DEBUG_MODE = DEBUG_MODE
        
        @objc.python_method
        def _initialize_properties(self):
            """初始化屬性"""
            self.loadPreferences()
            self.selectedChars = []
            self.currentArrangement = []
            self.windowController = None
            self.previousLockedChars = {}
            self.controlsPanelVisible = True
            self.windowPosition = None
            self._update_scheduled = False  # 防止重複更新

        @objc.python_method
        def start(self):
            """啟動外掛"""
            try:
                # 新增選單項
                newMenuItem = NSMenuItem(self.name, self.toggleWindow_)
                Glyphs.menu[WINDOW_MENU].append(newMenuItem)

                # 新增回調函數
                Glyphs.addCallback(self.updateInterface, UPDATEINTERFACE)
                Glyphs.addCallback(self.updateInterface, DOCUMENTACTIVATED)
                Glyphs.addCallback(self.selectionChanged_, DOCUMENTOPENED)
                Glyphs.addCallback(self.selectionChanged_, SELECTIONCHANGED)

                # 載入偏好設定
                self.loadPreferences()
                
            except Exception as e:
                print(f"啟動外掛時發生錯誤: {str(e)}")
                if self.DEBUG_MODE:
                    print(traceback.format_exc())

        # === 視窗操作 ===

        @objc.python_method
        def toggleWindow_(self, sender):
            """切換視窗顯示狀態"""
            try:
                self.loadPreferences()
                
                if self.windowController is None:
                    if self.selectedChars and not self.currentArrangement:
                        self.debug_log("初始化視窗前產生排列")
                        self.generateNewArrangement()
                    
                    # 嘗試初始化視窗控制器
                    self.debug_log("嘗試初始化視窗控制器")
                    self.windowController = self.NineBoxWindow.alloc().initWithPlugin_(self)
                    
                    # 檢查初始化是否成功
                    if self.windowController is None:
                        self.debug_log("初始化視窗控制器失敗")
                        Glyphs.showNotification(
                            self.name,
                            "初始化視窗失敗，請檢查控制台日誌"
                        )
                        return
                
                # 確保視窗控制器有效後再顯示視窗
                if self.windowController is not None:
                    self.windowController.makeKeyAndOrderFront()
                
            except Exception as e:
                print(f"切換視窗時發生錯誤: {str(e)}")
                if self.DEBUG_MODE:
                    print(traceback.format_exc())

        @objc.python_method
        def showWindow(self):
            """顯示視窗"""
            if self.windowController is not None:
                self.windowController.showWindow_(None)

        @objc.python_method
        def hideWindow(self):
            """隱藏視窗"""
            if self.windowController is not None:
                self.windowController.window().orderOut_(None)

        @objc.python_method
        def logToMacroWindow(self, message):
            """記錄訊息到巨集視窗"""
            self.log_to_macro_window(message)

        # === 界面更新（優化版）===

        @objc.python_method
        def _should_update_preview(self, sender):
            """判斷是否應該更新預覽"""
            # 檢查來源
            is_from_search_field = (sender is not None and 
                                   hasattr(sender, 'isKindOfClass_') and 
                                   sender.isKindOfClass_(NSTextField) and 
                                   hasattr(self.windowController, 'controlsPanelView') and
                                   hasattr(self.windowController.controlsPanelView, 'searchField') and
                                   sender == self.windowController.controlsPanelView.searchField)
            
            is_from_lock_field = (sender is not None and 
                                 hasattr(sender, 'isKindOfClass_') and 
                                 sender.isKindOfClass_(NSTextField) and
                                 hasattr(sender, 'position'))
            
            if is_from_search_field:
                # 搜尋欄位始終更新
                return True
            elif is_from_lock_field:
                # 鎖定欄位需要檢查鎖頭狀態
                if (hasattr(self.windowController, 'controlsPanelView') and 
                    self.windowController.controlsPanelView):
                    is_in_clear_mode = getattr(self.windowController.controlsPanelView, 
                                              'isInClearMode', True)
                    return not is_in_clear_mode  # 上鎖狀態才更新
                return False
            else:
                # 其他來源始終更新
                return True

        @objc.python_method
        def updateInterface(self, sender):
            """更新界面（階段2.1：完整版）"""
            try:
                # 避免重複更新
                if self._update_scheduled:
                    return
                
                if hasattr(self, 'windowController') and self.windowController is not None:
                    # === 階段2.1：完整更新邏輯 ===
                    self.debug_log(f"[階段2.1] 更新預覽：來源={type(sender).__name__}")
                    
                    # 批次更新
                    self._update_scheduled = True
                    
                    if hasattr(self.windowController, 'redraw'):
                        self.windowController.redraw()
                    
                    # === 階段2.1：啟用控制面板更新 ===
                    if hasattr(self.windowController, 'request_controls_panel_ui_update'):
                        self.windowController.request_controls_panel_ui_update()
                    
                    self._update_scheduled = False
                        
            except Exception as e:
                self._update_scheduled = False
                self.debug_log(f"[階段2.1] 更新介面時發生錯誤: {e}")
                if self.DEBUG_MODE:
                    print(traceback.format_exc())
        
        @objc.python_method
        def selectionChanged_(self, sender):
            """選擇變更處理"""
            try:
                # 清除快取
                self.clear_cache()
                
                # 更新介面
                self.updateInterface(None)
                
                # 更新控制面板
                if (hasattr(self, 'windowController') and 
                    self.windowController is not None and
                    hasattr(self.windowController, 'controlsPanelView') and 
                    self.windowController.controlsPanelView is not None and
                    hasattr(self.windowController, 'controlsPanelVisible') and
                    self.windowController.controlsPanelVisible):
                    
                    self.windowController.controlsPanelView.update_ui(self)
                    
            except Exception as e:
                self.debug_log(f"選擇變更處理錯誤: {e}")

        # === 事件處理（優化版）===

        @objc.python_method
        def searchFieldCallback(self, sender):
            """處理搜尋欄位輸入（優化版）"""
            if not Glyphs.font:
                self.debug_log("警告：沒有開啟字型檔案")
                return

            input_text = sender.stringValue()
            
            # 檢查是否有變更
            if hasattr(self, 'lastInput') and self.lastInput == input_text:
                return

            self.lastInput = input_text

            if input_text:
                new_chars = self.parse_input_text(input_text)
                
                if new_chars != self.selectedChars:
                    self.selectedChars = new_chars
                    self.generateNewArrangement()
            else:
                self.selectedChars = []
                self.currentArrangement = []

            self.updateInterfaceForSearchField(None)
            
            if hasattr(self, 'windowController') and self.windowController:
                if hasattr(self.windowController, 'request_controls_panel_ui_update'):
                    self.windowController.request_controls_panel_ui_update()

        @objc.python_method
        def updateInterfaceForSearchField(self, sender):
            """專為搜尋欄位的更新"""
            try:
                if hasattr(self, 'windowController') and self.windowController is not None:
                    if hasattr(self.windowController, 'redrawIgnoreLockState'):
                        self.windowController.redrawIgnoreLockState()
                    else:
                        self.windowController.redraw()
            except Exception as e:
                self.debug_log(f"更新搜尋欄位介面錯誤: {e}")

        @objc.python_method
        def smartLockCharacterCallback(self, sender):
            """智能鎖定字符回調（優化版）"""
            try:
                if not Glyphs.font:
                    return
                
                if not hasattr(self, 'lockedChars'):
                    self.lockedChars = {}
                
                position = sender.position
                input_text = sender.stringValue()
                
                if not input_text:
                    # 清除鎖定
                    if position in self.lockedChars:
                        del self.lockedChars[position]
                        self.debug_log(f"清除位置 {position} 的鎖定")
                        self.savePreferences()
                    return
                
                # 檢查鎖頭狀態
                is_in_clear_mode = self._get_lock_state()
                if is_in_clear_mode:
                    self.debug_log("解鎖狀態 - 忽略輸入")
                    return
                
                # 智能辨識
                recognized_char = self._recognize_character(input_text)
                
                if recognized_char:
                    if position not in self.lockedChars or self.lockedChars[position] != recognized_char:
                        self.lockedChars[position] = recognized_char
                        
                        # 更新排列
                        if hasattr(self, 'currentArrangement') and self.currentArrangement:
                            if position < len(self.currentArrangement):
                                self.currentArrangement[position] = recognized_char
                                self.debug_log(f"更新位置 {position} 為 '{recognized_char}'")
                        
                        self.savePreferences()
                        self.updateInterface(sender)
                        
                        if hasattr(self, 'windowController') and self.windowController:
                            if hasattr(self.windowController, 'request_controls_panel_ui_update'):
                                self.windowController.request_controls_panel_ui_update()
            
            except Exception as e:
                self.debug_log(f"智能鎖定字符處理錯誤: {e}")

        @objc.python_method
        def _get_lock_state(self):
            """取得鎖頭狀態"""
            if (hasattr(self, 'windowController') and self.windowController and 
                hasattr(self.windowController, 'controlsPanelView') and 
                self.windowController.controlsPanelView and 
                hasattr(self.windowController.controlsPanelView, 'isInClearMode')):
                return self.windowController.controlsPanelView.isInClearMode
            return True  # 預設為解鎖

        @objc.python_method
        def _recognize_character(self, input_text):
            """辨識字符（優化版）"""
            # 1. 嘗試完整輸入
            glyph = self.get_cached_glyph(Glyphs.font, input_text)
            if glyph:
                return input_text
            
            # 2. 嘗試第一個字符
            if len(input_text) > 0:
                first_char = input_text[0]
                first_glyph = self.get_cached_glyph(Glyphs.font, first_char)
                if first_glyph:
                    return first_char
            
            # 3. 解析輸入
            parsed_chars = self.parse_input_text(input_text)
            if parsed_chars:
                return parsed_chars[0]
            
            return None

        @objc.python_method
        def pickGlyphCallback(self, sender):
            """選擇字符按鈕回調（優化版）"""
            try:
                if not Glyphs.font:
                    self.debug_log("警告：沒有開啟字型檔案")
                    return
                
                # 準備選項列表
                options = self._prepare_glyph_options()
                
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
                        selected_chars = self._parse_glyph_selection(selection)
                        
                        if selected_chars:
                            self.selectedChars = selected_chars
                            self.generateNewArrangement()
                            self.lastInput = "".join(selected_chars)
                            
                            if (hasattr(self, 'windowController') and 
                                self.windowController and
                                hasattr(self.windowController, 'controlsPanelView') and 
                                self.windowController.controlsPanelView):
                                self.windowController.controlsPanelView.updateSearchField()
                            
                            self.savePreferences()
                            self.updateInterface(None)
                            
            except Exception as e:
                self.debug_log(f"選擇字符錯誤: {e}")

        @objc.python_method
        def _prepare_glyph_options(self):
            """準備字形選項列表"""
            options = []
            for glyph in Glyphs.font.glyphs:
                if glyph.unicode:
                    try:
                        char = chr(int(glyph.unicode, 16))
                        options.append(f"{char} ({glyph.name})")
                    except:
                        options.append(f".notdef ({glyph.name})")
                else:
                    options.append(f".notdef ({glyph.name})")
            return options

        @objc.python_method
        def _parse_glyph_selection(self, selection):
            """解析選擇的字形"""
            selected_chars = []
            for item in selection:
                if " (" in item and ")" in item:
                    char = item.split(" (")[0]
                    if char != ".notdef":
                        selected_chars.append(char)
            return selected_chars

        @objc.python_method
        def randomizeCallback(self, sender):
            """隨機排列按鈕回調（優化版）"""
            if not self.selectedChars:
                if Glyphs.font and Glyphs.font.selectedLayers:
                    self.updateInterface(None)
                return
            
            # 設定強制重排標記
            self.force_randomize = True
            self.generateNewArrangement()
            
            # 強制更新
            if hasattr(self, 'windowController') and self.windowController:
                if hasattr(self.windowController, 'redrawIgnoreLockState'):
                    self.windowController.redrawIgnoreLockState()
                else:
                    self.updateInterface(None)
            else:
                self.updateInterface(None)
            
            self.force_randomize = False

        @objc.python_method
        def generateNewArrangement(self):
            """生成新的字符排列（優化版）"""
            if not self.selectedChars:
                self.debug_log("沒有選擇字符，無法生成排列")
                return
            
            # 驗證鎖定字符
            if hasattr(self, 'lockedChars'):
                self.lockedChars = self.validate_locked_positions(self.lockedChars, Glyphs.font)
            
            # 檢查是否應用鎖定
            should_apply_locks = not self._get_lock_state()
            force_randomize = getattr(self, 'force_randomize', False)
            
            # 生成基礎排列
            base_arrangement = self.generate_arrangement(self.selectedChars, 8)
            
            if should_apply_locks and hasattr(self, 'lockedChars') and self.lockedChars:
                # 應用鎖定字符
                self.currentArrangement = self.apply_locked_chars(
                    base_arrangement, self.lockedChars, self.selectedChars
                )
                self.debug_log(f"應用鎖定後的排列: {self.currentArrangement}")
            else:
                # 直接使用基礎排列
                self.currentArrangement = base_arrangement
                self.debug_log(f"基礎排列: {self.currentArrangement}")
            
            self.savePreferences()

        @objc.python_method
        def loadPreferences(self):
            """載入偏好設定（優化版）"""
            # 基本設定
            self.lastInput = Glyphs.defaults.get(self.LAST_INPUT_KEY, "")
            self.selectedChars = Glyphs.defaults.get(self.SELECTED_CHARS_KEY, [])
            self.currentArrangement = Glyphs.defaults.get(self.CURRENT_ARRANGEMENT_KEY, [])
            self.zoomFactor = float(Glyphs.defaults.get(self.ZOOM_FACTOR_KEY, self.DEFAULT_ZOOM))
            
            # 視窗位置
            key_to_load_pos = self.WINDOW_POSITION_KEY
            loaded_pos = Glyphs.defaults.get(key_to_load_pos, None)
            self.windowPosition = loaded_pos
            self.debug_log(f"plugin.loadPreferences: Loaded windowPosition={loaded_pos} from key='{key_to_load_pos}'")
            
            # 控制面板可見性
            controls_panel_visible_value = Glyphs.defaults.get(self.CONTROLS_PANEL_VISIBLE_KEY)

            if controls_panel_visible_value is not None:
                self.controlsPanelVisible = bool(controls_panel_visible_value)
                self.sidebarVisible = bool(controls_panel_visible_value)  # 同步 sidebarVisible
                self.debug_log(f"plugin.loadPreferences: Loaded controlsPanelVisible={self.controlsPanelVisible} from CONTROLS_PANEL_VISIBLE_KEY")
            else:
                sidebar_visible_value = Glyphs.defaults.get(self.SIDEBAR_VISIBLE_KEY)
                if sidebar_visible_value is not None:
                    self.controlsPanelVisible = bool(sidebar_visible_value)
                    self.sidebarVisible = bool(sidebar_visible_value)
                    self.debug_log(f"plugin.loadPreferences: Loaded controlsPanelVisible={self.controlsPanelVisible} from SIDEBAR_VISIBLE_KEY (fallback)")
                else:
                    self.controlsPanelVisible = True
                    self.sidebarVisible = True
                    self.debug_log(f"plugin.loadPreferences: Set controlsPanelVisible to default True as no key was found")
            
            # 鎖定字符
            self._load_locked_chars()
            
            # === 階段2.1：如果有選定字符但沒有排列，則生成初始排列 ===
            if self.selectedChars and not self.currentArrangement:
                self.debug_log("[階段2.1] 載入偏好設定後生成初始排列")
                self.generateNewArrangement()

        @objc.python_method
        def _load_locked_chars(self):
            """載入鎖定字符設定"""
            locked_chars_str = Glyphs.defaults.get(self.LOCKED_CHARS_KEY)
            if locked_chars_str:
                self.lockedChars = {int(k): v for k, v in locked_chars_str.items()}
            else:
                self.lockedChars = {}
            
            previous_locked_chars_str = Glyphs.defaults.get(self.PREVIOUS_LOCKED_CHARS_KEY)
            if previous_locked_chars_str:
                self.previousLockedChars = {int(k): v for k, v in previous_locked_chars_str.items()}
            else:
                self.previousLockedChars = {}

        @objc.python_method
        def savePreferences(self):
            """儲存偏好設定（優化版）"""
            # 基本設定
            Glyphs.defaults[self.LAST_INPUT_KEY] = self.lastInput
            Glyphs.defaults[self.SELECTED_CHARS_KEY] = self.selectedChars
            Glyphs.defaults[self.CURRENT_ARRANGEMENT_KEY] = self.currentArrangement
            Glyphs.defaults[self.ZOOM_FACTOR_KEY] = self.zoomFactor
            
            # 控制面板可見性 - 同時更新新舊兩個 key
            current_controls_panel_visible = getattr(self, 'controlsPanelVisible', True) # 預設為 True
            Glyphs.defaults[self.CONTROLS_PANEL_VISIBLE_KEY] = current_controls_panel_visible
            Glyphs.defaults[self.SIDEBAR_VISIBLE_KEY] = current_controls_panel_visible # 保持同步
            self.debug_log(f"plugin.savePreferences: Saved controlsPanelVisible={current_controls_panel_visible}")
            
            # 視窗位置
            if hasattr(self, 'windowPosition') and self.windowPosition:
                key_to_save_pos = self.WINDOW_POSITION_KEY
                val_to_save_pos = self.windowPosition
                Glyphs.defaults[key_to_save_pos] = val_to_save_pos
                self.debug_log(f"plugin.savePreferences: Saved windowPosition={val_to_save_pos} to key='{key_to_save_pos}'")
            else:
                self.debug_log(f"plugin.savePreferences: windowPosition not saved (value: {getattr(self, 'windowPosition', 'Not Set')})")

            # 鎖定字符（轉換鍵為字串）
            if hasattr(self, 'lockedChars'):
                locked_chars_str = {str(k): v for k, v in self.lockedChars.items()}
                Glyphs.defaults[self.LOCKED_CHARS_KEY] = locked_chars_str
            
            if hasattr(self, 'previousLockedChars'):
                previous_locked_chars_str = {str(k): v for k, v in self.previousLockedChars.items()}
                Glyphs.defaults[self.PREVIOUS_LOCKED_CHARS_KEY] = previous_locked_chars_str
            # self.debug_log(f"plugin.savePreferences: Finished saving preferences.") # 可選的完成日誌

        @objc.python_method
        def resetZoom(self, sender):
            """重置縮放"""
            self.zoomFactor = self.DEFAULT_ZOOM
            self.savePreferences()
            self.updateInterface(None)

        @objc.python_method
        def getBaseWidth(self):
            """取得基準寬度"""
            return self.get_base_width()

        @objc.python_method
        def clearAllLockFieldsCallback(self, sender):
            """鎖定所有字符（優化版）"""
            try:
                if not Glyphs.font:
                    self.debug_log("警告：沒有開啟字型檔案")
                    return
                
                if not hasattr(self, 'lockedChars'):
                    self.lockedChars = {}
                if not hasattr(self, 'previousLockedChars'):
                    self.previousLockedChars = {}
                
                # 備份當前狀態
                self.previousLockedChars = self.lockedChars.copy()
                self.lockedChars = {}
                
                # 從控制面板取得鎖定字符
                if (hasattr(self, 'windowController') and self.windowController and
                    hasattr(self.windowController, 'controlsPanelView') and 
                    self.windowController.controlsPanelView and 
                    not self.windowController.controlsPanelView.isHidden() and
                    hasattr(self.windowController.controlsPanelView, 'lockFields')):
                    
                    for position, field in self.windowController.controlsPanelView.lockFields.items():
                        input_text = field.stringValue().strip()
                        if input_text:
                            recognized_char = self._recognize_character(input_text)
                            if recognized_char:
                                self.lockedChars[position] = recognized_char
                
                # 更新排列
                if hasattr(self, 'currentArrangement') and self.currentArrangement:
                    for position, char_or_name in self.lockedChars.items():
                        if position < len(self.currentArrangement):
                            self.currentArrangement[position] = char_or_name
                
                self.savePreferences()
                self.updateInterface(None)
                self.debug_log("已鎖定所有輸入框中的字符")
                
            except Exception as e:
                self.debug_log(f"鎖定字符錯誤: {e}")

        @objc.python_method
        def restoreAllLockFieldsCallback(self, sender):
            """解除所有鎖定（優化版）"""
            try:
                if not Glyphs.font:
                    self.debug_log("警告：沒有開啟字型檔案")
                    return
                
                if not hasattr(self, 'lockedChars'):
                    self.lockedChars = {}
                if not hasattr(self, 'previousLockedChars'):
                    self.previousLockedChars = {}
                
                # 備份當前狀態
                self.previousLockedChars = self.lockedChars.copy()
                
                # 清除所有鎖定
                self.lockedChars = {}
                
                # 重新生成排列
                if hasattr(self, 'selectedChars') and self.selectedChars:
                    self.generateNewArrangement()
                
                self.savePreferences()
                self.updateInterface(None)
                self.debug_log("已解除所有字符的鎖定")
                
            except Exception as e:
                self.debug_log(f"解除鎖定錯誤: {e}")

        @objc.python_method
        def __del__(self):
            """析構函數"""
            try:
                Glyphs.removeCallback(self.updateInterface)
                Glyphs.removeCallback(self.selectionChanged_)
            except:
                pass

        @objc.python_method
        def __file__(self):
            """回傳檔案路徑"""
            return __file__

except Exception as e:
    import traceback
    print(f"九宮格預覽外掛載入時發生錯誤: {e}")
    print(traceback.format_exc())