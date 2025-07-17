# encoding: utf-8
"""
九宮格預覽外掛 - 主程式
Nine Box Preview Plugin - Main Class (Simplified)
"""

from __future__ import division, print_function, unicode_literals
import traceback
import objc
from Foundation import NSObject, NSNotificationCenter, NSUserDefaultsDidChangeNotification
from AppKit import NSMenuItem, NSUserDefaults
from GlyphsApp import *
from GlyphsApp.plugins import *

try:
    # 設定 GeneralPlugin 子類別
    class NineBoxView(GeneralPlugin):
        """
        九宮格預覽外掛主類別
        Nine Box Preview Plugin Main Class (Simplified)
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
            })
            
            # 匯入模組（延遲匯入以避免反覆依賴）
            self._import_modules()
            
            # 初始化屬性
            self._initialize_properties()
            
            # 初始化事件處理器
            self.event_handlers = self.EventHandlers(self)
            
            print("九宮格預覽外掛已成功載入。")
        
        @objc.python_method
        def _import_modules(self):
            """匯入所需模組"""
            # 匯入常數
            from core.constants import (
                LAST_INPUT_KEY, SELECTED_CHARS_KEY, CURRENT_ARRANGEMENT_KEY,
                ZOOM_FACTOR_KEY, WINDOW_POSITION_KEY, CONTROLS_PANEL_VISIBLE_KEY,
                LOCKED_CHARS_KEY, PREVIOUS_LOCKED_CHARS_KEY, LOCK_MODE_KEY, WINDOW_SIZE_KEY,
                ORIGINAL_ARRANGEMENT_KEY, FINAL_ARRANGEMENT_KEY,
                DEFAULT_WINDOW_SIZE, MIN_WINDOW_SIZE, CONTROLS_PANEL_WIDTH,
                DEFAULT_ZOOM, DEBUG_MODE, FULL_ARRANGEMENT_SIZE, CENTER_POSITION
            )
            
            # 匯入工具函數
            from core.utils import (
                log_to_macro_window, debug_log, error_log, clear_cache,
                load_preferences, save_preferences, get_base_width,
                parse_input_text, get_cached_glyph, get_cached_width
            )
            
            # 匯入事件處理器
            from handlers.event_handlers import EventHandlers
            
            # 匯入視窗控制器
            from ui.window_controller import NineBoxWindow
            
            # 儲存到 self 中
            self.NineBoxWindow = NineBoxWindow
            self.EventHandlers = EventHandlers
            
            # 工具函數
            self.log_to_macro_window = log_to_macro_window
            self.debug_log = debug_log
            self.error_log = error_log
            self.clear_cache = clear_cache
            self.load_preferences = load_preferences
            self.save_preferences = save_preferences
            self.get_base_width = get_base_width
            self.parse_input_text = parse_input_text
            self.get_cached_glyph = get_cached_glyph
            self.get_cached_width = get_cached_width

            # 驗證工具函數是否正確匯入
            if not hasattr(self, 'get_base_width'):
                self.debug_log("警告：get_base_width 未正確匯入")
            
            # 常數
            self.LAST_INPUT_KEY = LAST_INPUT_KEY
            self.SELECTED_CHARS_KEY = SELECTED_CHARS_KEY
            self.CURRENT_ARRANGEMENT_KEY = CURRENT_ARRANGEMENT_KEY
            self.ZOOM_FACTOR_KEY = ZOOM_FACTOR_KEY
            self.WINDOW_POSITION_KEY = WINDOW_POSITION_KEY
            self.CONTROLS_PANEL_VISIBLE_KEY = CONTROLS_PANEL_VISIBLE_KEY
            self.LOCKED_CHARS_KEY = LOCKED_CHARS_KEY
            self.PREVIOUS_LOCKED_CHARS_KEY = PREVIOUS_LOCKED_CHARS_KEY
            self.LOCK_MODE_KEY = LOCK_MODE_KEY
            self.ORIGINAL_ARRANGEMENT_KEY = ORIGINAL_ARRANGEMENT_KEY
            self.FINAL_ARRANGEMENT_KEY = FINAL_ARRANGEMENT_KEY
            self.WINDOW_SIZE_KEY = WINDOW_SIZE_KEY
            self.DEFAULT_ZOOM = DEFAULT_ZOOM
            self.DEFAULT_WINDOW_SIZE = DEFAULT_WINDOW_SIZE
            self.DEBUG_MODE = DEBUG_MODE
        
        @objc.python_method
        def _initialize_properties(self):
            """初始化屬性"""
            # 初始化預設值
            self.selectedChars = []
            self.currentArrangement = []
            self.originalArrangement = []  # 儲存原始隨機排列
            self.finalArrangement = []  # 儲存關閉前的最終狀態
            self.windowController = None
            self.previousLockedChars = {}
            self.controlsPanelVisible = False
            self.windowSize = self.DEFAULT_WINDOW_SIZE # 初始化 windowSize
            self.windowPosition = None
            self._update_scheduled = False  # 防止重複更新
            
            # 載入偏好設定（會覆蓋預設值）
            self.load_preferences(self)

        @objc.python_method
        def start(self):
            """啟動外掛"""
            try:
                # 新增選單項
                newMenuItem = NSMenuItem(self.name, self.toggleWindow_)
                Glyphs.menu[WINDOW_MENU].append(newMenuItem)

                # 新增回呼函數 - 使用正確的 Glyphs API 事件
                Glyphs.addCallback(self.updateInterface, UPDATEINTERFACE)
                Glyphs.addCallback(self.updateInterface, DOCUMENTACTIVATED)
                Glyphs.addCallback(self.selectionChanged_, DOCUMENTOPENED)
                Glyphs.addCallback(self.selectionChanged_, SELECTIONCHANGED)
                Glyphs.addCallback(self.selectionChanged_, CURRENTGLYPHCHANGED)  # 當前字符變更
                Glyphs.addCallback(self.selectionChanged_, TABDIDOPEN)  # 分頁開啟
                Glyphs.addCallback(self.selectionChanged_, TABWILLCLOSE)  # 分頁關閉
                Glyphs.addCallback(self.selectionChanged_, DOCUMENTWASOPENED)  # 文檔開啟
                Glyphs.addCallback(self.selectionChanged_, DOCUMENTWILLCLOSE)  # 文檔關閉

                # 載入偏好設定
                self.loadPreferences()
                
            except Exception as e:
                self.error_log("啟動外掛時發生錯誤", e)

        # === 視窗操作 ===

        @objc.python_method
        def toggleWindow_(self, sender):
            """切換視窗顯示狀態"""
            try:
                # 只在視窗控制器不存在時載入偏好設定，避免覆蓋現有狀態
                if self.windowController is None:
                    self.loadPreferences()
                    self.debug_log("[切換視窗] 首次開啟，已載入偏好設定")
                    self.debug_log(f"  - lastInput: '{self.lastInput}'")
                    self.debug_log(f"  - selectedChars: {self.selectedChars}")
                    self.debug_log(f"  - lockedChars: {self.lockedChars}")
                    self.debug_log(f"  - currentArrangement: {self.currentArrangement}")
                else:
                    self.debug_log("[切換視窗] 使用現有視窗控制器，保持現有狀態")
                
                if self.windowController is None:
                    # 初次開啟視窗
                    self.debug_log("[切換視窗] 初始化新視窗控制器")
                    self.windowController = self.NineBoxWindow.alloc().initWithPlugin_(self)
                    
                    # 檢查初始化是否成功
                    if self.windowController is None:
                        self.debug_log("初始化視窗控制器失敗")
                        Glyphs.showNotification(
                            self.name,
                            "初始化視窗失敗，請檢查控制台記錄"
                        )
                        return
                else:
                    # 視窗已存在，但可能需要重新載入狀態
                    self.debug_log("[切換視窗] 使用現有視窗控制器")
                    
                    # 強制更新控制面板 UI
                    if (hasattr(self.windowController, 'controlsPanelView') and 
                        self.windowController.controlsPanelView):
                        self.debug_log("[切換視窗] 強制更新控制面板 UI")
                        self.windowController.controlsPanelView.update_ui(self, update_lock_fields=True)
                    
                    # 確保預覽視圖顯示最新狀態（不觸發隨機排列）
                    if (hasattr(self, 'event_handlers') and 
                        hasattr(self.windowController, 'previewView') and
                        self.windowController.previewView and
                        hasattr(self, 'currentArrangement')):
                        self.debug_log("[切換視窗] 同步現有排列到預覽視圖")
                        self.windowController.previewView.currentArrangement = self.currentArrangement
                
                # 確保視窗控制器有效後再顯示視窗
                if self.windowController is not None:
                    self.windowController.makeKeyAndOrderFront()
                
            except Exception as e:
                self.error_log("切換視窗時發生錯誤", e)

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

        # === 事件處理委派 ===
        
        @objc.python_method
        def updateInterface(self, sender):
            """更新介面 - 委派給事件處理器"""
            if hasattr(self, 'event_handlers'):
                self.event_handlers.update_interface(sender)
        
        @objc.python_method
        def updateInterfaceForSearchField(self, sender):
            """專為搜尋欄位的更新 - 委派給事件處理器"""
            if hasattr(self, 'event_handlers'):
                self.event_handlers.update_interface_for_search_field(sender)
        
        @objc.python_method
        def selectionChanged_(self, sender):
            """選擇變更處理 - 委派給事件處理器"""
            if hasattr(self, 'event_handlers'):
                self.event_handlers.selection_changed(sender)
        
        @objc.python_method
        def searchFieldCallback(self, sender):
            """處理搜尋欄位輸入 - 委派給事件處理器"""
            if hasattr(self, 'event_handlers'):
                self.event_handlers.search_field_callback(sender)
        
        @objc.python_method
        def smartLockCharacterCallback(self, sender):
            """智慧鎖定字符回呼 - 委派給事件處理器"""
            if hasattr(self, 'event_handlers'):
                self.event_handlers.smart_lock_character_callback(sender)
        
        @objc.python_method
        def clearAllLockFieldsCallback(self, sender):
            """清空所有鎖定輸入框 - 委派給事件處理器"""
            if hasattr(self, 'event_handlers'):
                self.event_handlers.clear_all_lock_fields_callback(sender)
        
        @objc.python_method
        def pickGlyphCallback(self, sender):
            """選擇字符按鈕回呼 - 委派給事件處理器"""
            if hasattr(self, 'event_handlers'):
                self.event_handlers.pick_glyph_callback(sender)
        
        @objc.python_method
        def randomizeCallback(self, sender):
            """隨機排列按鈕回呼 - 委派給事件處理器"""
            if hasattr(self, 'event_handlers'):
                self.event_handlers.randomize_callback(sender)
        
        @objc.python_method
        def resetZoom(self, sender):
            """重置縮放 - 委派給事件處理器"""
            if hasattr(self, 'event_handlers'):
                self.event_handlers.reset_zoom(sender)
        
        @objc.python_method
        def generateNewArrangement(self):
            """生成新的字符排列 - 委派給事件處理器"""
            if hasattr(self, 'event_handlers'):
                self.event_handlers.generate_new_arrangement()
        
        # === 偏好設定 ===
        
        @objc.python_method
        def loadPreferences(self):
            """載入偏好設定"""
            self.load_preferences(self)
        
        @objc.python_method
        def savePreferences(self):
            """儲存偏好設定"""
            self.save_preferences(self)
        
        # === 生命週期 ===
        
        @objc.python_method
        def __del__(self):
            """解構式"""
            try:
                # 移除所有回調
                events_list = [
                    UPDATEINTERFACE, DOCUMENTACTIVATED, DOCUMENTOPENED, 
                    SELECTIONCHANGED, CURRENTGLYPHCHANGED, TABDIDOPEN, 
                    TABWILLCLOSE, DOCUMENTWASOPENED, DOCUMENTWILLCLOSE
                ]
                
                for callback in [self.updateInterface, self.selectionChanged_]:
                    for event in events_list:
                        try:
                            Glyphs.removeCallback(callback, event)
                        except:
                            pass
            except:
                pass

        @objc.python_method
        def getBaseWidth(self):
            """取得基準寬度 - 委派給工具函數"""
            try:
                if not hasattr(self, 'get_base_width'):
                    self.debug_log("getBaseWidth: get_base_width 方法未初始化")
                    return 1000
                width = self.get_base_width()
                # 確保回傳值是有效的數字
                if not isinstance(width, (int, float)) or width <= 0:
                    self.debug_log(f"getBaseWidth: 無效的寬度值 {width}")
                    return 1000
                return width
            except Exception as e:
                self.error_log("getBaseWidth 錯誤", e)
                return 1000  # 預設值
        
        @objc.python_method
        def __file__(self):
            """回傳檔案路徑"""
            return __file__

except Exception as e:
    import traceback
    print(f"九宮格預覽外掛載入時發生錯誤: {e}")
    print(traceback.format_exc())
