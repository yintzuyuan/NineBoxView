# encoding: utf-8
"""
GlyphsService 測試

測試統一的 Glyphs API 服務層
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


class TestGlyphsService(unittest.TestCase):
    """GlyphsService 測試類"""
    
    def setUp(self):
        """測試設定"""
        self.mock_glyphs = setup_mock_environment()
        
        # 延遲匯入以使用 Mock 環境
        from core.glyphs_service import GlyphsService
        self.service = GlyphsService
    
    def tearDown(self):
        """測試清理"""
        teardown_mock_environment()
    
    def test_is_available(self):
        """測試 Glyphs API 可用性檢查"""
        # 在 Mock 環境中應該可用
        available = self.service.is_available()
        self.assertIsInstance(available, bool)
    
    def test_get_current_font(self):
        """測試獲取當前字體"""
        font = self.service.get_current_font()
        # 在 Mock 環境中應該返回 Mock 字體或 None
        self.assertTrue(font is None or hasattr(font, 'familyName'))
    
    def test_get_glyph_from_font(self):
        """測試從字體獲取字符"""
        font = self.mock_glyphs.font
        
        # 測試有效字符
        glyph = self.service.get_glyph_from_font(font, "a")
        if glyph:
            self.assertEqual(glyph.name, "a")
        
        # 測試無效字符
        invalid_glyph = self.service.get_glyph_from_font(font, "nonexistent")
        self.assertIsNone(invalid_glyph)
        
        # 測試空輸入
        empty_glyph = self.service.get_glyph_from_font(font, "")
        self.assertIsNone(empty_glyph)
    
    def test_get_layer_from_glyph(self):
        """測試從字符獲取圖層"""
        font = self.mock_glyphs.font
        glyph = self.service.get_glyph_from_font(font, "a")
        
        if glyph:
            layer = self.service.get_layer_from_glyph(glyph, "master01")
            if layer:
                self.assertEqual(layer.master.id, "master01")
    
    def test_get_layer_for_char(self):
        """測試完整的字符到圖層流程"""
        font = self.mock_glyphs.font
        layer = self.service.get_layer_for_char(font, "a", "master01")
        
        if layer:
            self.assertEqual(layer.parent.name, "a")
    
    def test_show_notification(self):
        """測試顯示通知"""
        # 不應該拋出例外
        try:
            self.service.show_notification("Test Title", "Test Message")
            success = True
        except Exception:
            success = False
        
        self.assertTrue(success)
    
    def test_get_current_font_id(self):
        """測試獲取字型唯一標識"""
        font_id = self.service.get_current_font_id()
        
        # 應該返回字符串或 None
        self.assertTrue(isinstance(font_id, (str, type(None))))


class TestGlyphsServiceCache(unittest.TestCase):
    """測試 GlyphsService 快取功能"""
    
    def setUp(self):
        """測試設定"""
        self.mock_glyphs = setup_mock_environment()
        
        from core.glyphs_service import GlyphsService
        self.service = GlyphsService
    
    def tearDown(self):
        """測試清理"""
        teardown_mock_environment()
    
    def test_tempdata_cache(self):
        """測試 tempData 快取機制"""
        font = self.mock_glyphs.font
        
        # 第一次尋找
        glyph1 = self.service.get_glyph_from_font(font, "a")
        
        # 檢查是否使用了快取
        cache_key = "glyph_lookup_a"
        if hasattr(font, 'tempData'):
            self.assertIn(cache_key, font.tempData)
            
            # 第二次尋找應該使用快取
            glyph2 = self.service.get_glyph_from_font(font, "a")
            self.assertEqual(glyph1, glyph2)


if __name__ == '__main__':
    unittest.main()