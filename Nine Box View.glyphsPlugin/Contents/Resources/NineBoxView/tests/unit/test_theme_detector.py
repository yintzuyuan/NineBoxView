# encoding: utf-8
"""
ThemeDetector 測試

測試主題偵測系統 - Issue #21 的重要功能
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


class TestThemeDetector(unittest.TestCase):
    """ThemeDetector 測試類"""
    
    def setUp(self):
        """測試設定"""
        self.mock_glyphs = setup_mock_environment()
        
        # 延遲匯入以使用 Mock 環境
        from core.theme_detector import ThemeDetector
        self.detector = ThemeDetector()
    
    def tearDown(self):
        """測試清理"""
        teardown_mock_environment()
    
    def test_create_detector(self):
        """測試建立 ThemeDetector 實例"""
        self.assertIsNotNone(self.detector)
        self.assertTrue(hasattr(self.detector, 'detect_current_theme'))
    
    def test_detect_theme_basic(self):
        """測試基本主題偵測"""
        # 設定 Mock Tab
        from tests.mocks.glyphs_mocks import MockGSTab
        mock_tab = MockGSTab()
        self.mock_glyphs.font.currentTab = mock_tab
        
        theme = self.detector.detect_current_theme(self.mock_glyphs.font)
        
        # 應該返回布爾值或主題資訊
        self.assertIsInstance(theme, (bool, dict, str))
    
    def test_tab_level_detection(self):
        """測試 Tab 層級偵測 - Issue #21 核心功能"""
        from tests.mocks.glyphs_mocks import MockGSTab
        mock_tab = MockGSTab()
        
        # 測試 Tab 有 previewView 方法
        preview_view = mock_tab.previewView()
        self.assertIsNotNone(preview_view)
        self.assertTrue(hasattr(preview_view, 'setBlack_'))
    
    def test_fallback_mechanism(self):
        """測試多層級偵測器的復原機制"""
        # 測試沒有 currentTab 的情況
        self.mock_glyphs.font.currentTab = None
        
        theme = self.detector.detect_current_theme(self.mock_glyphs.font)
        
        # 應該有合理的復原值
        self.assertIsNotNone(theme)


class TestThemeDetectionMethods(unittest.TestCase):
    """測試主題偵測方法"""
    
    def setUp(self):
        """測試設定"""
        self.mock_glyphs = setup_mock_environment()
        
        from core.theme_detector import ThemeDetector
        self.detector = ThemeDetector()
    
    def tearDown(self):
        """測試清理"""
        teardown_mock_environment()
    
    def test_tab_level_api(self):
        """測試 Tab 層級 API - 正確實作"""
        from tests.mocks.glyphs_mocks import MockGSTab, MockPreviewView
        
        mock_tab = MockGSTab()
        preview_view = mock_tab.previewView()
        
        # 測試 setBlack_ API
        result = preview_view.setBlack_(True)
        self.assertTrue(result)
        
        result = preview_view.setBlack_(False)
        self.assertFalse(result)
    
    def test_theme_consistency(self):
        """測試主題偵測的一致性"""
        from tests.mocks.glyphs_mocks import MockGSTab
        mock_tab = MockGSTab()
        self.mock_glyphs.font.currentTab = mock_tab
        
        # 多次偵測應該返回一致結果（在同一條件下）
        theme1 = self.detector.detect_current_theme(self.mock_glyphs.font)
        theme2 = self.detector.detect_current_theme(self.mock_glyphs.font)
        
        self.assertEqual(theme1, theme2)


if __name__ == '__main__':
    unittest.main()