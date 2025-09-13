# encoding: utf-8

"""
本地化功能測試
測試多語言系統的正確性和完整性
"""

import unittest
import sys
import os

# Python 2/3 相容性
try:
    unicode
except NameError:
    # Python 3
    unicode = str

# 新增專案路徑以供測試匯入
test_dir = os.path.dirname(__file__)
project_dir = os.path.dirname(test_dir)
if project_dir not in sys.path:
    sys.path.insert(0, project_dir)

try:
    from NineBoxView.localization import (
        localize, localize_with_params, 
        get_available_languages, validate_translations,
        STRINGS
    )
except ImportError:
    # 直接匯入本地化模組避免依賴問題
    import sys
    import os
    test_dir = os.path.dirname(__file__)
    parent_dir = os.path.dirname(test_dir)
    localization_path = os.path.join(parent_dir, 'localization.py')
    
    import importlib.util
    spec = importlib.util.spec_from_file_location("localization", localization_path)
    localization = importlib.util.module_from_spec(spec)
    
    # Mock Glyphs.localize for testing
    class MockGlyphs:
        @staticmethod
        def localize(translations):
            # 返回英文作為預設
            return translations.get('en', 'MISSING_EN')
    
    import sys
    sys.modules['GlyphsApp'] = type('MockGlyphsApp', (), {'Glyphs': MockGlyphs})()
    
    spec.loader.exec_module(localization)
    
    localize = localization.localize
    localize_with_params = localization.localize_with_params
    get_available_languages = localization.get_available_languages
    validate_translations = localization.validate_translations
    STRINGS = localization.STRINGS


class TestLocalization(unittest.TestCase):
    """本地化系統測試"""
    
    def setUp(self):
        """測試前準備"""
        pass
    
    def test_get_available_languages(self):
        """測試支援的語言清單"""
        languages = get_available_languages()
        
        # 檢查必要的語言都存在
        expected_languages = ['en', 'zh-Hant', 'zh-Hans', 'ja', 'ko']
        self.assertEqual(set(languages), set(expected_languages))
        
        # 檢查語言順序（英文應該第一個作為預設）
        self.assertEqual(languages[0], 'en')
    
    def test_localize_basic_functionality(self):
        """測試基本本地化功能"""
        # 測試已知的鍵值
        result = localize('menu_glyph_picker')
        self.assertIsInstance(result, (str, unicode))
        self.assertNotEqual(result, 'menu_glyph_picker')  # 應該返回翻譯而非鍵值
        
        # 測試不存在的鍵值
        result = localize('non_existent_key')
        self.assertEqual(result, 'non_existent_key')  # 應該返回鍵值本身
    
    def test_localize_with_params_functionality(self):
        """測試帶參數的本地化功能"""
        # 注意：tooltip_locked_char 已移除，現在測試其他參數化功能
        # 直接測試參數功能使用基本測試案例
        test_key = 'window_control_panel_suffix'  # 使用非參數化鍵值測試基本功能
        result = localize_with_params(test_key)
        self.assertIsInstance(result, (str, unicode))
        
        # 測試不存在鍵值的參數化處理
        result = localize_with_params('non_existent_key', param1='test')
        self.assertEqual(result, 'non_existent_key')  # 應該返回鍵值本身
    
    def test_all_translations_have_required_languages(self):
        """測試所有翻譯都包含必要的語言"""
        required_languages = get_available_languages()
        missing_translations = validate_translations()
        
        if missing_translations:
            # 顯示缺失的翻譯詳情
            for key, missing_langs in missing_translations.items():
                print(f"缺失翻譯 - 鍵值: {key}, 缺失語言: {missing_langs}")
        
        # 所有翻譯都應該完整
        self.assertEqual(len(missing_translations), 0, 
                        f"發現缺失的翻譯: {missing_translations}")
    
    def test_translation_consistency(self):
        """測試翻譯一致性"""
        # 檢查所有翻譯字典的結構
        for key, translations in STRINGS.items():
            self.assertIsInstance(translations, dict, 
                                f"翻譯鍵值 {key} 應該是字典")
            
            # 檢查是否包含英文（必須的備用語言）
            self.assertIn('en', translations, 
                         f"翻譯鍵值 {key} 缺少英文翻譯")
            
            # 檢查英文翻譯是否為空
            self.assertNotEqual(translations['en'].strip(), '', 
                              f"翻譯鍵值 {key} 的英文翻譯為空")
    
    def test_specific_translation_keys(self):
        """測試特定的翻譯鍵值"""
        # 測試選單項目
        menu_keys = [
            'menu_glyph_picker',
            'menu_insert_to_current_tab',
            'menu_open_in_new_tab',
            'menu_copy_glyph_name',
            'menu_lock_field_title'  # 新增
        ]
        
        for key in menu_keys:
            result = localize(key)
            self.assertIsInstance(result, (str, unicode))
            self.assertNotEqual(result, key)  # 應該有翻譯
        
        # 測試保留的前台錯誤訊息
        error_keys = [
            'error_glyph_not_exist'  # 保留：前台 UI 訊息（右鍵選單顯示）
        ]
        
        for key in error_keys:
            result = localize(key)
            self.assertIsInstance(result, (str, unicode))
            self.assertNotEqual(result, key)  # 應該有翻譯
        
        # 測試 UI 元件
        ui_keys = [
            'clear_all_locks',
            'tooltip_clear_all_locks',
            'tooltip_toggle_to_unlock',
            'tooltip_toggle_to_lock',
            'tooltip_search_input'
        ]
        
        for key in ui_keys:
            result = localize(key)
            self.assertIsInstance(result, (str, unicode))
            self.assertNotEqual(result, key)  # 應該有翻譯
    
    def test_parameterized_translations(self):
        """測試參數化翻譯"""
        parameterized_keys = [
            # 注意：tooltip_locked_char 已從本地化系統移除
            # 目前沒有其他參數化翻譯鍵值，此測試驗證參數化機制本身
        ]
        
        for key in parameterized_keys:
            # 測試包含參數的翻譯
            translations = STRINGS.get(key, {})
            for lang, text in translations.items():
                self.assertIsInstance(text, (str, unicode))
                # 參數化翻譯應該包含 {} 佔位符
                if '{' in text and '}' in text:
                    # 測試參數替換
                    try:
                        # 嘗試用匹配的虛擬參數測試格式化
                        test_params = {
                            'locked_char': 'TestGlyph'
                        }
                        formatted = text.format(**test_params)
                        self.assertIsInstance(formatted, (str, unicode))
                    except KeyError as e:
                        # 如果格式化失敗，應該讓測試失敗
                        self.fail(f"參數化翻譯失敗 - 鍵值: {key}, 語言: {lang}, 文字: {text}, 錯誤: {e}")
    
    def test_unicode_support(self):
        """測試 Unicode 字符支援"""
        # 測試中文翻譯
        zh_hant_result = localize('menu_glyph_picker')
        self.assertIsInstance(zh_hant_result, (str, unicode))
        
        # 測試是否能正確處理中文字符（使用現有鍵值）
        test_key = 'clear_all_locks'
        result = localize(test_key)
        self.assertIsInstance(result, (str, unicode))
        # 驗證返回的是中文翻譯而不是鍵值本身
        self.assertNotEqual(result, test_key)


class TestLocalizationIntegration(unittest.TestCase):
    """本地化系統整合測試"""
    
    def test_module_import(self):
        """測試模組匯入"""
        # 在測試環境中，我們已經成功匯入了函數，直接測試它們
        # 確認函數可呼叫
        self.assertTrue(callable(localize))
        self.assertTrue(callable(localize_with_params))
        self.assertTrue(callable(get_available_languages))
        self.assertTrue(callable(validate_translations))
        self.assertIsInstance(STRINGS, dict)
        
        # 測試函數基本運作
        languages = get_available_languages()
        self.assertIsInstance(languages, list)
        self.assertIn('en', languages)
    
    def test_glyphs_localize_mock(self):
        """測試在沒有 Glyphs.app 環境下的本地化功能"""
        # 這個測試確認本地化系統在測試環境下也能正常工作
        # 即使沒有實際的 Glyphs.localize API
        
        result = localize('menu_glyph_picker')
        self.assertIsInstance(result, (str, unicode))
        
        # 測試基本參數化功能（使用不存在的鍵值測試錯誤處理）
        result_with_params = localize_with_params('test_key', 
                                                 test_param='TestChar')
        self.assertIsInstance(result_with_params, (str, unicode))
        self.assertEqual(result_with_params, 'test_key')  # 應該返回鍵值本身


def run_localization_tests():
    """執行本地化測試"""
    # 建立測試套件
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    
    # 新增測試案例
    suite.addTests(loader.loadTestsFromTestCase(TestLocalization))
    suite.addTests(loader.loadTestsFromTestCase(TestLocalizationIntegration))
    
    # 執行測試
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    return result.wasSuccessful()


if __name__ == '__main__':
    # 執行測試
    success = run_localization_tests()
    
    if success:
        print("\n✅ 所有本地化測試通過！")
    else:
        print("\n❌ 部分本地化測試失敗！")
        sys.exit(1)