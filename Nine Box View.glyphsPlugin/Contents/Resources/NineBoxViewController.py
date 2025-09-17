# encoding: utf-8

"""
NineBoxView Controller
主要控制器類別，處理所有外掛業務邏輯
基於平面座標系統 (0-8) 的現代化架構
"""

import objc
import traceback
from GlyphsApp import Glyphs

# 平面座標系統常數
GRID_TOTAL = 9  # 0-8 座標
CENTER_POSITION = 4  # 中央位置

# 匯入進階重繪支援
try:
    from NineBoxView.core.grid_manager import GridManager
    from NineBoxView.data.cache import clear_all_cache
except ImportError:
    # 復原方案：可能在初始化期間
    GridManager = None

class NineBoxViewController:
    """
    九宮格外掛主控制器
    基於平面座標系統的現代化架構
    純業務邏輯層 - 不處理 UI 或視窗管理
    """
    
    def __init__(self, parent_plugin=None):
        """初始化控制器
        
        Args:
            parent_plugin: 父插件實例（用於視窗管理通訊）
        """
        self._parent_plugin = parent_plugin
        self._initialize_properties()
        self.initializeComponents()
    
    def _initialize_properties(self):
        """初始化屬性"""
        # 外掛資訊
        self.name = self._parent_plugin.name
        
        # 三層架構：平面座標系統統一九宮格資料
        self.base_glyphs = [''] * GRID_TOTAL      # 最底層：當前字符讀取（不持久化）
        self.base_arrangement = [''] * GRID_TOTAL # 第二層：搜尋輸入框狀態（持久化）  
        self.lock_inputs = [''] * GRID_TOTAL      # 最上層：鎖定輸入框狀態（持久化）
        
        # 向後相容：保留舊的 grid 屬性（指向 base_arrangement）
        self.grid = self.base_arrangement
        
        # 業務狀態（視窗相關屬性保留用於偏好設定）
        self.controlsPanelVisible = False
        self.controlsPanelWidth = 150  # 控制面板寬度
        self.windowSize = (500, 400)  # 預設視窗大小
        self.windowPosition = None
        
        # 搜尋和鎖定狀態
        self.lastInput = ""
        self.isLockFieldsActive = True
        
        
        # 載入偏好設定
        self.loadPreferences()
    
    def initializeComponents(self):
        """初始化元件（整合進階重繪支援）"""
        from NineBoxView.core.event_handler import NineBoxEventHandler
        
        # 建立事件處理器
        self.event_handler = NineBoxEventHandler(self)
        
        # 初始化網格管理器（進階重繪支援）
        try:
            if GridManager:
                self.grid_manager = GridManager()
                # 同步初始狀態到基礎排列層
                self.grid_manager.grid_glyphs = self.base_arrangement[:]
            else:
                self.grid_manager = None
        except Exception:
            print(traceback.format_exc())
            self.grid_manager = None
        
        # 工具方法
        self._setup_utility_methods()
                
    def _setup_utility_methods(self):
        """設定工具方法"""
        # 基本工具函數將在需要時動態載入
        pass
    
    def loadPreferences(self):
        """載入偏好設定"""
        try:
            from NineBoxView.data.preferences import PreferencesManager
            prefs = PreferencesManager()
            
            # 載入基本設定
            self.lastInput = prefs.get_string('lastInput', '')
            
            # 優先讀取新的 isLockFieldsActive 設定，如果不存在則從舊的 isInClearMode 轉換
            if prefs.has_key('isLockFieldsActive'):
                self.isLockFieldsActive = prefs.get_bool('isLockFieldsActive', True)
            else:
                # 向後相容：讀取舊的 isInClearMode 並反轉為新的 isLockFieldsActive
                old_clear_mode = prefs.get_bool('isInClearMode', False)
                self.isLockFieldsActive = not old_clear_mode
            self.controlsPanelVisible = prefs.get_bool('controlsPanelVisible', False)
            self.controlsPanelWidth = prefs.get_int('controlsPanelWidth', 150)
            
            # 載入視窗狀態
            self.windowSize = prefs.get_size('windowSize', (500, 400))
            self.windowPosition = prefs.get_point('windowPosition', None)
            
            # 載入兩層分離的資料結構
            self.base_arrangement = prefs.get_grid('base_arrangement', [''] * GRID_TOTAL)  # 第一層：基礎排列
            self.lock_inputs = prefs.get_grid('lock_inputs', [''] * GRID_TOTAL)            # 第二層：鎖定覆寫
            
            # 向後相容性：如果存在舊的 grid 資料，遷移到新架構
            if prefs.has_key('grid') and not prefs.has_key('base_arrangement'):
                old_grid = prefs.get_grid('grid', [''] * GRID_TOTAL)
                self.base_arrangement = old_grid[:]
            
        except Exception:
            print(traceback.format_exc())
    
    def savePreferences(self):
        """儲存偏好設定（簡化版）"""
        self._perform_save_preferences()
    
    
    def _perform_save_preferences(self):
        """實際執行偏好設定儲存"""
        try:
            from NineBoxView.data.preferences import PreferencesManager
            prefs = PreferencesManager()
            
            # 儲存基本設定
            prefs.set_string('lastInput', self.lastInput)
            prefs.set_bool('isLockFieldsActive', self.isLockFieldsActive)
            prefs.set_bool('controlsPanelVisible', self.controlsPanelVisible)
            prefs.set_int('controlsPanelWidth', self.controlsPanelWidth)
            
            # 儲存視窗狀態
            prefs.set_size('windowSize', self.windowSize)
            prefs.set_point('windowPosition', self.windowPosition)
            
            # 儲存兩層分離的資料結構
            prefs.set_grid('base_arrangement', self.base_arrangement)  # 第一層：基礎排列
            prefs.set_grid('lock_inputs', self.lock_inputs)            # 第二層：鎖定覆寫
            
            prefs.save()
            
        except Exception:
            print(traceback.format_exc())
    
    # ============================================================================
    # 平面座標系統核心方法
    # ============================================================================
    
    def get_center_glyph(self):
        """取得中央格顯示的字符
        
        Returns:
            str: 中央格字符（位置4）
        """
        # 兩層架構：優先鎖定層，否則使用基礎層
        if self.lock_inputs[CENTER_POSITION]:
            return self.lock_inputs[CENTER_POSITION]
        return self.base_arrangement[CENTER_POSITION]
    
    def set_center_glyph(self, glyph):
        """設定中央格字符（操作基礎層）"""
        self.base_arrangement[CENTER_POSITION] = glyph or ''
    
    def _update_base_glyphs(self):
        """更新最底層 base_glyphs 陣列（全格位即時更新，不持久化）
        
        所有 9 個位置都使用即時更新：
        - 中央格：即時 get_selected_glyph() + 三層備份機制
        - 周圍格：即時標準模式重繪（基於中央格的相關字符）
        """
        try:
            # 匯入必要模組（有條件匯入，避免測試環境報錯）
            try:
                from NineBoxView.core.utils import FontManager
                font, master = FontManager.getCurrentFontContext()
            except ImportError:
                # 測試環境或 GlyphsApp 不可用時
                font, master = None, None
            
            if not font or not master:
                # 沒有有效字型時，清空 base_glyphs
                self.base_glyphs = [''] * GRID_TOTAL
                return
            
            # === 中央格：即時選擇 + 三層備份機制 ===
            center_char = ''
            if hasattr(self, 'event_handler'):
                # 第一優先級：即時字符選擇
                current_glyph = self.event_handler.get_selected_glyph()
                if current_glyph:
                    center_char = current_glyph
                else:
                    # 三層備份機制：當沒有選中字符時的備份邏輯
                    center_char = self._get_center_char_with_backup(font, master)
            
            self.base_glyphs[CENTER_POSITION] = center_char
            
            # === 周圍格：簡化邏輯，直接使用當前字符填滿所有位置 ===
            if center_char:
                # 將當前字符填入所有周圍格
                surrounding_positions = [0, 1, 2, 3, 5, 6, 7, 8]
                for pos in surrounding_positions:
                    self.base_glyphs[pos] = center_char
            else:
                # 中央格為空時，清空所有周圍格
                for pos in [0, 1, 2, 3, 5, 6, 7, 8]:
                    self.base_glyphs[pos] = ''
                    
        except Exception:
            print(traceback.format_exc())
            # 例外時清空所有位置
            self.base_glyphs = [''] * GRID_TOTAL
    
    def _get_center_char_with_backup(self, font, master):
        """中央格三層備份機制（當沒有選中字符時使用）
        
        三層備份順序：
        1. Light Table 比較版本（如果啟用且按下 Shift）
        2. tab.layers 備份機制（Edit View 模式）
        3. 標準 cache 機制（最後復原）
        
        Args:
            font: 當前字型
            master: 當前 Master
            
        Returns:
            str: 備份的中央格字符
        """
        try:
            # 這裡可以實作更複雜的備份邏輯，目前暫時返回空字符
            # 未來可以整合 Light Table 支援等高級功能
            return ''
        except Exception:
            print(traceback.format_exc())
            return ''
    
    def _get_related_chars(self, font, center_char):
        """取得與中央字符相關的字符列表（周圍格使用）
        
        Args:
            font: 當前字型
            center_char (str): 中央字符
            
        Returns:
            list: 最多8個相關字符
        """
        try:
            related = []
            
            # 如果是單個字符，嘗試找相近的 Unicode 字符
            if len(center_char) == 1:
                center_code = ord(center_char)
                
                # 搜尋前後各幾個字符
                for offset in [-4, -3, -2, -1, 1, 2, 3, 4]:
                    try:
                        related_code = center_code + offset
                        if 0x20 <= related_code <= 0x10FFFF:  # 有效 Unicode 範圍
                            related_char = chr(related_code)
                            # 檢查字型中是否有這個字符
                            from NineBoxView.data.cache import get_glyph_with_fallback
                            glyph = get_glyph_with_fallback(font, related_char)
                            if glyph:
                                related.append(related_char)
                                if len(related) >= 8:
                                    break
                    except (ValueError, OverflowError):
                        continue
            
            # 如果找不到足夠的相關字符，用空字符補足
            while len(related) < 8:
                related.append('')
                
            return related[:8]  # 最多返回8個
            
        except Exception:
            print(traceback.format_exc())
            return [''] * 8
    
    def displayArrangement(self):
        """三層架構的統一顯示排列合併器（整合即時更新）
        
        三層分離架構：
        1. base_glyphs: 最底層（當前字符讀取，不持久化）
        2. base_arrangement: 第二層（搜尋結果、隨機排列，持久化）
        3. lock_inputs: 最上層（用戶鎖定的字符，持久化）
        
        合併優先級：
        lock_inputs > base_arrangement > base_glyphs
        + 中央格即時檢查（最高優先級）
        """
        # 確保 base_glyphs 是最新的（包括周圍格即時跟隨）
        self._update_base_glyphs()
        
        # 第一層：從最底層 base_glyphs 開始
        arrangement = self.base_glyphs[:]
        
        # 第二層：條件性套用 base_arrangement（差異化處理：即時重繪 + 行為一致性）
        # 平衡修復：既保持即時重繪，又確保無效字符與空輸入行為一致
        if self.lastInput:  # 有任何輸入內容就處理（恢復即時重繪）
            if self.has_valid_search_input():
                # 有效輸入：使用搜尋排列結果
                for pos in range(GRID_TOTAL):
                    if self.base_arrangement[pos]:
                        arrangement[pos] = self.base_arrangement[pos]
            # 無效輸入：保持 base_glyphs 即時內容（維持您的核心改進：與空輸入行為一致）
        
        # 第三層：只在上鎖狀態時套用鎖定覆寫層（排除中央格）
        if self.isLockFieldsActive:
            for pos in range(GRID_TOTAL):
                if pos != CENTER_POSITION and self.lock_inputs[pos]:
                    # 顯示時解析鎖定輸入，取第一個有效字符
                    raw_input = self.lock_inputs[pos]
                    try:
                        from NineBoxView.core.input_recognition import parse_glyph_input
                        parsed_chars = parse_glyph_input(raw_input)
                        # 修復：只有在解析出有效字符時才覆寫，無效字符時保留底層內容
                        if parsed_chars:  # 只有在有有效字符時才覆寫
                            arrangement[pos] = parsed_chars[0]
                        # 無有效字符時不做任何操作，保留底層內容
                    except ImportError:
                        # 復原：只有在非空輸入時才覆寫（向後相容且安全）
                        if raw_input and raw_input.strip():
                            arrangement[pos] = raw_input
                        # 空白輸入時保留底層內容
        
        # 最後階段：中央格即時檢查（恢復穩定版本的即時重繪邏輯）
        if self.event_handler:
            current_glyph = self.event_handler.get_selected_glyph()
            if current_glyph:  # 即時字符選擇具有最高優先級
                arrangement[CENTER_POSITION] = current_glyph
            else:  # 沒有選中字符時，中央格始終為空
                arrangement[CENTER_POSITION] = ''
        
        return arrangement
    
    def compose_display_arrangement(self):
        """合成最終顯示排列（統一資料源方法）
        
        在平面座標系統中，這個方法直接返回 grid，
        但保留此介面以保持向後相容性
        """
        # 同步網格狀態（如果使用 GridManager）
        if self.grid_manager:
            # 檢查狀態是否有變化（使用顯示排列）
            display_arrangement = self.displayArrangement()
            if self.grid_manager.grid_glyphs != display_arrangement:
                self.grid_manager.grid_glyphs = display_arrangement[:]
        
        return self.displayArrangement()
        
    def getBaseWidth(self):
        """取得基準寬度（採用官方模式統一上下文）
        
        整合 6570fe8 修復：支援 Default Layer Width 參數解析
        
        Returns:
            float: 基準字符寬度
        """
        try:
            # 使用統一的字型上下文獲取
            from NineBoxView.core.utils import FontManager
            font, master = FontManager.getCurrentFontContext()
            if not font or not master:
                return 1000
            
            # === 1. 優先檢查 Master 的 Default Layer Width 參數（6570fe8 修復）===
            try:
                if (master and hasattr(master, 'customParameters') and 
                    'Default Layer Width' in master.customParameters):
                    # 使用官方推薦的字典存取語法
                    param_value = master.customParameters['Default Layer Width']
                    if param_value is not None:
                        # 處理可能的格式如 'han: 950'
                        if isinstance(param_value, str) and ':' in param_value:
                            # 取冒號後的數值部分
                            value_part = param_value.split(':', 1)[1].strip()
                            default_width = float(value_part)
                        else:
                            default_width = float(param_value)
                        
                        if default_width > 0:
                            return default_width
                            
            except (ValueError, TypeError, KeyError):
                print(traceback.format_exc())
            
            # === 2. 使用中央格字符寬度（通過統一偵測方法）===
            if self.event_handler:
                current_glyph = self.event_handler.get_selected_glyph()
                if current_glyph:
                    glyph = font.glyphs[current_glyph]
                    if glyph:
                        layer = glyph.layers[master.id]
                        if layer and layer.width > 0:
                            return layer.width
                
                # === 3. 復原到字型平均寬度（簡化版本）===
                total_width = 0
                count = 0
                for glyph in font.glyphs[:100]:  # 只檢查前100個字符
                    if glyph.layers[master.id] and glyph.layers[master.id].width > 0:
                        total_width += glyph.layers[master.id].width
                        count += 1
                        if count >= 20:  # 最多取得20個有效樣本
                            break
                
                if count > 0:
                    return total_width / count
            
            # === 4. 最後的備選值 ===
            return 1000
            
        except Exception:
            print(traceback.format_exc())
            return 1000
    
    def randomize_grid(self):
        """兩層架構：填充基礎排列層（使用 tempData 快取優化）"""
        try:
            # 更新防抖時間戳（修復首次開啟後快速雙擊的雙重隨機排列問題）
            self._update_debounce_timestamp()
            
            # 獲取當前 master 用於快取（暫時未使用，保留供未來優化）
            master = None
            try:
                from NineBoxView.core.utils import FontManager
                _, master = FontManager.getCurrentFontContext()
            except:
                pass
            
            # 避免未使用參數警告（master 保留供未來快取功能使用）
            _ = master
            
            # 取得可用字符
            chars = self._get_available_chars()
            
            if not chars:
                # 沒有可用字符時，基礎排列全部設為空字符
                self.base_arrangement = [''] * GRID_TOTAL
            else:
                # 使用 GridManager 的隨機填充功能
                if hasattr(self, 'grid_manager') and self.grid_manager:
                    # 先同步基礎排列層到 GridManager
                    self.grid_manager.grid_glyphs = self.base_arrangement[:]
                    
                    # 使用新架構的 GridManager 進行隨機填充
                    changed = self.grid_manager.randomize_surrounding_positions(chars)
                    if changed:
                        # 同步 GridManager 的結果到基礎排列層
                        self.base_arrangement = self.grid_manager.displayArrangement()
                else:
                    # 復原方案：使用隨機排列服務（支援 tempData 快取）
                    try:
                        from NineBoxView.core.random_arrangement import get_random_service
                        random_service = get_random_service()
                        if random_service:
                            # 填充整個基礎排列層（包含中央格）
                            random_chars = random_service.create_non_repeating_batch(chars, GRID_TOTAL)
                            for i in range(GRID_TOTAL):
                                self.base_arrangement[i] = random_chars[i] if i < len(random_chars) else ''
                        else:
                            raise ImportError("隨機服務不可用")
                    except ImportError:
                        # 最終復原方案：簡單隨機分配到基礎排列層
                        import random
                        for pos in range(GRID_TOTAL):
                            self.base_arrangement[pos] = random.choice(chars)
            
        except Exception:
            print(traceback.format_exc())
    
    def _update_debounce_timestamp(self):
        """更新防抖時間戳（修復首次開啟後快速雙擊的雙重隨機排列問題）"""
        try:
            # 檢查是否有活躍的 preview_view
            if (hasattr(self, 'parent_plugin') and self.parent_plugin and
                hasattr(self.parent_plugin, 'window_controller') and 
                self.parent_plugin.window_controller and
                hasattr(self.parent_plugin.window_controller, 'previewView') and
                self.parent_plugin.window_controller.previewView):
                
                preview_view = self.parent_plugin.window_controller.previewView
                
                # 更新防抖時間戳
                if hasattr(preview_view, '_last_randomize_time'):
                    import time
                    preview_view._last_randomize_time = time.monotonic()
                    
        except Exception:
            # 防抖時間戳更新失敗不應影響主要功能
            pass
    
    def _get_available_chars(self):
        """取得可用於填充的字符列表（使用 tempData 快取優化）
        
        新的簡潔邏輯：
        - 當有選擇當前字符時：lastInput為空用當前字符，有內容用內容填充
        - 當沒有選擇字符時：lastInput為空用空字符，有內容用內容填充
        """
        # 獲取當前 master 用於快取
        master = None
        try:
            from NineBoxView.core.utils import FontManager
            _, master = FontManager.getCurrentFontContext()
        except:
            pass
        
        # 檢查是否有當前選擇的字符
        current_glyph = None
        if self.event_handler:
            current_glyph = self.event_handler.get_selected_glyph()
        
        if current_glyph:
            # 有選擇當前字符時
            if self.lastInput:
                # lastInput 有內容 → 使用內容填充
                from NineBoxView.core.input_recognition import parse_glyph_input
                chars = parse_glyph_input(self.lastInput, master=master)
                if chars:
                    return chars  # 有效輸入：使用解析結果
                else:
                    # 無效輸入：復原到當前字符（與全空輸入一致）
                    return [current_glyph]
            else:
                # lastInput 為空 → 使用當前字符
                return [current_glyph]
        else:
            # 沒有選擇字符時
            if self.lastInput:
                # lastInput 有內容 → 使用內容填充
                from NineBoxView.core.input_recognition import parse_glyph_input
                chars = parse_glyph_input(self.lastInput, master=master)
                if chars:
                    return chars  # 有效輸入：使用解析結果
                else:
                    # 無效輸入：復原到空字符邏輯（與全空輸入一致）
                    return []
            else:
                # lastInput 為空 → 使用空字符
                return []
    
    @property
    def selectedChars(self):
        """動態解析的有效字符列表（向後相容性 property）
        
        這個 property 提供向後相容性，讓現有程式碼可以繼續存取 selectedChars，
        但實際上是基於當前的 lastInput 即時解析得出的結果。
        
        Returns:
            list: 解析出的有效字符列表，無效輸入時返回空列表
        """
        if not self.lastInput:
            return []
        
        try:
            from NineBoxView.core.input_recognition import parse_glyph_input
            return parse_glyph_input(self.lastInput)
        except Exception:
            # 解析失敗時返回空列表
            return []
    
    def has_valid_search_input(self):
        """檢查是否有有效的搜尋輸入（即時解析，無狀態依賴）
        
        這個方法統一判斷搜尋輸入框的內容是否包含有效字符，
        用於替代單純的 lastInput 檢查，確保無效字符與空輸入有一致的行為。
        
        使用即時解析策略，消除狀態同步問題，始終基於最新的 lastInput 進行判斷。
        
        Returns:
            bool: True 如果有有效的搜尋字符，False 如果輸入為空或全部無效
        """
        if not self.lastInput:
            return False
        
        try:
            from NineBoxView.core.input_recognition import parse_glyph_input
            parsed_chars = parse_glyph_input(self.lastInput)
            return bool(parsed_chars)
        except Exception:
            # 解析失敗時視為無效輸入
            return False
    
    # ============================================================================
    # 視窗管理介面（委派給視窗層）
    # ============================================================================
    
    def should_randomize_on_show(self):
        """智慧判斷是否需要隨機化（減法重構：避免不必要的隨機化）
        
        Returns:
            bool: True 如果需要隨機化，False 如果有現有內容可用
        """
        try:
            # 1. 有保存的排列內容 → 不需要隨機化
            if any(self.base_arrangement):
                return False
                
            # 2. 有當前選中字符 → 用字符填充，不需要隨機化
            if self.event_handler:
                current_glyph = self.event_handler.get_selected_glyph()
                if current_glyph:
                    return False
                    
            # 3. 搜尋框有內容且有效 → 用內容填充，不需要隨機化  
            if self.lastInput and self.lastInput.strip():
                try:
                    from NineBoxView.core.input_recognition import parse_glyph_input
                    chars = parse_glyph_input(self.lastInput.strip())
                    if chars:  # 有有效字符就不需要隨機化
                        return False
                except ImportError:
                    pass  # 如果模組無法載入，繼續下一步檢查
            
            # 4. 只有在真正無任何內容時才隨機化
            return True
            
        except Exception:
            print(traceback.format_exc())
            return True  # 安全復原：發生錯誤時隨機化

    def initialize_grid_content(self):
        """初始化九宮格內容（智慧填充替代盲目隨機化）
        
        根據實際可用內容決定如何初始化九宮格，避免不必要的隨機化
        """
        try:
            if self.should_randomize_on_show():
                # 真正需要隨機化時才隨機化
                self.randomize_grid()
            else:
                # 使用現有內容：觸發重繪讓 displayArrangement() 的三層邏輯發揮作用
                # 這會根據當前字符、搜尋內容或保存的排列來填充九宮格
                if hasattr(self, 'event_handler') and self.event_handler:
                    self.event_handler.update_and_redraw_grid()
                    
        except Exception:
            print(traceback.format_exc())
            # 例外時復原到隨機化
            self.randomize_grid()

    def request_window_creation(self):
        """請求建立視窗（抽象方法，由 plugin 層實作）
        
        這個方法不直接建立視窗，而是委派給父插件實作
        
        Returns:
            object: 視窗控制器實例（由父插件建立）
        """
        try:
            if (self._parent_plugin and 
                hasattr(self._parent_plugin, 'create_window_for_controller')):
                return self._parent_plugin.create_window_for_controller(self)
            return None
        except Exception:
            print(traceback.format_exc())
            return None
    
    def show_window(self, window_controller=None):
        """顯示視窗（純業務邏輯）
        
        Args:
            window_controller: 視窗控制器實例（由呼叫方管理）
        """
        try:
            # 首次顯示時載入偏好設定
            self.loadPreferences()
            
            # 使用智慧內容感知邏輯初始化九宮格（減法重構：避免盲目隨機化）
            self.initialize_grid_content()
            
            # 避免未使用參數警告
            _ = window_controller
                
        except Exception:
            print(traceback.format_exc())
    
    def has_active_window(self):
        """檢查是否有活躍的視窗（抽象視窗介面）
        
        Returns:
            bool: True 如果有活躍的預覽視窗
        """
        try:
            # 抽象視窗狀態檢查：委派給父插件
            if (self._parent_plugin and 
                hasattr(self._parent_plugin, 'has_active_preview_window')):
                return self._parent_plugin.has_active_preview_window()
            return False
        except Exception:
            print(traceback.format_exc())
            return False
    
    def update_preview_view(self, arrangement=None):
        """更新預覽視圖（抽象視窗介面）
        
        Args:
            arrangement: 指定的排列，預設使用當前 displayArrangement
        
        Returns:
            bool: True 如果更新成功
        """
        try:
            if not self.has_active_window():
                return False
            
            # 使用指定的排列或當前排列
            if arrangement is None:
                arrangement = self.displayArrangement()
            
            # 抽象視窗更新：委派給父插件
            if (self._parent_plugin and 
                hasattr(self._parent_plugin, 'update_preview_arrangement')):
                return self._parent_plugin.update_preview_arrangement(arrangement)
                
            return False
            
        except Exception:
            print(traceback.format_exc())
            return False
    
    def trigger_preview_redraw(self, use_refresh=False):
        """觸發預覽視圖重繪（抽象視窗介面）
        
        Args:
            use_refresh: True 使用完整重繪， False 使用快速重繪
            
        Returns:
            bool: True 如果重繪成功
        """
        try:
            if not self.has_active_window():
                return False
            
            # 抽象視窗重繪：委派給父插件
            if (self._parent_plugin and 
                hasattr(self._parent_plugin, 'trigger_preview_redraw')):
                return self._parent_plugin.trigger_preview_redraw(use_refresh)
                
            return False
            
        except Exception:
            print(traceback.format_exc())
            return False
    
    # ============================================================================
    # 主要功能方法（純業務邏輯介面）
    # ============================================================================
    
    def start(self):
        """啟動控制器（事件註冊已統一到 plugin.py 層）"""
        try:
            # 控制器初始化完成，事件註冊由 plugin.py 統一管理
            pass
            
        except Exception:
            print(traceback.format_exc())
    
    def update_interface(self, sender):
        """更新介面（純業務邏輯，由視窗層呼叫）"""
        if self.event_handler:
            # 委派給事件處理器
            self.event_handler.update_interface(sender)
    
    def handle_document_opened(self, sender):
        """處理文件開啟事件（DOCUMENTOPENED）- 完整初始化"""
        try:
            # 清除快取（開啟新檔案時清理所有快取）
            clear_all_cache()
            
            # 重新載入偏好設定（新檔案可能需要不同設定）
            self.loadPreferences()
            
            # 委派給事件處理器的文件開啟處理
            if self.event_handler:
                self.event_handler.handle_document_opened(sender)
                
        except Exception:
            print(traceback.format_exc())

    def handle_document_activated(self, sender):
        """處理文件啟動事件（DOCUMENTACTIVATED）- 輕量狀態同步"""
        try:
            # 清除快取（切換檔案時清理舊快取）
            clear_all_cache()
            
            # 委派給事件處理器的文件啟動處理
            if self.event_handler:
                self.event_handler.handle_document_activated(sender)
                
        except Exception:
            print(traceback.format_exc())
    
    def handle_document_will_close(self, sender):
        """處理文件即將關閉事件（DOCUMENTWILLCLOSE）- 檢查全關閉狀態"""
        try:
            # 委派給事件處理器的文件關閉處理
            if self.event_handler:
                self.event_handler.handle_document_will_close(sender)
                
        except Exception:
            print(traceback.format_exc())
    
    # ============================================================================
    # 中央格同步機制（對外介面）
    # ============================================================================
    
    def sync_center_layer_to_preview(self, layer_info=None, selected_glyph=None):
        """同步當前圖層到預覽中央格（對外介面）
        
        Args:
            layer_info: 圖層資訊（與 develop 分支相容）
            selected_glyph: 選中的字符
        """
        try:
            if self.event_handler:
                self.event_handler.sync_center_layer_to_preview(layer_info, selected_glyph)
        except Exception:
            print(traceback.format_exc())
    
    def syncCenterLayerToPreview(self, layer_info=None, selected_glyph=None):
        """camelCase 方法別名，與 develop 分支相容"""
        return self.sync_center_layer_to_preview(layer_info, selected_glyph)
    
    def randomizeAction_(self, sender):
        """隨機排列回呼方法（修復左鍵點擊功能）
        
        由預覽視圖的滑鼠點擊事件呼叫，觸發九宮格的隨機重新排列
        
        Args:
            sender: 發送者（通常是預覽視圖）
        """
        try:
            # 呼叫現有的隨機化邏輯
            self.randomize_grid()
            
            # 更新介面
            self.update_interface(sender)
            
            # 儲存狀態
            self.savePreferences()
            
        except Exception:
            print(traceback.format_exc())