# encoding: utf-8

"""
RandomArrangementService - 隨機排列計算服務
專門處理九宮格字符的隨機排列邏輯，與鎖定功能分離
"""

from __future__ import division, print_function, unicode_literals
import random


class RandomArrangementService(object):
    """隨機排列服務類別
    
    提供各種隨機排列算法，專注於字符陣列操作
    與鎖定邏輯完全分離，保持職責單一
    """
    
    def __init__(self):
        """初始化隨機排列服務"""
        pass
        
    def generate_random_arrangement(self, source_chars, positions, total_slots=9, font=None, master=None):
        """生成隨機排列（使用 font.tempData 快取機制）
        
        Args:
            source_chars (list): 用於填充的可用字符列表
            positions (list): 需要填充的位置索引列表
            total_slots (int): 總位置數量（預設9）
            font: GSFont 物件（用於 tempData 快取）
            master: GSFontMaster 物件（用於生成快取鍵）
            
        Returns:
            list: 完整的字符陣列，未指定位置為 None
        """
        if not source_chars or not positions:
            return [None] * total_slots
        
        # 使用 font.tempData 快取隨機排列結果
        if font and hasattr(font, 'tempData') and master:
            # 生成快取鍵（基於字符集合和位置）
            chars_hash = hash(tuple(sorted(source_chars)))
            positions_hash = hash(tuple(positions))
            cache_key = f"random_arrangement_{master.id}_{chars_hash}_{positions_hash}_{total_slots}"
            
            # 檢查快取
            if cache_key in font.tempData:
                cached_result = font.tempData[cache_key]
                # 驗證快取結果的有效性
                if (isinstance(cached_result, list) and 
                    len(cached_result) == total_slots):
                    return cached_result
                else:
                    # 快取無效，移除
                    del font.tempData[cache_key]
            
        final_arrangement = [None] * total_slots
        num_positions = len(positions)
        
        # 準備填充字符
        chars_for_filling = self.create_non_repeating_batch(source_chars, num_positions)
        
        # 填充指定位置
        for i, pos in enumerate(positions):
            if pos < total_slots and i < len(chars_for_filling):
                final_arrangement[pos] = chars_for_filling[i]
        
        # 快取結果
        if font and hasattr(font, 'tempData') and master:
            font.tempData[cache_key] = final_arrangement[:]
                
        return final_arrangement
        
    def create_non_repeating_batch(self, batch_chars, num_slots):
        """建立非重複批次（從開發版復刻）
        
        根據 batch_chars 和 num_slots 產生一個排列，符合：
        - 多於 num_slots：隨機抽取 num_slots 個不重複字符
        - 等於 num_slots：隨機排列
        - 少於 num_slots：每個字符至少出現一次，剩下的隨機補齊
        
        Args:
            batch_chars (list): 有效字符列表
            num_slots (int): 欲產生的排列長度
            
        Returns:
            list: 長度為 num_slots 的字符列表
        """
        chars = list(batch_chars)
        if not chars or num_slots <= 0:
            return []
            
        if len(chars) >= num_slots:
            # 字符充足：隨機選取不重複字符
            arrangement = random.sample(chars, num_slots)
        else:
            # 字符不足：先全部使用，再隨機補足
            arrangement = chars.copy()
            while len(arrangement) < num_slots:
                arrangement.append(random.choice(chars))
            random.shuffle(arrangement)
            
        return arrangement
        
    def randomize_unlocked_positions(self, current_arrangement, unlocked_positions, source_chars, font=None, master=None):
        """隨機填充未鎖定位置（使用 font.tempData 快取機制）
        
        Args:
            current_arrangement (list): 當前字符陣列
            unlocked_positions (list): 未鎖定位置的索引列表
            source_chars (list): 用於隨機填充的字符列表
            font: GSFont 物件（用於 tempData 快取）
            master: GSFontMaster 物件（用於生成快取鍵）
            
        Returns:
            list: 更新後的字符陣列
        """
        if not unlocked_positions or not source_chars:
            return current_arrangement[:]
        
        # 使用 font.tempData 快取隨機字符批次
        random_chars = None
        if font and hasattr(font, 'tempData') and master:
            # 生成快取鍵
            chars_hash = hash(tuple(sorted(source_chars)))
            positions_count = len(unlocked_positions)
            batch_cache_key = f"random_batch_{master.id}_{chars_hash}_{positions_count}"
            
            # 檢查快取
            if batch_cache_key in font.tempData:
                cached_batch = font.tempData[batch_cache_key]
                if (isinstance(cached_batch, list) and 
                    len(cached_batch) == positions_count):
                    random_chars = cached_batch
        
        # 如果沒有快取，生成新的隨機字符批次
        if random_chars is None:
            random_chars = self.create_non_repeating_batch(source_chars, len(unlocked_positions))
            
            # 快取結果
            if font and hasattr(font, 'tempData') and master:
                font.tempData[batch_cache_key] = random_chars[:]
            
        # 建立結果陣列的副本
        result = current_arrangement[:]
        
        # 填充未鎖定位置
        for i, pos in enumerate(unlocked_positions):
            if i < len(random_chars):
                result[pos] = random_chars[i]
                
        return result
        
    def generate_arrangement_with_duplicates(self, source_chars, positions, allow_duplicates=True):
        """生成允許重複的排列（擴充版本）
        
        Args:
            source_chars (list): 源字符列表
            positions (list): 需要填充的位置
            allow_duplicates (bool): 是否允許重複
            
        Returns:
            list: 填充字符列表
        """
        if not source_chars or not positions:
            return []
            
        if allow_duplicates:
            # 允許重複：每個位置隨機選擇
            return [random.choice(source_chars) for _ in positions]
        else:
            # 不允許重複：使用非重複批次方法
            return self.create_non_repeating_batch(source_chars, len(positions))
            
    def shuffle_existing_arrangement(self, arrangement, positions_to_shuffle):
        """打亂現有排列的指定位置
        
        Args:
            arrangement (list): 當前排列
            positions_to_shuffle (list): 需要打亂的位置索引
            
        Returns:
            list: 打亂後的排列
        """
        if not arrangement or not positions_to_shuffle:
            return arrangement[:]
            
        result = arrangement[:]
        
        # 提取指定位置的字符
        chars_to_shuffle = [result[pos] for pos in positions_to_shuffle if pos < len(result) and result[pos] is not None]
        
        if chars_to_shuffle:
            # 隨機打亂
            random.shuffle(chars_to_shuffle)
            
            # 重新分配到位置
            char_iter = iter(chars_to_shuffle)
            for pos in positions_to_shuffle:
                if pos < len(result) and result[pos] is not None:
                    try:
                        result[pos] = next(char_iter)
                    except StopIteration:
                        break
                        
        return result
        
    def simple_random_arrangement(self, positions, source_chars):
        """簡單隨機排列（原 GridManager 復原邏輯）
        
        統一所有簡單隨機邏輯到此處，消除重複實作
        
        Args:
            positions (list): 需要填充的位置索引列表
            source_chars (list): 用於隨機選擇的字符列表
            
        Returns:
            list: 隨機字符列表，對應於 positions
        """
        if not positions or not source_chars:
            return []
        
        return [random.choice(source_chars) for _ in range(len(positions))]


# 全域服務實例
_random_service = RandomArrangementService()


def get_random_service():
    """獲取隨機排列服務實例
    
    Returns:
        RandomArrangementService: 服務實例
    """
    return _random_service


# 便利函數（向後相容且支援 tempData 快取）
def generate_random_arrangement(source_chars, positions, total_slots=9, font=None, master=None):
    """生成隨機排列（便利函數）"""
    return _random_service.generate_random_arrangement(source_chars, positions, total_slots, font, master)


def create_non_repeating_batch(batch_chars, num_slots):
    """建立非重複批次（便利函數）"""
    return _random_service.create_non_repeating_batch(batch_chars, num_slots)


def randomize_unlocked_positions(current_arrangement, unlocked_positions, source_chars, font=None, master=None):
    """隨機填充未鎖定位置（便利函數）"""
    return _random_service.randomize_unlocked_positions(current_arrangement, unlocked_positions, source_chars, font, master)


def simple_random_arrangement(positions, source_chars):
    """簡單隨機排列（便利函數）"""
    return _random_service.simple_random_arrangement(positions, source_chars)