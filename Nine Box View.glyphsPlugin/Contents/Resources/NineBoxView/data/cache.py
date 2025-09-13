# encoding: utf-8

"""
Cache System - 九宮格預覽的輕量化快取系統
整合官方 API 最佳實踐，專注於核心創新功能
"""

from __future__ import division, print_function, unicode_literals
import traceback


# 全域快取儲存（僅保留核心功能）
_failed_glyph_cache = {}  # 失敗尋找快取：避免重複嘗試無效字符
_width_change_cache = {}  # 寬度變更偵測快取：{layer_id: last_width}
_cache_stats = {   # 快取統計
    'glyph_queries': 0,
    'glyph_failures': 0,
    'width_checks': 0,
    'width_changes': 0
}


def get_glyph_with_fallback(font, char_name, master=None):
    """
    多方式字符尋找函數（使用 tempData 快取機制）
    
    Args:
        font: GSFont 物件
        char_name (str): 字符名稱或單字符
        master: GSFontMaster 物件（用於 tempData 快取）
        
    Returns:
        GSGlyph or None: 找到的字符物件
    """
    global _cache_stats
    
    if not font or not font.glyphs or not char_name:
        return None
    
    try:
        # 使用 font.tempData 作為快取載體
        cache_key = f"glyph_cache_{master.id}_{char_name}" if master else f"glyph_cache_{char_name}"
        
        # 檢查 tempData 快取
        if font and hasattr(font, 'tempData'):
            if cache_key in font.tempData:
                cached_result = font.tempData[cache_key]
                if cached_result == 'NOT_FOUND':
                    return None
                # 驗證快取的字符仍然存在
                if cached_result in font.glyphs:
                    return font.glyphs[cached_result]
                else:
                    # 快取失效，移除過時項目
                    del font.tempData[cache_key]
            
        _cache_stats['glyph_queries'] += 1
        glyph = None
        
        # 方法1：直接按名稱尋找（使用官方優化的字典存取）
        try:
            glyph = font.glyphs[char_name]
            if glyph:
                # 快取成功結果
                if font and hasattr(font, 'tempData'):
                    font.tempData[cache_key] = glyph.name
                return glyph
        except (KeyError, IndexError):
            pass
            
        # 方法2：Unicode 尋找（使用官方 API）
        if len(char_name) == 1:
            try:
                unicode_value = ord(char_name)
                glyph = font.glyphForUnicode_(unicode_value)
                if glyph:
                    # 快取成功結果
                    if font and hasattr(font, 'tempData'):
                        font.tempData[cache_key] = glyph.name
                    return glyph
            except (AttributeError, ValueError):
                pass
                
        # 方法3：Unicode 名稱尋找（如 'A' -> 'uni0041'）
        if len(char_name) == 1:
            try:
                unicode_name = f"uni{ord(char_name):04X}"
                glyph = font.glyphs[unicode_name]
                if glyph:
                    # 快取成功結果
                    if font and hasattr(font, 'tempData'):
                        font.tempData[cache_key] = glyph.name
                    return glyph
            except (KeyError, IndexError, ValueError, OverflowError):
                pass
        
        # 所有方法都失敗，快取失敗結果
        if font and hasattr(font, 'tempData'):
            font.tempData[cache_key] = 'NOT_FOUND'
        _cache_stats['glyph_failures'] += 1
        return None
        
    except Exception:
        print(traceback.format_exc())
        return None


def use_performance_api(font, layer_operations_func):
    """
    使用官方效能 API 執行批次操作
    
    Args:
        font: GSFont 物件
        layer_operations_func: 要執行的圖層操作函數
        
    Returns:
        函數執行結果
    """
    if not font:
        return layer_operations_func() if layer_operations_func else None
        
    try:
        # 使用官方 API 禁用介面更新提升效能
        font.disableUpdateInterface()
        return layer_operations_func() if layer_operations_func else None
    except Exception:
        print(traceback.format_exc())
        return layer_operations_func() if layer_operations_func else None
    finally:
        try:
            font.enableUpdateInterface()
        except:
            pass


def detect_width_change_with_tempdata(layer, font=None, master=None):
    """
    偵測圖層寬度是否發生變化（使用 font.tempData 快取機制）
    
    Args:
        layer: GSLayer 物件
        font: GSFont 物件（用於 tempData 快取）
        master: GSFontMaster 物件（用於生成快取鍵）
        
    Returns:
        bool: True 如果寬度有變化
    """
    global _cache_stats
    
    if not layer:
        return False
        
    try:
        current_width = layer.width
        _cache_stats['width_checks'] += 1
        
        # 使用 font.tempData 作為快取載體
        if font and hasattr(font, 'tempData') and master:
            layer_key = f"width_cache_{master.id}_{layer.layerId}" if hasattr(layer, 'layerId') else f"width_cache_{master.id}_{id(layer)}"
            
            # 檢查快取的寬度
            cached_width = font.tempData.get(layer_key)
            
            # 更新快取
            font.tempData[layer_key] = current_width
            
            # 檢查是否有變化
            if cached_width is not None and cached_width != current_width:
                _cache_stats['width_changes'] += 1
                return True
        else:
            # 復原到全域快取
            layer_id = layer.layerId if hasattr(layer, 'layerId') else id(layer)
            cached_width = _width_change_cache.get(layer_id)
            _width_change_cache[layer_id] = current_width
            
            if cached_width is not None and cached_width != current_width:
                _cache_stats['width_changes'] += 1
                return True
            
        return False
        
    except Exception:
        print(traceback.format_exc())
        return False

# 保留舊的介面以向後相容
def detect_width_change(layer, font=None):
    """向後相容的寬度偵測介面"""
    return detect_width_change_with_tempdata(layer, font)


def detect_multiple_width_changes(layers):
    """
    批次偵測多個圖層的寬度變化
    
    Args:
        layers (list): GSLayer 物件列表
        
    Returns:
        bool: True 如果任何圖層寬度有變化
    """
    if not layers:
        return False
        
    has_change = False
    for layer in layers:
        if layer and detect_width_change(layer):
            has_change = True
            
    return has_change


def clear_failed_glyph_cache():
    """清除失敗字符尋找快取"""
    global _failed_glyph_cache
    _failed_glyph_cache.clear()


def clear_width_change_cache():
    """清除寬度變更偵測快取"""
    global _width_change_cache
    _width_change_cache.clear()


def clear_all_cache():
    """清除所有快取"""
    clear_failed_glyph_cache()
    clear_width_change_cache()


def get_cache_stats():
    """
    取得快取統計資訊
    
    Returns:
        dict: 快取統計字典
    """
    global _cache_stats
    return _cache_stats.copy()


def reset_cache_stats():
    """重置快取統計"""
    global _cache_stats
    _cache_stats = {
        'glyph_queries': 0,
        'glyph_failures': 0,
        'width_checks': 0,
        'width_changes': 0
    }


def optimize_cache():
    """
    優化快取：清理過大的快取項目
    """
    global _failed_glyph_cache, _width_change_cache
    
    try:
        # 限制失敗尋找快取大小
        max_failed_cache_size = 200
        if len(_failed_glyph_cache) > max_failed_cache_size:
            # 清除一半舊項目
            items = list(_failed_glyph_cache.items())
            _failed_glyph_cache.clear()
            _failed_glyph_cache.update(items[len(items)//2:])
            
        # 限制寬度變更偵測快取大小
        max_width_cache_size = 300
        if len(_width_change_cache) > max_width_cache_size:
            items = list(_width_change_cache.items())
            _width_change_cache.clear()
            _width_change_cache.update(items[len(items)//2:])
            
    except Exception:
        print(traceback.format_exc())


def create_width_change_detector():
    """
    建立寬度變更偵測器（使用 tempData 快取機制）
    
    Returns:
        function: 偵測器函數
    """
    def detector(font, arrangement, current_master):
        """
        寬度變更偵測器函數（整合 tempData 快取）
        
        Args:
            font: 當前字型
            arrangement (list): 字符排列
            current_master: 當前主版
            
        Returns:
            bool: True 如果偵測到寬度變更
        """
        if not font or not arrangement or not current_master:
            return False
            
        width_changed = False
        
        try:
            # 檢查選中的圖層（中央格）
            if font.selectedLayers:
                center_layer = font.selectedLayers[0]
                if center_layer and detect_width_change_with_tempdata(center_layer, font, current_master):
                    width_changed = True
            
            # 檢查排列中所有字符的寬度（使用 tempData 快取）
            for char in arrangement:
                if char is not None and char != '':
                    glyph = get_glyph_with_fallback(font, char, current_master)
                    if glyph and current_master.id in glyph.layers:
                        layer = glyph.layers[current_master.id]
                        if detect_width_change_with_tempdata(layer, font, current_master):
                            width_changed = True
            
            return width_changed
            
        except Exception:
            print(traceback.format_exc())
            return False
    
    return detector
