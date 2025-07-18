# Glyphs 程式碼模板庫

> 實際可用的程式碼模板，遵循模組化和 GUI 框架選擇規範

## 腳本模板（單檔案 + vanilla GUI）

### 基礎腳本模板
```python
#MenuTitle: 您的腳本名稱
# -*- coding: utf-8 -*-
from __future__ import division, print_function, unicode_literals

__doc__="""
腳本功能說明
"""

# 載入作者資訊
# Author: YinTzuYuan (erikyin)
# Copyright: Copyright 2025 YinTzuYuan. All rights reserved.

from GlyphsApp import *
from vanilla import *

class ScriptDialog:
    def __init__(self):
        # 檢查字型
        self.font = Glyphs.font
        if not self.font:
            Message("請先開啟字型", "此腳本需要開啟的字型檔案")
            return
        
        # 建立視窗
        self.setup_window()
    
    def setup_window(self):
        """使用 vanilla 建立簡單介面"""
        self.w = Window((400, 200), "腳本功能")
        
        # 介面元件
        self.w.descriptionText = TextBox((15, 15, -15, 30), 
            "這個腳本會處理選中的字符...")
        
        self.w.parameterLabel = TextBox((15, 60, 100, 20), "參數值：")
        self.w.parameterInput = EditText((120, 60, -15, 20), "10")
        
        # 進度條（可選）
        self.w.progress = ProgressBar((15, 100, -15, 16))
        
        # 按鈕
        self.w.cancelButton = Button((15, -40, 80, 20), "取消", 
                                    callback=self.close_window)
        self.w.runButton = Button((-95, -40, 80, 20), "執行", 
                                 callback=self.run_script)
        
        # 設定預設按鈕
        self.w.setDefaultButton(self.w.runButton)
        
        self.w.open()
    
    def run_script(self, sender):
        """執行主要邏輯"""
        try:
            # 取得參數
            parameter = int(self.w.parameterInput.get())
            
            # 停用介面更新
            self.font.disableUpdateInterface()
            
            # 處理選中的字符
            glyphs = self.font.selectedGlyphs or self.font.glyphs
            total = len(glyphs)
            
            for i, glyph in enumerate(glyphs):
                # 更新進度
                self.w.progress.set(100 * i / total)
                
                # 處理每個字符
                self.process_glyph(glyph, parameter)
            
            # 完成
            self.w.progress.set(100)
            
        except Exception as e:
            Message("執行錯誤", str(e))
        finally:
            self.font.enableUpdateInterface()
            self.close_window(None)
    
    def process_glyph(self, glyph, parameter):
        """處理單一字符"""
        for layer in glyph.layers:
            # 您的處理邏輯
            for path in layer.paths:
                for node in path.nodes:
                    node.x += parameter
    
    def close_window(self, sender):
        self.w.close()

# 執行腳本
ScriptDialog()
```

### 批次處理腳本模板
```python
#MenuTitle: 批次處理字符
# -*- coding: utf-8 -*-
from __future__ import division, print_function, unicode_literals

from GlyphsApp import *

# 清空巨集視窗
Glyphs.clearLog()
Glyphs.showMacroWindow()

font = Glyphs.font
if not font:
    Message("請開啟字型", "")
else:
    # 批次處理
    font.disableUpdateInterface()
    
    try:
        for glyph in font.glyphs:
            print(f"處理 {glyph.name}")
            
            # 您的處理邏輯
            for layer in glyph.layers:
                # 範例：自動設定寬度
                if not layer.paths:
                    layer.width = 600
        
        print("✅ 處理完成")
        
    except Exception as e:
        print(f"❌ 錯誤：{e}")
        import traceback
        print(traceback.format_exc())
    
    finally:
        font.enableUpdateInterface()
```

## 外掛模板（模組化 + PyObjC GUI）

### 主入口檔案 (plugin.py)
```python
# -*- coding: utf-8 -*-
from __future__ import division, print_function, unicode_literals
import objc
from GlyphsApp import *
from GlyphsApp.plugins import *

# 相對匯入模組
from .lib.ui.main_window import MainWindow
from .lib.core.processor import GlyphProcessor
from .lib.utils.helpers import setup_logging

class YourPlugin(GeneralPlugin):
    
    @objc.python_method
    def settings(self):
        """外掛設定"""
        self.name = Glyphs.localize({
            'en': 'Your Plugin Name',
            'zh-Hant': '您的外掛名稱'
        })
        
        # 選單設定
        self.menuName = Glyphs.localize({
            'en': 'Process Glyphs',
            'zh-Hant': '處理字符'
        })
        
    @objc.python_method
    def start(self):
        """外掛啟動"""
        # 初始化日誌
        setup_logging(self.name)
        
        # 載入偏好設定
        self.load_preferences()
        
        # 新增選單項目
        menu_item = NSMenuItem(self.menuName, self.showWindow_)
        Glyphs.menu[EDIT_MENU].append(menu_item)
    
    def showWindow_(self, sender):
        """顯示主視窗"""
        if not Glyphs.font:
            Message("請先開啟字型", "此外掛需要開啟的字型檔案")
            return
        
        # 建立處理器和視窗
        self.processor = GlyphProcessor()
        self.window = MainWindow(self)
        self.window.show()
    
    @objc.python_method
    def load_preferences(self):
        """載入偏好設定"""
        Glyphs.registerDefault(self.domain("parameterValue"), 10)
        
    @objc.python_method
    def domain(self, key):
        """偏好設定鍵值"""
        return f"com.YinTzuYuan.{self.__class__.__name__}.{key}"
```

### UI 模組 (lib/ui/main_window.py)
```python
# -*- coding: utf-8 -*-
import objc
from AppKit import *
from vanilla import *

class MainWindow:
    def __init__(self, plugin):
        self.plugin = plugin
        self.font = Glyphs.font
        self.setup_window()
    
    def setup_window(self):
        """使用 PyObjC 建立原生介面"""
        # 建立視窗
        self.window = NSWindow.alloc().initWithContentRect_styleMask_backing_defer_(
            ((100, 100), (500, 400)),
            NSTitledWindowMask | NSClosableWindowMask | NSMiniaturizableWindowMask,
            NSBackingStoreBuffered,
            False
        )
        
        self.window.setTitle_("外掛功能視窗")
        
        # 建立內容視圖
        content_view = self.window.contentView()
        
        # 標題文字
        title = NSTextField.alloc().initWithFrame_(((20, 350), (460, 30)))
        title.setStringValue_("處理字符設定")
        title.setBezeled_(False)
        title.setDrawsBackground_(False)
        title.setEditable_(False)
        title.setFont_(NSFont.boldSystemFontOfSize_(16))
        content_view.addSubview_(title)
        
        # 參數輸入
        param_label = NSTextField.labelWithString_("參數值：")
        param_label.setFrame_(((20, 300), (80, 20)))
        content_view.addSubview_(param_label)
        
        self.param_input = NSTextField.alloc().initWithFrame_(((110, 300), (100, 22)))
        self.param_input.setStringValue_("10")
        content_view.addSubview_(self.param_input)
        
        # 進度指示器
        self.progress = NSProgressIndicator.alloc().initWithFrame_(((20, 250), (460, 20)))
        self.progress.setStyle_(NSProgressIndicatorBarStyle)
        self.progress.setIndeterminate_(False)
        content_view.addSubview_(self.progress)
        
        # 按鈕
        cancel_button = NSButton.alloc().initWithFrame_(((320, 20), (80, 32)))
        cancel_button.setTitle_("取消")
        cancel_button.setBezelStyle_(NSRoundedBezelStyle)
        cancel_button.setTarget_(self)
        cancel_button.setAction_("cancelAction:")
        content_view.addSubview_(cancel_button)
        
        run_button = NSButton.alloc().initWithFrame_(((410, 20), (80, 32)))
        run_button.setTitle_("執行")
        run_button.setBezelStyle_(NSRoundedBezelStyle)
        run_button.setTarget_(self)
        run_button.setAction_("runAction:")
        run_button.setKeyEquivalent_("\r")  # Enter 鍵
        content_view.addSubview_(run_button)
        
    def show(self):
        """顯示視窗"""
        self.window.makeKeyAndOrderFront_(None)
        self.window.center()
    
    @objc.IBAction
    def runAction_(self, sender):
        """執行動作"""
        parameter = int(self.param_input.stringValue())
        
        # 在背景執行
        self.performSelectorInBackground_withObject_(
            self.processInBackground_, 
            parameter
        )
    
    @objc.python_method
    def processInBackground_(self, parameter):
        """背景處理"""
        try:
            glyphs = self.font.selectedGlyphs or self.font.glyphs
            total = len(glyphs)
            
            for i, glyph in enumerate(glyphs):
                # 更新進度（主執行緒）
                progress = 100.0 * i / total
                self.performSelectorOnMainThread_withObject_waitUntilDone_(
                    self.updateProgress_, 
                    progress, 
                    False
                )
                
                # 處理字符
                self.plugin.processor.process(glyph, parameter)
            
            # 完成
            self.performSelectorOnMainThread_withObject_waitUntilDone_(
                self.processingComplete_, 
                None, 
                False
            )
            
        except Exception as e:
            self.performSelectorOnMainThread_withObject_waitUntilDone_(
                self.showError_, 
                str(e), 
                False
            )
    
    @objc.python_method
    def updateProgress_(self, value):
        """更新進度條"""
        self.progress.setDoubleValue_(value)
    
    @objc.python_method
    def processingComplete_(self, _):
        """處理完成"""
        self.progress.setDoubleValue_(100)
        NSRunAlertPanel("完成", "處理完成！", "確定", None, None)
        self.window.close()
    
    @objc.python_method
    def showError_(self, error):
        """顯示錯誤"""
        NSRunAlertPanel("錯誤", error, "確定", None, None)
    
    @objc.IBAction
    def cancelAction_(self, sender):
        """取消動作"""
        self.window.close()
```

### 核心處理模組 (lib/core/processor.py)
```python
# -*- coding: utf-8 -*-
from GlyphsApp import *

class GlyphProcessor:
    """字符處理核心邏輯"""
    
    def __init__(self):
        self.processed_count = 0
    
    def process(self, glyph, parameter):
        """處理單一字符"""
        for layer in glyph.layers:
            self.process_layer(layer, parameter)
        
        self.processed_count += 1
    
    def process_layer(self, layer, parameter):
        """處理圖層"""
        # 範例：移動所有節點
        for path in layer.paths:
            for node in path.nodes:
                node.x += parameter
                
        # 更新度量
        layer.updateMetrics()
```

### 初始化檔案 (lib/__init__.py)
```python
# -*- coding: utf-8 -*-
"""
外掛核心模組
"""

# 確保模組可以被正確匯入
import os
import sys

# 加入外掛路徑
plugin_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if plugin_path not in sys.path:
    sys.path.insert(0, plugin_path)
```

### 工具模組 (lib/utils/helpers.py)
```python
# -*- coding: utf-8 -*-
import os
import logging

def setup_logging(plugin_name):
    """設定日誌系統"""
    log_format = f'[{plugin_name}] %(levelname)s: %(message)s'
    logging.basicConfig(format=log_format, level=logging.INFO)
    
def validate_selection(font):
    """驗證選擇"""
    if not font.selectedGlyphs:
        return False, "請先選擇字符"
    return True, None
```

## Reporter 外掛模板
```python
# -*- coding: utf-8 -*-
from __future__ import division, print_function, unicode_literals
import objc
from GlyphsApp import *
from GlyphsApp.plugins import *

class YourReporter(ReporterPlugin):
    
    @objc.python_method
    def settings(self):
        self.menuName = Glyphs.localize({
            'en': 'Show Metrics',
            'zh-Hant': '顯示度量'
        })
    
    @objc.python_method
    def foreground(self, layer):
        """前景繪製"""
        # 取得縮放
        scale = self.getScale()
        
        # 繪製資訊
        x = layer.bounds.origin.x
        y = layer.bounds.origin.y - 20 / scale
        
        self.drawTextAtPoint(
            f"寬度: {layer.width}",
            (x, y),
            fontSize=10.0 / scale,
            fontColor=NSColor.redColor()
        )
```

## Filter 外掛模板
```python
# -*- coding: utf-8 -*-
from __future__ import division, print_function, unicode_literals
import objc
from GlyphsApp import *
from GlyphsApp.plugins import *

class YourFilter(FilterPlugin):
    
    @objc.python_method
    def settings(self):
        self.menuName = Glyphs.localize({
            'en': 'Transform Glyphs',
            'zh-Hant': '變換字符'
        })
        self.keyboardShortcut = 't'
        self.keyboardShortcutModifier = NSCommandKeyMask | NSShiftKeyMask
    
    @objc.python_method
    def filter(self, layer, inEditView, customParameters):
        """處理圖層"""
        # 取得參數
        offset = customParameters.get('offset', 10)
        
        # 處理路徑
        for path in layer.paths:
            for node in path.nodes:
                node.x += offset
    
    @objc.python_method
    def generateCustomParameter(self):
        """定義參數介面"""
        return """(
            {
                name = offset;
                type = int;
                default = 10;
                min = -100;
                max = 100;
            }
        )"""
```
