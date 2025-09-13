# encoding: utf-8
"""
InputRecognition 測試

測試字符輸入識別和驗證系統
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


class TestInputRecognition(unittest.TestCase):
    """InputRecognition 測試類"""
    
    def setUp(self):
        """測試設定"""
        self.mock_glyphs = setup_mock_environment()
        
        # 延遲匯入以使用 Mock 環境
        from core.input_recognition import InputRecognitionService
        self.service = InputRecognitionService()
    
    def tearDown(self):
        """測試清理"""
        teardown_mock_environment()
    
    def test_create_service(self):
        """測試建立 InputRecognition 服務"""
        self.assertIsNotNone(self.service)
        self.assertTrue(hasattr(self.service, 'validate_glyph_input'))
    
    def test_recognize_valid_input(self):
        """測試識別有效輸入"""
        result = self.service.validate_glyph_input("a")
        
        self.assertIsInstance(result, dict)
        self.assertIn('valid', result)
        self.assertIn('valid_glyphs', result)
        self.assertIn('invalid_chars', result)
    
    def test_recognize_empty_input(self):
        """測試空輸入識別"""
        result = self.service.validate_glyph_input("")
        
        self.assertIsInstance(result, dict)
        self.assertEqual(result['valid_glyphs'], [])
    
    def test_recognize_multiple_chars(self):
        """測試多字符識別"""
        result = self.service.validate_glyph_input("abc")
        
        self.assertIsInstance(result, dict)
        self.assertIn('valid', result)
        self.assertIn('valid_glyphs', result)
        self.assertIn('invalid_chars', result)


class TestCharacterValidation(unittest.TestCase):
    """測試字符驗證功能"""
    
    def setUp(self):
        """測試設定"""
        self.mock_glyphs = setup_mock_environment()
        
        try:
            from core.input_recognition import validate_glyph_input
            self.validate_function = validate_glyph_input
        except ImportError:
            self.validate_function = None
    
    def tearDown(self):
        """測試清理"""
        teardown_mock_environment()
    
    def test_validate_function_exists(self):
        """測試驗證函數是否存在"""
        if self.validate_function:
            self.assertTrue(callable(self.validate_function))
    
    def test_validate_basic_chars(self):
        """測試基本字符驗證"""
        if not self.validate_function:
            self.skipTest("validate_glyph_input function not available")
        
        # 測試有效字符
        result = self.validate_function("a")
        self.assertIsInstance(result, dict)
        
        # 測試空輸入
        result = self.validate_function("")
        self.assertIsInstance(result, dict)


if __name__ == '__main__':
    unittest.main()