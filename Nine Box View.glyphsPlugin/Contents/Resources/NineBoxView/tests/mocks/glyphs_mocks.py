# encoding: utf-8
"""
Glyphs API Mock 物件 - 支援新架構的測試

針對新的 GlyphsService 和依賴注入架構進行測試支援
"""

from __future__ import division, print_function, unicode_literals
import sys
import types


class MockGSFont(object):
    """Mock GSFont 物件"""
    
    def __init__(self):
        self.familyName = "Test Font"
        self.glyphs = {}
        self.masters = [MockGSFontMaster()]
        self.selectedLayers = []
        self.currentTab = None
        self.filepath = "/tmp/test_font.glyphs"
        self.tempData = {}  # 支援 tempData 快取
        self.selectedFontMaster = self.masters[0]  # 預設選中第一個 master
    
    def __getitem__(self, key):
        return self.glyphs.get(key)
    
    def __setitem__(self, key, value):
        self.glyphs[key] = value


class MockGSFontMaster(object):
    """Mock GSFontMaster 物件"""
    
    def __init__(self):
        self.id = "master01"
        self.name = "Regular"


class MockGSGlyph(object):
    """Mock GSGlyph 物件"""
    
    def __init__(self, name="a", unicode_value="0061"):
        self.name = name
        self.unicode = unicode_value
        self.layers = {}
        self.parent = None


class MockGSLayer(object):
    """Mock GSLayer 物件"""
    
    def __init__(self, glyph=None, master_id="master01"):
        self.parent = glyph or MockGSGlyph()
        self.master = MockGSFontMaster()
        self.master.id = master_id
        
        
class MockGSTab(object):
    """Mock GSTab 物件"""
    
    def __init__(self):
        self.layers = []
        
    def previewView(self):
        return MockPreviewView()


class MockPreviewView(object):
    """Mock PreviewView 物件"""
    
    def __init__(self):
        self._black = False
    
    def setBlack_(self, value):
        self._black = bool(value)
        return self._black


class MockGlyphs(object):
    """Mock Glyphs 全域物件"""
    
    def __init__(self):
        self.font = MockGSFont()
        
    def showNotification(self, title, message):
        """Mock 通知顯示"""
        print(f"Notification: {title} - {message}")


# 全域 Mock 物件實例
mock_glyphs = MockGlyphs()


def setup_mock_environment():
    """設定 Mock 測試環境"""
    # 攔截 GlyphsApp 模組匯入
    mock_glyphs_app = types.ModuleType('GlyphsApp')
    mock_glyphs_app.Glyphs = mock_glyphs
    mock_glyphs_app.GSFont = MockGSFont
    mock_glyphs_app.GSGlyph = MockGSGlyph
    mock_glyphs_app.GSLayer = MockGSLayer
    mock_glyphs_app.GSFontMaster = MockGSFontMaster
    
    # 將 Mock 模組插入 sys.modules
    sys.modules['GlyphsApp'] = mock_glyphs_app
    
    # 建立標準測試字符
    test_glyph = MockGSGlyph("a", "0061")
    test_layer = MockGSLayer(test_glyph)
    test_glyph.layers["master01"] = test_layer
    
    mock_glyphs.font.glyphs["a"] = test_glyph
    mock_glyphs.font.glyphs["0061"] = test_glyph
    
    return mock_glyphs


def teardown_mock_environment():
    """清理 Mock 測試環境"""
    mock_glyphs.font.glyphs.clear()
    mock_glyphs.font.tempData.clear()
    mock_glyphs.font.selectedLayers = []
    mock_glyphs.font.currentTab = None
    
    # 移除 Mock 模組（可選，通常保留以避免重複設定）
    # if 'GlyphsApp' in sys.modules:
    #     del sys.modules['GlyphsApp']