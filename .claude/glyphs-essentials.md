# Glyphs 開發必要知識

> 本文件僅包含 Glyphs 開發的必要知識，遵循「少即是多」原則

## 專案類型自動判斷

根據資料夾結構自動判斷開發類型：

```
# 外掛專案結構
YourPlugin.glyphsPlugin/
├── Contents/
│   ├── Info.plist
│   ├── MacOS/
│   └── Resources/
│       ├── plugin.py           # 主入口
│       └── lib/               # 模組化程式碼
│           ├── __init__.py
│           ├── ui/
│           │   ├── __init__.py
│           │   └── dialogs.py
│           └── core/
│               ├── __init__.py
│               └── processor.py

# 腳本專案結構
Scripts/
└── YourScript.py              # 單一檔案
```

## 核心物件關係（必須理解）

```
GSFont (字型檔案)
├── masters[]: GSFontMaster (主板定義)
├── glyphs[]: GSGlyph (字符)
│   └── layers[masterID]: GSLayer (圖層=字符在特定主板的形狀)
│       ├── paths[]: GSPath → nodes[]: GSNode
│       └── components[]: GSComponent → component: GSGlyph
└── instances[]: GSInstance (輸出實體)
```

**關鍵概念**：每個字符(Glyph)在每個主板(Master)都有一個對應的圖層(Layer)

## 最常用 API（涵蓋 80% 使用場景）

```python
# 基本存取
font = Glyphs.font  # 當前字型
if not font:
    Message("請先開啟字型", "")
    return

# 遍歷所有字符
for glyph in font.glyphs:
    print(f"處理 {glyph.name}")
    
    # 存取特定主板的圖層
    layer = glyph.layers[font.masters[0].id]
    
    # 處理路徑
    for path in layer.paths:
        for node in path.nodes:
            # node.x, node.y, node.type
            pass

# 批次處理模式（重要！）
font.disableUpdateInterface()  # 停用更新
try:
    # 您的批次處理
    pass
finally:
    font.enableUpdateInterface()  # 恢復更新
```

## 模組化開發規範（外掛專用）

### 外掛模組結構
```python
# plugin.py - 主入口檔案
# -*- coding: utf-8 -*-
from __future__ import division, print_function, unicode_literals
import objc
from GlyphsApp import *
from GlyphsApp.plugins import *

# 使用相對路徑匯入，避免衝突
from .lib.ui.dialogs import MainDialog
from .lib.core.processor import GlyphProcessor

class YourPlugin(GeneralPlugin):
    @objc.python_method
    def settings(self):
        self.name = "Your Plugin"
        
    def showWindow_(self, sender):
        # 使用 PyObjC 建立原生 GUI
        self.dialog = MainDialog(self)
        self.dialog.show()
```

### 模組檔案範例
```python
# lib/ui/dialogs.py
import objc
from AppKit import *
from vanilla import *

class MainDialog:
    def __init__(self, plugin):
        self.plugin = plugin
        self.setup_window()
    
    def setup_window(self):
        # 使用 PyObjC 原生元件
        self.window = NSWindow.alloc().initWithContentRect_styleMask_backing_defer_(
            ((100, 100), (400, 300)),
            NSTitledWindowMask | NSClosableWindowMask,
            NSBackingStoreBuffered,
            False
        )
        self.window.setTitle_("外掛功能")
```

### __init__.py 檔案
```python
# lib/__init__.py
"""外掛核心模組"""

# lib/ui/__init__.py
"""使用者介面模組"""
from .dialogs import MainDialog

# lib/core/__init__.py
"""核心處理模組"""
from .processor import GlyphProcessor
```

## GUI 框架選擇規範

### 腳本：使用 vanilla
```python
# 簡單腳本的 GUI（vanilla）
from vanilla import Window, Button, TextBox

self.w = Window((400, 150), "腳本功能")
self.w.label = TextBox((20, 20, -20, 20), "說明文字")
self.w.runButton = Button((-90, -40, 70, 22), "執行", 
                         callback=self.execute)
self.w.open()
```

### 外掛：使用 PyObjC
```python
# 外掛的原生 GUI（PyObjC）
from AppKit import *

# 建立視窗
window = NSWindow.alloc().initWithContentRect_styleMask_backing_defer_(
    ((0, 0), (400, 300)),
    NSTitledWindowMask | NSClosableWindowMask | NSMiniaturizableWindowMask,
    NSBackingStoreBuffered,
    False
)

# 建立控制項
button = NSButton.alloc().initWithFrame_(((300, 20), (80, 32)))
button.setTitle_("執行")
button.setTarget_(self)
button.setAction_("executeAction:")
button.setBezelStyle_(NSRoundedBezelStyle)

# 加入視窗
window.contentView().addSubview_(button)
```

## Glyphs 環境特定安全原則

延續使用者記憶體的安全原則，加上 Glyphs 特定注意事項：

```python
# ❌ 錯誤：硬編碼路徑
font.save("/Users/erikyin/Desktop/font.glyphs")

# ✅ 正確：使用對話框或環境變數
filepath = GetSaveFile("儲存字型", ["glyphs"])
if filepath:
    font.save(filepath)

# 偏好設定儲存（不使用檔案）
Glyphs.defaults["com.YinTzuYuan.PluginName.setting"] = value

# 操作前備份
backup = font.copy()  # 記憶體中的完整複製
```

## Glyphs TDD 實踐指南

遵循紅燈→綠燈→重構循環，並考慮模組化測試：

```python
# test_plugin.py（外掛測試）
import unittest
import sys
import os

# 加入外掛路徑
plugin_path = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, plugin_path)

from lib.core.processor import GlyphProcessor

class TestGlyphProcessor(unittest.TestCase):
    def setUp(self):
        """每個測試前準備乾淨環境"""
        self.font = GSFont()
        self.font.masters.append(GSFontMaster())
        self.processor = GlyphProcessor()
        
    def test_process_glyph(self):
        """測試字符處理功能"""
        # Arrange
        glyph = GSGlyph("A")
        self.font.glyphs.append(glyph)
        
        # Act
        result = self.processor.process(glyph)
        
        # Assert
        self.assertTrue(result)

# 執行測試
if __name__ == '__main__':
    unittest.main()
```

## 插件類型快速決策

```
需要什麼？
├─ 顯示資訊 → ReporterPlugin (foreground/background)
├─ 修改形狀 → FilterPlugin (filter + parameters)
├─ 側邊面板 → PalettePlugin (init + update)
└─ 其他一切 → GeneralPlugin (showWindow_)
```

## 除錯技巧

```python
# 清空並顯示巨集視窗
Glyphs.clearLog()
Glyphs.showMacroWindow()

# 除錯輸出（記得移除！）
print(f"處理 {glyph.name}: {layer.bounds}")

# 錯誤處理
try:
    # 主要邏輯
except Exception as e:
    import traceback
    print(traceback.format_exc())
    Message("執行失敗", str(e))
```

## 記住：簡單優於複雜

- 先讓它能運作，再考慮優化
- 腳本保持單檔案簡單，外掛才模組化
- 遵循使用者記憶體的 300 行限制原則
- 大部分情況用 GeneralPlugin 就夠了
- 遵循使用者記憶體的通用原則
