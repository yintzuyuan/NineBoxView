# encoding: utf-8

"""
九宮格預覽外掛 - 偏好設定管理器
基於原版 preferences 的完整復刻，適配平面座標系統
"""

from __future__ import division, print_function, unicode_literals
import objc
from GlyphsApp import Glyphs
from Foundation import NSUserDefaults

# 平面座標系統常數
GRID_SIZE = 9  # 0-8 座標
CENTER_POSITION = 4  # 中央位置

class PreferencesManager:
    """偏好設定管理器 - 基於原版架構的完整復刻"""
    
    def __init__(self, plugin_id="com.YinTzuYuan.NineBoxView"):
        """初始化偏好設定管理器"""
        self.plugin_id = plugin_id
        self.user_defaults = NSUserDefaults.standardUserDefaults()
    
    def _make_key(self, key):
        """生成完整的偏好設定鍵值"""
        return f"{self.plugin_id}.{key}"
    
    def get_string(self, key, default=""):
        """取得字串偏好設定"""
        full_key = self._make_key(key)
        value = self.user_defaults.objectForKey_(full_key)
        if value is None:
            return default
        return str(value)
    
    def set_string(self, key, value):
        """設定字串偏好設定"""
        full_key = self._make_key(key)
        self.user_defaults.setObject_forKey_(value or "", full_key)
        self.user_defaults.synchronize()
    
    def get_bool(self, key, default=False):
        """取得布林偏好設定"""
        full_key = self._make_key(key)
        if self.user_defaults.objectForKey_(full_key) is None:
            return default
        return bool(self.user_defaults.boolForKey_(full_key))
    
    def set_bool(self, key, value):
        """設定布林偏好設定"""
        full_key = self._make_key(key)
        self.user_defaults.setBool_forKey_(bool(value), full_key)
        self.user_defaults.synchronize()
    
    def get_array(self, key, default=None):
        """取得陣列偏好設定（平面座標系統適配）"""
        if default is None:
            default = [''] * GRID_SIZE  # 0-8 位置的空字串
        
        full_key = self._make_key(key)
        value = self.user_defaults.objectForKey_(full_key)
        if value is None:
            return default[:]
        
        # 確保陣列長度正確
        result = list(value)
        while len(result) < GRID_SIZE:
            result.append('')
        
        return result[:GRID_SIZE]  # 限制為9個元素
    
    def set_array(self, key, value):
        """設定陣列偏好設定（平面座標系統適配）"""
        if not isinstance(value, (list, tuple)):
            value = [''] * GRID_SIZE
        
        # 確保陣列長度為9
        array_value = list(value)[:GRID_SIZE]
        while len(array_value) < GRID_SIZE:
            array_value.append('')
        
        full_key = self._make_key(key)
        self.user_defaults.setObject_forKey_(array_value, full_key)
        self.user_defaults.synchronize()
    
    def get_dict(self, key, default=None):
        """取得字典偏好設定（用於鎖定位置）"""
        if default is None:
            default = {}
        
        full_key = self._make_key(key)
        value = self.user_defaults.objectForKey_(full_key)
        if value is None:
            return default.copy()
        
        return dict(value)
    
    def set_dict(self, key, value):
        """設定字典偏好設定（用於鎖定位置）"""
        if not isinstance(value, dict):
            value = {}
        
        full_key = self._make_key(key)
        self.user_defaults.setObject_forKey_(value, full_key)
        self.user_defaults.synchronize()
    
    def get_float(self, key, default=0.0):
        """取得浮點數偏好設定"""
        full_key = self._make_key(key)
        if self.user_defaults.objectForKey_(full_key) is None:
            return default
        return float(self.user_defaults.floatForKey_(full_key))
    
    def set_float(self, key, value):
        """設定浮點數偏好設定"""
        full_key = self._make_key(key)
        self.user_defaults.setFloat_forKey_(float(value), full_key)
        self.user_defaults.synchronize()
    
    def get_int(self, key, default=0):
        """取得整數偏好設定"""
        full_key = self._make_key(key)
        if self.user_defaults.objectForKey_(full_key) is None:
            return default
        return int(self.user_defaults.integerForKey_(full_key))
    
    def set_int(self, key, value):
        """設定整數偏好設定"""
        full_key = self._make_key(key)
        self.user_defaults.setInteger_forKey_(int(value), full_key)
        self.user_defaults.synchronize()
    
    def get_size(self, key, default=(0, 0)):
        """取得尺寸偏好設定 (width, height)"""
        size_str = self.get_string(key, "")
        if not size_str:
            return default
        
        try:
            parts = size_str.split(',')
            if len(parts) == 2:
                return (float(parts[0]), float(parts[1]))
        except (ValueError, IndexError):
            pass
        
        return default
    
    def set_size(self, key, value):
        """設定尺寸偏好設定 (width, height)"""
        if isinstance(value, (list, tuple)) and len(value) == 2:
            size_str = f"{float(value[0])},{float(value[1])}"
            self.set_string(key, size_str)
        else:
            self.set_string(key, "0,0")
    
    def get_point(self, key, default=None):
        """取得座標點偏好設定 (x, y)"""
        point_str = self.get_string(key, "")
        if not point_str:
            return default
        
        try:
            parts = point_str.split(',')
            if len(parts) == 2:
                return (float(parts[0]), float(parts[1]))
        except (ValueError, IndexError):
            pass
        
        return default
    
    def set_point(self, key, value):
        """設定座標點偏好設定 (x, y)"""
        if value is None:
            self.set_string(key, "")
        elif isinstance(value, (list, tuple)) and len(value) == 2:
            point_str = f"{float(value[0])},{float(value[1])}"
            self.set_string(key, point_str)
        else:
            self.set_string(key, "")
    
    def get_grid(self, key, default=None):
        """取得網格陣列偏好設定（別名為 get_array）"""
        return self.get_array(key, default)
    
    def set_grid(self, key, value):
        """設定網格陣列偏好設定（別名為 set_array）"""
        self.set_array(key, value)
    
    def remove_key(self, key):
        """移除偏好設定鍵值"""
        full_key = self._make_key(key)
        self.user_defaults.removeObjectForKey_(full_key)
        self.user_defaults.synchronize()
    
    def clear_all(self):
        """清除所有相關的偏好設定"""
        # 取得所有鍵值
        all_keys = self.user_defaults.dictionaryRepresentation().allKeys()
        prefix = f"{self.plugin_id}."
        
        # 移除以外掛ID為前綴的所有鍵值
        for key in all_keys:
            if str(key).startswith(prefix):
                self.user_defaults.removeObjectForKey_(key)
        
        self.user_defaults.synchronize()
    
    def export_preferences(self):
        """匯出偏好設定（用於除錯）"""
        all_prefs = self.user_defaults.dictionaryRepresentation()
        prefix = f"{self.plugin_id}."
        
        plugin_prefs = {}
        for key in all_prefs:
            if str(key).startswith(prefix):
                short_key = str(key)[len(prefix):]
                plugin_prefs[short_key] = all_prefs[key]
        
        return plugin_prefs
    
    def has_key(self, key):
        """檢查偏好設定鍵值是否存在"""
        full_key = self._make_key(key)
        return self.user_defaults.objectForKey_(full_key) is not None
    
    def save(self):
        """儲存偏好設定（向後相容方法）
        
        注意：所有 set_* 方法已自動呼叫 synchronize()，
        此方法主要用於向後相容性。
        """
        self.user_defaults.synchronize()

# 便利函數 - 全域偏好設定管理器實例
_global_manager = None

def get_preferences_manager():
    """取得全域偏好設定管理器實例"""
    global _global_manager
    if _global_manager is None:
        _global_manager = PreferencesManager()
    return _global_manager

def reset_preferences_manager():
    """重置全域偏好設定管理器（主要用於測試）"""
    global _global_manager
    _global_manager = None