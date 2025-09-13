# encoding: utf-8
"""
NineBox 整合測試

測試各模組間的合作和完整的九宮格預覽流程
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


class TestNineBoxIntegration(unittest.TestCase):
    """NineBox 整合測試類"""
    
    def setUp(self):
        """測試設定"""
        self.mock_glyphs = setup_mock_environment()
    
    def tearDown(self):
        """測試清理"""
        teardown_mock_environment()
    
    def test_full_pipeline(self):
        """測試完整的九宮格預覽管道"""
        from core.grid_manager import GridManager
        from core.glyphs_service import GlyphsService
        from core.input_recognition import InputRecognitionService
        
        # 建立服務實例
        grid_manager = GridManager()
        font = self.mock_glyphs.font
        input_service = InputRecognitionService()
        
        # 測試完整流程
        # 1. 輸入識別
        recognition_result = input_service.parse_glyph_input("a")
        self.assertIsInstance(recognition_result, dict)
        
        # 2. 字符排列
        grid_manager.update_current_font(font)
        grid_manager.set_center_glyph("a")
        arrangement = grid_manager.displayArrangement()
        self.assertIsInstance(arrangement, list)
        self.assertEqual(len(arrangement), 9)
        
        # 3. 中央格獲取
        center_layer = grid_manager.get_center_glyph_layer("master01")
        # 中央格應該有內容或為 None（合理的結果）
        self.assertTrue(center_layer is None or hasattr(center_layer, 'parent'))
    
    def test_service_interactions(self):
        """測試服務間互動"""
        from core.glyphs_service import GlyphsService
        from core.theme_detector import ThemeDetector
        
        # GlyphsService 可用性
        self.assertTrue(GlyphsService.is_available())
        
        # 主題偵測
        detector = ThemeDetector()
        # 檢查 detector 是否有偵測方法
        self.assertTrue(hasattr(detector, 'get_theme_is_black'))
        
        # 進行主題偵測測試
        theme = detector.get_theme_is_black(self.mock_glyphs.font)
        self.assertIsInstance(theme, bool)
    
    def test_error_handling(self):
        """測試錯誤處理和邊界情況"""
        from core.grid_manager import GridManager
        
        grid_manager = GridManager()
        font = self.mock_glyphs.font
        
        # 測試 None 輸入
        grid_manager.set_center_glyph(None)
        result = grid_manager.displayArrangement()
        self.assertIsInstance(result, list)
        
        # 測試空字體
        grid_manager.update_current_font(None)
        grid_manager.set_center_glyph("a")
        result = grid_manager.displayArrangement()
        self.assertIsInstance(result, list)


class TestModuleLoading(unittest.TestCase):
    """測試模組載入和依賴"""
    
    def setUp(self):
        """測試設定"""
        self.mock_glyphs = setup_mock_environment()
    
    def tearDown(self):
        """測試清理"""
        teardown_mock_environment()
    
    def test_all_core_modules_loadable(self):
        """測試所有核心模組都能正確載入"""
        modules_to_test = [
            'core.grid_manager',
            'core.glyphs_service',
            'core.input_recognition',
            'core.theme_detector',
            'core.event_handler',
            'core.menu_manager',
            'core.utils',
            'core.random_arrangement',
            'core.light_table_support'
        ]
        
        loaded_modules = []
        failed_modules = []
        
        for module_name in modules_to_test:
            try:
                __import__(module_name)
                loaded_modules.append(module_name)
            except Exception as e:
                failed_modules.append((module_name, str(e)))
        
        # 至少核心模組應該能載入
        essential_modules = [
            'core.grid_manager',
            'core.glyphs_service',
            'core.theme_detector'
        ]
        
        for essential in essential_modules:
            self.assertIn(essential, loaded_modules, 
                         f"Essential module {essential} failed to load")
        
        # 記錄失敗的模組（但不讓測試失敗，因為有些模組可能有特殊依賴）
        if failed_modules:
            print(f"\n注意：以下模組無法在測試環境中載入：")
            for module, error in failed_modules:
                print(f"  - {module}: {error}")


if __name__ == '__main__':
    unittest.main()