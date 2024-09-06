# encoding: utf-8

import objc
from GlyphsApp import *
from GlyphsApp.plugins import *
from AppKit import NSColor, NSFont, NSAffineTransform, NSRectFill, NSView, NSBezierPath, NSFloatingWindowLevel
from vanilla import Window, Group, Button, EditText
import traceback

class NineBoxPreviewView(NSView):
    
    def drawRect_(self, rect):
        try:
            # 設置背景顏色
            if self.wrapper.plugin.darkMode:
                NSColor.blackColor().set()
            else:
                NSColor.whiteColor().set()
            NSRectFill(rect)

            if not Glyphs.font or not Glyphs.font.selectedLayers:
                return

            currentLayer = Glyphs.font.selectedLayers[0]
            currentChar = currentLayer.parent.unicode
            searchChar = self.wrapper.plugin.lastChar or currentChar

            # 可調整參數
            MARGIN_RATIO = 0.05  # 邊距佔總寬度的比例
            SPACING_RATIO = 0.03  # 間距佔總寬度的比例

            # 計算九宮格的大小（包含邊距）
            gridSize = min(rect.size.width, rect.size.height)
            
            # 計算實際的邊距和間距
            MARGIN = gridSize * MARGIN_RATIO
            SPACING = gridSize * SPACING_RATIO

            # 找出要被渲染的字形中最寬的一個
            maxWidth = 0
            glyphsToRender = []
            for i in range(9):
                if i == 4:  # 中間格子
                    glyph = currentLayer.parent
                else:
                    glyph = Glyphs.font.glyphs[searchChar] if searchChar else currentLayer.parent
                glyphsToRender.append(glyph)
                if glyph:
                    layer = glyph.layers[Glyphs.font.selectedFontMaster.id]
                    maxWidth = max(maxWidth, layer.bounds.size.width)

            # 計算格子大小,使最寬的字形能夠完全顯示
            cellSize = min((gridSize - 2 * MARGIN - 2 * SPACING) / 3, maxWidth * 1.2)  # 1.2 是一個調整因子,可以根據需要修改

            # 重新計算九宮格的起始位置（左上角）
            startX = (rect.size.width - (3 * cellSize + 2 * SPACING)) / 2
            startY = (rect.size.height + (3 * cellSize + 2 * SPACING)) / 2

            for i, glyph in enumerate(glyphsToRender):
                row = i // 3
                col = i % 3
                
                # 計算每個格子的中心點
                x = startX + col * (cellSize + SPACING) + cellSize / 2
                y = startY - row * (cellSize + SPACING) - cellSize / 2

                if glyph:
                    layer = glyph.layers[Glyphs.font.selectedFontMaster.id]
                    
                    # 計算縮放比例，使字形盡可能填滿格子
                    glyphWidth = layer.bounds.size.width
                    glyphHeight = layer.bounds.size.height
                    scaleX = cellSize / glyphWidth if glyphWidth > 0 else 1
                    scaleY = cellSize / glyphHeight if glyphHeight > 0 else 1
                    scale = min(scaleX, scaleY)

                    transform = NSAffineTransform.transform()
                    transform.translateXBy_yBy_(x, y)
                    transform.scaleBy_(scale)

                    # 移動字形，使其在格子中居中
                    offsetX = -layer.bounds.origin.x - glyphWidth / 2
                    offsetY = -layer.bounds.origin.y - glyphHeight / 2
                    transform.translateXBy_yBy_(offsetX, offsetY)

                    bezierPath = layer.completeBezierPath.copy()
                    bezierPath.transformUsingAffineTransform_(transform)

                    # 設置繪製顏色
                    if self.wrapper.plugin.darkMode:
                        NSColor.whiteColor().set()
                    else:
                        NSColor.blackColor().set()
                    bezierPath.fill()

        except Exception as e:
            print(traceback.format_exc())

class NineBoxPreview(Group):
    nsViewClass = NineBoxPreviewView

    def __init__(self, posSize, plugin):
        super(NineBoxPreview, self).__init__(posSize)
        self._nsObject.wrapper = self
        self.plugin = plugin

    def redraw(self):
        self._nsObject.setNeedsDisplay_(True)

class NineBoxView(GeneralPlugin):

    @objc.python_method
    def settings(self):
        self.name = Glyphs.localize({'en': u'Nine Box View', 'zh-Hant': u'九宮格預覽'})

    @objc.python_method
    def start(self):
        try:
            newMenuItem = NSMenuItem(self.name, self.showWindow_)
            Glyphs.menu[WINDOW_MENU].append(newMenuItem)
            
            self.loadPreferences()
            
            Glyphs.addCallback(self.updateInterface, UPDATEINTERFACE)
        except:
            self.logToMacroWindow(traceback.format_exc())

    @objc.python_method
    def showWindow_(self, sender):
        try:
            self.w = Window((300, 340), self.name, minSize=(200, 240))
            self.w.preview = NineBoxPreview((0, 0, -0, -40), self)
            self.w.searchField = EditText((10, -30, -100, -10), 
                                          placeholder="輸入一個字符", 
                                          callback=self.searchFieldCallback)
            self.w.darkModeButton = Button((-90, -30, -10, -10), "深色模式",
                                           callback=self.darkModeCallback)
            self.w.open()
            
            # 設置視窗永遠浮動於上方
            self.w.getNSWindow().setLevel_(NSFloatingWindowLevel)
            
            self.updateInterface(None)
        except:
            self.logToMacroWindow(traceback.format_exc())

    @objc.python_method
    def loadPreferences(self):
        self.darkMode = Glyphs.defaults.get("com.YinTzuYuan.NineBoxView.darkMode", False)
        self.lastChar = Glyphs.defaults.get("com.YinTzuYuan.NineBoxView.lastChar", "")

    @objc.python_method
    def savePreferences(self):
        Glyphs.defaults["com.YinTzuYuan.NineBoxView.darkMode"] = self.darkMode
        Glyphs.defaults["com.YinTzuYuan.NineBoxView.lastChar"] = self.lastChar

    @objc.python_method
    def __del__(self):
        self.savePreferences()
        Glyphs.removeCallback(self.updateInterface, UPDATEINTERFACE)

    @objc.python_method
    def logToMacroWindow(self, message):
        Glyphs.clearLog()
        print(message)

    @objc.python_method
    def updateInterface(self, sender):
        if hasattr(self, 'w') and hasattr(self.w, 'preview'):
            self.w.preview.redraw()

    @objc.python_method
    def searchFieldCallback(self, sender):
        char = sender.get()
        if len(char) > 0:
            self.lastChar = char[0]
        self.updateInterface(None)

    @objc.python_method
    def darkModeCallback(self, sender):
        self.darkMode = not self.darkMode
        self.updateInterface(None)

    @objc.python_method
    def __file__(self):
        """Please leave this method unchanged"""
        return __file__