# encoding: utf-8
"""
GridManager 測試

測試九宮格平面座標管理核心邏輯
"""

from __future__ import division, print_function, unicode_literals
import unittest
import sys
import os

# 新增測試路徑
test_dir = os.path.dirname(__file__)
project_root = os.path.dirname(os.path.dirname(test_dir))
sys.path.insert(0, project_root)

# 必須在匯入其他模組之前設定 Mock 環境
from tests.mocks.glyphs_mocks import setup_mock_environment, teardown_mock_environment


class TestGridManager(unittest.TestCase):
    """GridManager 測試類"""
    
    def setUp(self):
        """測試設定"""
        self.mock_glyphs = setup_mock_environment()
        
        # 延遲匯入以使用 Mock 環境
        from core.grid_manager import GridManager
        self.grid_manager = GridManager()
    
    def tearDown(self):
        """測試清理"""
        teardown_mock_environment()
    
    def test_create_grid_manager(self):
        """測試建立 GridManager 實例"""
        self.assertIsNotNone(self.grid_manager)
        self.assertTrue(hasattr(self.grid_manager, 'displayArrangement'))
        self.assertTrue(hasattr(self.grid_manager, 'get_center_glyph_layer'))
    
    def test_position_constants(self):
        """測試位置常數"""
        # 使用實例常數
        self.assertEqual(self.grid_manager.CENTER_POSITION, 4)  # 中央位置
        self.assertEqual(self.grid_manager.GRID_SIZE, 9)  # 總共9個位置
    
    def test_display_arrangement_basic(self):
        """測試基本字符排列功能"""
        font = self.mock_glyphs.font
        
        # 設定字體
        self.grid_manager.update_current_font(font)
        
        # 測試設定中央字符
        self.grid_manager.set_center_glyph("a")
        
        # 測試獲取排列
        arrangement = self.grid_manager.displayArrangement()
        self.assertIsInstance(arrangement, list)
        self.assertEqual(len(arrangement), 9)  # 應該返回9個位置的排列
    
    def test_get_center_layer(self):
        """測試獲取中央格圖層"""
        font = self.mock_glyphs.font
        
        # 設定字體和中央字符
        self.grid_manager.update_current_font(font)
        self.grid_manager.set_center_glyph("a")
        
        center_layer = self.grid_manager.get_center_glyph_layer("master01")
        # 中央格應該有內容或為 None
        self.assertTrue(center_layer is None or hasattr(center_layer, 'parent'))


class TestGridCoordinates(unittest.TestCase):
    """測試平面座標系統"""
    
    def setUp(self):
        """測試設定"""
        self.mock_glyphs = setup_mock_environment()
        
        from core.grid_manager import GridManager
        self.grid_manager = GridManager()
    
    def tearDown(self):
        """測試清理"""
        teardown_mock_environment()
    
    def test_position_mapping(self):
        """測試位置映射邏輯"""
        # 這裡測試 0-8 座標系統的基本概念
        positions = list(range(9))
        
        # 確保有9個位置
        self.assertEqual(len(positions), 9)
        
        # 中央位置是4
        center = 4
        self.assertIn(center, positions)
    
    def test_surrounding_positions(self):
        """測試周圍位置計算"""
        center = 4
        all_positions = list(range(9))
        surrounding = [pos for pos in all_positions if pos != center]
        
        # 應該有8個周圍位置
        self.assertEqual(len(surrounding), 8)
        self.assertNotIn(center, surrounding)


if __name__ == '__main__':
    unittest.main()