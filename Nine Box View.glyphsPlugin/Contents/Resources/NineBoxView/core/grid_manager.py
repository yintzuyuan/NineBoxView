# encoding: utf-8

"""
GridManager - 九宮格平面座標管理
採用直觀的 0-8 座標系統，避免複雜的三層架構
"""

from __future__ import division, print_function, unicode_literals
# 使用絕對匯入避免測試環境問題
try:
    # 在正常執行環境中使用相對匯入
    from ..data.cache import get_glyph_with_fallback, create_width_change_detector
    from .random_arrangement import get_random_service
except (ImportError, ValueError):
    # 在測試環境中使用絕對匯入
    from data.cache import get_glyph_with_fallback, create_width_change_detector
    from core.random_arrangement import get_random_service
import traceback

class GridManager(object):
    """九宮格平面座標管理器
    
    座標系統：
    0 | 1 | 2
    ---------
    3 | 4 | 5  ← 位置4為中心格
    ---------
    6 | 7 | 8
    """
    
    # 常數定義
    GRID_SIZE = 9
    CENTER_POSITION = 4
    
    def __init__(self):
        """初始化網格管理器（整合進階重繪支援）"""
        # 九宮格字符陣列（0-8位置）
        self.grid_glyphs = [''] * self.GRID_SIZE
        
        # 鎖定狀態陣列
        self.locked_positions = [False] * self.GRID_SIZE
        
        # 當前選中字符序列
        self.selected_chars = []
        
        # 當前字體參考
        self.current_font = None
        
        # 進階重繪支援：寬度偵測器初始化
        self._width_detector = create_width_change_detector()
        
        self._last_arrangement = None
        
    # === 基本座標操作 ===
    
    def set_glyph_at_position(self, position, glyph_name):
        """設定指定位置的字符
        
        Args:
            position (int): 位置索引 (0-8)
            glyph_name (str): 字符名稱
        """
        if 0 <= position < self.GRID_SIZE:
            self.grid_glyphs[position] = glyph_name or ''
            
    def get_glyph_at_position(self, position):
        """獲取指定位置的字符
        
        Args:
            position (int): 位置索引 (0-8)
            
        Returns:
            str: 字符名稱
        """
        if 0 <= position < self.GRID_SIZE:
            return self.grid_glyphs[position]
        return ''
        
    def displayArrangement(self):
        """獲取當前顯示排列
        
        Returns:
            list: 長度為9的字符陣列
        """
        return self.grid_glyphs[:]
        
    # === 鎖定功能 ===
    
    def toggle_lock_at_position(self, position):
        """切換指定位置的鎖定狀態
        
        Args:
            position (int): 位置索引 (0-8)
            
        Returns:
            bool: 切換後的鎖定狀態
        """
        if 0 <= position < self.GRID_SIZE:
            self.locked_positions[position] = not self.locked_positions[position]
            return self.locked_positions[position]
        return False
        
    def is_position_locked(self, position):
        """檢查位置是否被鎖定
        
        Args:
            position (int): 位置索引 (0-8)
            
        Returns:
            bool: 是否鎖定
        """
        if 0 <= position < self.GRID_SIZE:
            return self.locked_positions[position]
        return False
        
    def get_unlocked_positions(self):
        """獲取所有未鎖定的位置
        
        Returns:
            list: 未鎖定位置的索引列表
        """
        return [i for i in range(self.GRID_SIZE) if not self.locked_positions[i]]
        
    def clear_unlocked_positions(self):
        """清空所有未鎖定位置的字符"""
        for i in range(self.GRID_SIZE):
            if not self.locked_positions[i]:
                self.grid_glyphs[i] = ''
                
    # === 中心格管理 ===
    
    def set_center_glyph(self, glyph_name):
        """設定中心格字符（位置4）
        
        Args:
            glyph_name (str): 字符名稱
        """
        self.set_glyph_at_position(self.CENTER_POSITION, glyph_name)
        
    def get_center_glyph(self):
        """獲取中心格字符
        
        Returns:
            str: 中心格字符名稱
        """
        return self.get_glyph_at_position(self.CENTER_POSITION)
        
    
    def get_center_glyph_layer(self, font=None):
        """獲取中心格字符的進階圖層（採用官方模式統一上下文）
        
        Args:
            font: 當前字型（可選，已統一到內部上下文獲取）
            
        Returns:
            GSLayer or None: 中心格字符的圖層
        """
        try:
            char_or_name = self.get_center_glyph()
            if not char_or_name:
                return None
                
            # 使用統一的字型上下文獲取
            from .utils import FontManager
            context_font, master = FontManager.getCurrentFontContext()
            current_font = font or context_font  # 支援傳入參數，優先使用統一上下文
            
            if current_font and master and get_glyph_with_fallback:
                glyph = get_glyph_with_fallback(current_font, char_or_name, master)
                if glyph:
                    return glyph.layers[master.id]
            
            return None
            
        except Exception:
            print(traceback.format_exc())
            return None
        
    # === 智慧填充功能 ===
    
    def auto_fill_from_selected_chars(self, selected_chars=None):
        """根據選中字符序列隨機填充未鎖定位置（統一使用隨機排列服務）
        
        Args:
            selected_chars (list, optional): 字符序列，預設使用內部儲存的序列
            
        Returns:
            bool: True 如果排列有變化
        """
        old_arrangement = self.grid_glyphs[:]
        
        if selected_chars is not None:
            self.selected_chars = selected_chars[:]
            
        if not self.selected_chars:
            # 沒有選中字符時清空未鎖定位置
            self.clear_unlocked_positions()
        else:
            # 統一使用隨機排列服務填充未鎖定位置
            unlocked = self.get_unlocked_positions()
            if unlocked:
                # 使用隨機服務生成字符排列（傳遞 font 和 master 用於快取）
                from .utils import FontManager
                context_font, master = FontManager.getCurrentFontContext()
                random_service = get_random_service()
                new_arrangement = random_service.randomize_unlocked_positions(
                    self.grid_glyphs, unlocked, self.selected_chars, context_font, master
                )
                self.grid_glyphs = new_arrangement
        
        # 檢查排列是否有變化
        return old_arrangement != self.grid_glyphs
            
    def set_surrounding_pattern(self, pattern_chars):
        """設定周圍格（非中心格）的字符模式
        
        Args:
            pattern_chars (list): 8個字符的列表，對應位置 0,1,2,3,5,6,7,8
        """
        if len(pattern_chars) != 8:
            return
            
        positions = [0, 1, 2, 3, 5, 6, 7, 8]  # 排除中心位置4
        for i, pos in enumerate(positions):
            if not self.is_position_locked(pos):
                self.set_glyph_at_position(pos, pattern_chars[i])
                
    def randomize_positions(self, positions, source_chars):
        """隨機填充指定位置（統一使用隨機排列服務）
        
        Args:
            positions (list): 需要隨機填充的位置索引列表
            source_chars (list): 用於填充的字符列表
            
        Returns:
            bool: True 如果有變化
        """
        if not positions or not source_chars:
            return False
            
        old_arrangement = self.grid_glyphs[:]
        
        # 統一使用隨機服務（移除復原邏輯，傳遞 font 和 master 用於快取）
        from .utils import FontManager
        context_font, master = FontManager.getCurrentFontContext()
        random_service = get_random_service()
        new_arrangement = random_service.randomize_unlocked_positions(
            self.grid_glyphs, positions, source_chars, context_font, master
        )
        self.grid_glyphs = new_arrangement
                    
        return old_arrangement != self.grid_glyphs
        
    def randomize_surrounding_positions(self, source_chars):
        """隨機填充周圍位置（排除中心格和鎖定位置）
        
        Args:
            source_chars (list): 用於填充的字符列表
            
        Returns:
            bool: True 如果有變化
        """
        surrounding_positions = [0, 1, 2, 3, 5, 6, 7, 8]  # 排除中心位置4
        unlocked_surrounding = [pos for pos in surrounding_positions 
                               if not self.is_position_locked(pos)]
        return self.randomize_positions(unlocked_surrounding, source_chars)
                
    # === 座標轉換工具 ===
    
    @staticmethod
    def position_to_coordinates(position):
        """將位置索引轉換為二維座標
        
        Args:
            position (int): 位置索引 (0-8)
            
        Returns:
            tuple: (row, col) 座標 (0-2, 0-2)
        """
        if 0 <= position < 9:
                return (position // 3, position % 3)
        return (0, 0)
        
    @staticmethod
    def coordinates_to_position(row, col):
        """將二維座標轉換為位置索引
        
        Args:
            row (int): 行座標 (0-2)
            col (int): 列座標 (0-2)
            
        Returns:
            int: 位置索引 (0-8)
        """
        if 0 <= row < 3 and 0 <= col < 3:
                return row * 3 + col
        return 0
        return 0
        
    # === 狀態管理 ===
    
    def reset_all(self):
        """重置所有狀態"""
        self.grid_glyphs = [''] * self.GRID_SIZE
        self.locked_positions = [False] * self.GRID_SIZE
        self.selected_chars = []
        
    def get_state_dict(self):
        """獲取當前狀態字典（用於儲存/載入）
        
        Returns:
            dict: 包含所有狀態的字典
        """
        return {
            'grid_glyphs': self.grid_glyphs[:],
            'locked_positions': self.locked_positions[:],
            'selected_chars': self.selected_chars[:]
        }
        
    def load_state_dict(self, state_dict):
        """載入狀態字典
        
        Args:
            state_dict (dict): 狀態字典
            
        Returns:
            bool: True 如果狀態有變化
        """
        old_state = self.get_state_dict()
        
        if 'grid_glyphs' in state_dict and len(state_dict['grid_glyphs']) == self.GRID_SIZE:
            self.grid_glyphs = state_dict['grid_glyphs'][:]
            
        if 'locked_positions' in state_dict and len(state_dict['locked_positions']) == self.GRID_SIZE:
            self.locked_positions = state_dict['locked_positions'][:]
            
        if 'selected_chars' in state_dict:
            self.selected_chars = state_dict['selected_chars'][:] if state_dict['selected_chars'] else []
        
        # 檢查狀態是否有變化
        return old_state != self.get_state_dict()
        
    # === 進階重繪支援方法 ===
    
    def detect_width_changes(self, font=None):
        """偵測當前排列的字符寬度變化（採用官方模式統一上下文）
        
        Args:
            font: 當前字型（可選，已統一到內部上下文獲取）
            
        Returns:
            bool: True 如果偵測到寬度變化
        """
        try:
            # 使用統一的字型上下文獲取
            from .utils import FontManager
            context_font, master = FontManager.getCurrentFontContext()
            current_font = font or context_font  # 支援傳入參數，優先使用統一上下文
            
            if not current_font or not master:
                return False
            
            # 使用寬度變更偵測器
            if self._width_detector:
                result = self._width_detector(
                    current_font, 
                    self.grid_glyphs, 
                    master
                )
                return result
            else:
                return False
            
        except Exception:
            print(traceback.format_exc())
            return False
    
    def has_arrangement_changed(self):
        """檢查排列是否從上次檢查後發生變化
        
        Returns:
            bool: True 如果排列有變化
        """
        current = self.grid_glyphs[:]
        if self._last_arrangement != current:
            self._last_arrangement = current[:]
            return True
        return False
        
    def update_current_font(self, font):
        """更新當前字型參考
        
        Args:
            font: 新的字型
            
        Returns:
            bool: True 如果字型有變化
        """
        if self.current_font != font:
            self.current_font = font
            return True
        return False